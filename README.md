# TurboMyRide - GPX Time Adjuster

A Flask-based web application for adjusting GPX file timestamps. Perfect for modifying activity timing data for training analysis, route planning, or data correction.

## Features

- **Three Adjustment Modes:**
  - **Mode 1:** Adjust the entire GPX file by a percentage
  - **Mode 2:** Adjust from a specific time offset onwards (with optional duration window)
  - **Mode 3:** Change the start date and time of the entire route

- Clean, intuitive web interface
- Real-time file processing
- Automatic file download after processing
- Support for positive (faster) and negative (slower) percentage adjustments

## Requirements

- Python 3.x
- Flask
- gpxpy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Networkwilliams/turbomyride.git
cd turbomyride
```

2. Install dependencies:
```bash
pip install flask gpxpy
```

## Usage

1. Start the Flask application:
```bash
python3 app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5001
```

3. Upload a GPX file and choose your adjustment mode:
   - **Adjust entire file:** Enter a percentage (e.g., 10 for 10% faster, -5 for 5% slower)
   - **Adjust from specific time:** Specify start time in minutes and optional duration
   - **Change start date/time:** Select a new start date and time

4. Click "Adjust GPX Timing" and download your modified file

## How It Works

The application parses GPX files, modifies the timestamps according to your chosen adjustment mode, and generates a new GPX file with adjusted timing data. The original GPS coordinates and route remain unchanged - only the time data is modified.

## Output Files

Processed files are saved in the `outputs/` directory with descriptive filenames indicating the adjustment applied:
- `adjusted_10.0pct_faster_xxxxx.gpx`
- `adjusted_20.0pct_faster_from_98.0min_for_5.0min_xxxxx.gpx`
- `datetime_changed_20240809_0111_xxxxx.gpx`

## Note

This is a development server. For production deployment, use a production WSGI server like gunicorn or waitress.
