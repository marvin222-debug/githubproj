# ANPR System Usage Instructions

## Overview

The Automatic Number Plate Recognition (ANPR) system for petrol stations enforces fuel restrictions based on vehicle age. This document provides instructions for running and using the system.

## Prerequisites

1. **Install Tesseract OCR**
   - For Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - For Linux: `sudo apt install tesseract-ocr`
   - For macOS: `brew install tesseract`

2. **Install MongoDB**
   - Download and install from https://www.mongodb.com/try/download/community
   - Ensure the MongoDB service is running

3. **Install Python Requirements**
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the root directory (copy from the `.env.example` template)
2. Adjust the following settings as needed:
   - `DB_URI` - MongoDB connection URI
   - `TESSERACT_PATH` - Path to Tesseract OCR executable
   - `VAHAN_API_KEY` - API key for the government's vehicle database
   - `DIESEL_AGE_LIMIT` - Maximum age for diesel vehicles (default: 10 years)
   - `PETROL_AGE_LIMIT` - Maximum age for petrol vehicles (default: 15 years)
   - `CAMERA_SOURCE` - Camera index (0 for default webcam)

## Running the System

### Command-line Interface

The system can be run in several modes:

1. **Process a Single Image**
   ```
   python src/main.py --image path/to/image.jpg
   ```

2. **Run in Continuous Mode with Camera**
   ```
   python src/main.py --continuous
   ```

3. **Run in Continuous Mode without Preview**
   ```
   python src/main.py --continuous --no-preview
   ```

4. **Adjust Processing Interval**
   ```
   python src/main.py --continuous --interval 1.5
   ```

### Web API

To start the web API server:
```
python src/api/app.py
```

The API server provides the following endpoints:

1. **Health Check**
   ```
   GET /health
   ```

2. **Process an Image**
   ```
   POST /api/process
   Content-Type: multipart/form-data
   Body: image=@file.jpg
   ```

3. **Check Registration Number**
   ```
   GET /api/check-plate?plate=ABC123
   ```

## Understanding Output

When a vehicle is processed, the system will:

1. Detect and read the license plate
2. Look up vehicle information in the database
3. Calculate the vehicle's age
4. Determine fuel eligibility based on age limits
5. Display the result as "FUEL ALLOWED" or "FUEL DENIED"

## Troubleshooting

- **OCR Issues**: Ensure Tesseract is correctly installed and the path is set in `.env`
- **Camera Access**: Verify your webcam is working and accessible
- **Database Connection**: Check that MongoDB is running
- **API Errors**: Confirm that your Vahan API key is valid

## Developer Notes

- All logs are written to `anpr_system.log`
- Captured images are saved in the `data/captured` directory
- Test with various lighting conditions for optimal OCR performance 