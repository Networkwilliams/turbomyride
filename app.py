from flask import Flask, render_template, request, jsonify, send_file, url_for
import gpxpy
import gpxpy.gpx
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create upload and output directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def adjust_gpx_time(file_path, percentage_change, start_offset_minutes=None, duration_minutes=None, new_start_datetime=None):
    """
    Adjusts the timing of a GPX file by a given percentage or changes the start date/time.

    Args:
        file_path: Path to the GPX file
        percentage_change: Percentage to change the time by
        start_offset_minutes: If provided, only adjust from this time offset (in minutes) onwards
        duration_minutes: If provided with start_offset, only adjust for this duration (in minutes)
        new_start_datetime: If provided, shifts all timestamps to start at this new date/time
    """
    try:
        # Parse the GPX file
        with open(file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        # Calculate the time adjustment factor
        time_factor = 1 - (percentage_change / 100)

        # Collect all timestamped points
        timestamped_points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time:
                        timestamped_points.append(point)

        if not timestamped_points:
            return None, "No timestamped points found in the GPX file."

        # Calculate original duration
        start_time = timestamped_points[0].time
        end_time = timestamped_points[-1].time
        original_duration = end_time - start_time

        # Adjust timestamps
        if new_start_datetime is not None:
            # Mode 3: Change the start date/time
            # Ensure both datetimes have compatible timezone info
            from datetime import timezone
            if start_time.tzinfo is None:
                # Original is naive, make new_start_datetime naive too
                new_start_datetime = new_start_datetime.replace(tzinfo=None)
            elif new_start_datetime.tzinfo is None:
                # Original is aware, make new_start_datetime aware (UTC)
                new_start_datetime = new_start_datetime.replace(tzinfo=timezone.utc)

            time_shift = new_start_datetime - start_time

            for point in timestamped_points:
                point.time = point.time + time_shift

        elif start_offset_minutes is not None:
            # Mode 2: Adjust from a specific offset
            adjustment_start_time = start_time + timedelta(minutes=start_offset_minutes)

            if duration_minutes is not None:
                # Mode 2 with duration: Adjust only within a specific window
                adjustment_end_time = adjustment_start_time + timedelta(minutes=duration_minutes)
                accumulated_time_shift = timedelta(0)

                for i, point in enumerate(timestamped_points):
                    if i == 0:
                        continue

                    original_point_time = point.time

                    if point.time < adjustment_start_time:
                        # Before adjustment window - keep original
                        continue
                    elif point.time <= adjustment_end_time:
                        # Within adjustment window - apply percentage change
                        time_from_adjustment_start = point.time - adjustment_start_time
                        adjusted_time_from_start = time_from_adjustment_start * time_factor
                        point.time = adjustment_start_time + adjusted_time_from_start

                        # Track the accumulated shift at the end of the window
                        if i < len(timestamped_points) - 1 and timestamped_points[i + 1].time > adjustment_end_time:
                            # This is the last point in the adjustment window
                            accumulated_time_shift = point.time - original_point_time
                    else:
                        # After adjustment window - apply accumulated shift
                        if accumulated_time_shift == timedelta(0):
                            # Calculate the shift from the last adjusted point
                            for j in range(i - 1, -1, -1):
                                if timestamped_points[j].time <= adjustment_end_time:
                                    # Find the time shift at the boundary
                                    time_at_boundary = adjustment_end_time
                                    time_from_adj_start = time_at_boundary - adjustment_start_time
                                    adjusted_boundary = adjustment_start_time + (time_from_adj_start * time_factor)
                                    accumulated_time_shift = adjusted_boundary - time_at_boundary
                                    break

                        point.time = point.time + accumulated_time_shift
            else:
                # Mode 2 without duration: Adjust from offset to end
                for i, point in enumerate(timestamped_points):
                    if i == 0:
                        continue

                    if point.time < adjustment_start_time:
                        # Don't adjust points before the offset
                        continue
                    else:
                        # Adjust from the offset onwards
                        time_from_adjustment_start = point.time - adjustment_start_time
                        adjusted_time_from_start = time_from_adjustment_start * time_factor
                        point.time = adjustment_start_time + adjusted_time_from_start
        else:
            # Mode 1: Adjust the entire file (original behavior)
            for i, point in enumerate(timestamped_points):
                if i == 0:
                    continue

                elapsed_from_start = point.time - start_time
                adjusted_elapsed = elapsed_from_start * time_factor
                point.time = start_time + adjusted_elapsed

        # Calculate new duration
        new_duration = timestamped_points[-1].time - timestamped_points[0].time

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        if new_start_datetime is not None:
            # Mode 3: Date/time change
            date_str = new_start_datetime.strftime("%Y%m%d_%H%M")
            output_filename = f"datetime_changed_{date_str}_{unique_id}.gpx"
        else:
            # Mode 1 or 2: Percentage adjustments
            modifier = "faster" if percentage_change > 0 else "slower"
            if start_offset_minutes is not None:
                if duration_minutes is not None:
                    output_filename = f"adjusted_{abs(percentage_change)}pct_{modifier}_from_{start_offset_minutes}min_for_{duration_minutes}min_{unique_id}.gpx"
                else:
                    output_filename = f"adjusted_{abs(percentage_change)}pct_{modifier}_from_{start_offset_minutes}min_{unique_id}.gpx"
            else:
                output_filename = f"adjusted_{abs(percentage_change)}pct_{modifier}_{unique_id}.gpx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Save the modified GPX file
        with open(output_path, 'w') as f:
            f.write(gpx.to_xml())

        return {
            'filename': output_filename,
            'original_duration': str(original_duration),
            'new_duration': str(new_duration),
            'percentage': percentage_change,
            'start_offset': start_offset_minutes,
            'duration': duration_minutes,
            'original_start': str(start_time) if new_start_datetime else None,
            'new_start': str(timestamped_points[0].time) if new_start_datetime else None
        }, None

    except Exception as e:
        return None, f"Error processing GPX file: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_gpx():
    try:
        # Check if file was uploaded
        if 'gpxFile' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['gpxFile']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})

        # Check file extension
        if not file.filename.lower().endswith('.gpx'):
            return jsonify({'success': False, 'error': 'Please upload a GPX file'})

        # Get adjustment mode (default to mode 1 - full file adjustment)
        adjustment_mode = request.form.get('adjustmentMode', '1')

        # Initialize parameters
        percentage = 0
        start_offset = None
        duration = None
        new_start_datetime = None

        if adjustment_mode == '3':
            # Mode 3: Date/time change
            new_date = request.form.get('newDate', '').strip()
            new_time = request.form.get('newTime', '').strip()

            if not new_date or not new_time:
                return jsonify({'success': False, 'error': 'Please provide both date and time'})

            try:
                # Parse the date and time (expecting format: YYYY-MM-DD and HH:MM)
                from datetime import timezone
                datetime_str = f"{new_date} {new_time}"
                # Create timezone-aware datetime in UTC to match GPX timestamps
                new_start_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date or time format'})
        else:
            # Mode 1 or 2: Percentage adjustments
            try:
                percentage = float(request.form.get('percentage', 0))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid percentage value'})

            if adjustment_mode == '2':
                # Get start offset and duration for mode 2
                try:
                    start_offset = float(request.form.get('startOffset', 0))
                    if start_offset < 0:
                        return jsonify({'success': False, 'error': 'Start offset must be positive'})
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid start offset value'})

                # Get duration (optional for mode 2)
                duration_str = request.form.get('duration', '').strip()
                if duration_str:
                    try:
                        duration = float(duration_str)
                        if duration <= 0:
                            return jsonify({'success': False, 'error': 'Duration must be positive'})
                    except ValueError:
                        return jsonify({'success': False, 'error': 'Invalid duration value'})

        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        upload_filename = f"{unique_id}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        file.save(upload_path)

        # Process the GPX file
        result, error = adjust_gpx_time(upload_path, percentage, start_offset, duration, new_start_datetime)

        # Clean up uploaded file
        os.remove(upload_path)

        if error:
            return jsonify({'success': False, 'error': error})

        return jsonify({'success': True, **result})

    except Exception as e:
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Security check - ensure filename is safe
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)