# Petrol Station ANPR System

An Automatic Number Plate Recognition (ANPR) system for petrol stations to enforce fuel restrictions based on vehicle age.

## Overview

This system determines a vehicle's age through a four-step process:

1. **License Plate Capture**: Captures vehicle license plates via cameras at petrol station entrances
2. **Data Extraction**: Processes images using OCR to extract registration numbers
3. **Database Cross-Referencing**: Matches the registration number against vehicle databases
4. **Age Calculation**: Compares registration date with current date to enforce age restrictions

## Installation

1. Install Tesseract OCR on your system
   - For Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - For Linux: `sudo apt install tesseract-ocr`
   - For macOS: `brew install tesseract`

2. Install MongoDB
   - Download from https://www.mongodb.com/try/download/community
   - Start the MongoDB service

3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your configuration

## Usage

### Command-Line Interface

Run the system from the command line:

```
# Process a single image
python src/main.py --image path/to/image.jpg

# Run in continuous mode with camera
python src/main.py --continuous

# Run with additional options
python src/main.py --continuous --no-preview --interval 1.5
```

### Web Application

Start the web interface:

```
python src/api/web_app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

The web interface provides:
- Home page with system overview
- Upload image page for license plate detection
- Check registration page for direct vehicle lookup
- About page with detailed system information

### API Endpoints

The system also provides REST API endpoints:

- `GET /health` - System health check
- `POST /api/process` - Process license plate image
- `GET /api/check-plate?plate=ABC123` - Check vehicle by registration number

## Project Structure

- `src/`: Source code
  - `api/`: API and web application
  - `capture/`: License plate image capture modules
  - `processing/`: Image processing and OCR functions
  - `database/`: Database connection and query handlers
  - `models/`: Data models
  - `utils/`: Utility functions
  - `static/`: Web assets (CSS, JavaScript)
  - `templates/`: HTML templates for web interface
- `data/`: Data storage
- `tests/`: Test files
- `config/`: Configuration files 