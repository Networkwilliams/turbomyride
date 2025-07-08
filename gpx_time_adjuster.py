import gpxpy
import gpxpy.gpx
from datetime import datetime, timedelta
import os

def adjust_gpx_time(file_path, percentage_change):
    """
    Adjusts the timing of a GPX file by a given percentage.
    
    Args:
        file_path: Path to the GPX file
        percentage_change: Percentage to change the time by (positive = faster, negative = slower)
    """
    
    # Parse the GPX file
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    # Calculate the time adjustment factor
    # If percentage_change is positive, we make it faster (reduce time intervals)
    # If percentage_change is negative, we make it slower (increase time intervals)
    time_factor = 1 - (percentage_change / 100)
    
    # Collect all timestamped points
    timestamped_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.time:
                    timestamped_points.append(point)
    
    if not timestamped_points:
        print("No timestamped points found in the GPX file.")
        return None
    
    # Calculate original duration
    start_time = timestamped_points[0].time
    end_time = timestamped_points[-1].time
    original_duration = end_time - start_time
    
    print(f"Original duration: {original_duration}")
    
    # Adjust timestamps
    for i, point in enumerate(timestamped_points):
        if i == 0:
            # Keep the first point's time unchanged
            continue
        
        # Calculate elapsed time from start
        elapsed_from_start = point.time - start_time
        
        # Adjust the elapsed time
        adjusted_elapsed = elapsed_from_start * time_factor
        
        # Set the new time
        point.time = start_time + adjusted_elapsed
    
    # Calculate new duration
    new_duration = timestamped_points[-1].time - timestamped_points[0].time
    print(f"New duration: {new_duration}")
    
    # Save the modified GPX file
    base_name = os.path.splitext(file_path)[0]
    modifier = "faster" if percentage_change > 0 else "slower"
    modified_file_path = f"{base_name}_{abs(percentage_change)}pct_{modifier}.gpx"
    
    with open(modified_file_path, 'w') as f:
        f.write(gpx.to_xml())
    
    print(f"Modified GPX file saved as: {modified_file_path}")
    return modified_file_path

def main():
    print("GPX Time Adjuster")
    print("=================")
    
    # Get file path
    file_path = input("Enter the path to the GPX file: ").strip()
    
    if not os.path.exists(file_path):
        print("File not found. Please check the path.")
        return
    
    # Get percentage change
    try:
        percentage = float(input("Enter percentage to make it faster (positive) or slower (negative): "))
    except ValueError:
        print("Invalid percentage. Please enter a number.")
        return
    
    # Adjust the GPX file
    result = adjust_gpx_time(file_path, percentage)
    
    if result:
        print(f"Success! Modified file created: {result}")

if __name__ == '__main__':
    main()