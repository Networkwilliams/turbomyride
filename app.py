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

def adjust_gpx_time(file_path, percentage_change):
    """
    Adjusts the timing of a GPX file by a given percentage.
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
        for i, point in enumerate(timestamped_points):
            if i == 0:
                continue
            
            # Calculate elapsed time from start
            elapsed_from_start = point.time - start_time
            
            # Adjust the elapsed time
            adjusted_elapsed = elapsed_from_start * time_factor
            
            # Set the new time
            point.time = start_time + adjusted_elapsed
        
        # Calculate new duration
        new_duration = timestamped_points[-1].time - timestamped_points[0].time
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        modifier = "faster" if percentage_change > 0 else "slower"
        output_filename = f"adjusted_{abs(percentage_change)}pct_{modifier}_{unique_id}.gpx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Save the modified GPX file
        with open(output_path, 'w') as f:
            f.write(gpx.to_xml())
        
        return {
            'filename': output_filename,
            'original_duration': str(original_duration),
            'new_duration': str(new_duration),
            'percentage': percentage_change
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
        
        # Get percentage
        try:
            percentage = float(request.form.get('percentage', 0))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid percentage value'})
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        upload_filename = f"{unique_id}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        file.save(upload_path)
        
        # Process the GPX file
        result, error = adjust_gpx_time(upload_path, percentage)
        
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