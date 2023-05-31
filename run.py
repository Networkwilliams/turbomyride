import gpxpy
import gpxpy.gpx

def increase_gpx(file_path, percentage):
    # Parse the GPX file
    gpx = gpxpy.parse(open(file_path, 'r'))

    # Calculate the increase factor
    increase_factor = 1 + (percentage / 100)

    # Increase the latitude and longitude coordinates
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                point.latitude *= increase_factor
                point.longitude *= increase_factor

    # Save the modified GPX file
    modified_file_path = file_path.replace('.gpx', '_modified.gpx')
    with open(modified_file_path, 'w') as f:
        f.write(gpx.to_xml())

    print(f"Modified GPX file saved as: {modified_file_path}")


if __name__ == '__main__':
    # Prompt the user for the GPX file path
    file_path = input("Enter the path to the GPX file: ")

    # Prompt the user for the percentage increase
    percentage = float(input("Enter the percentage increase: "))

    # Call the function to increase the GPX file
    increase_gpx(file_path, percentage)
