# 🚗 ANPR System - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Algorithms & Detection Methods](#algorithms--detection-methods)
5. [Frontend Technologies](#frontend-technologies)
6. [Backend & APIs](#backend--apis)
7. [Database Systems](#database-systems)
8. [Workflow & Process Flow](#workflow--process-flow)
9. [Project Structure](#project-structure)
10. [Key Features](#key-features)

---

## 🎯 Project Overview

**ANPR (Automatic Number Plate Recognition) System** is an intelligent fuel eligibility checking system for petrol stations. It automatically detects vehicle license plates from images, extracts registration numbers using OCR, queries vehicle databases, and determines fuel eligibility based on vehicle age restrictions.

### Purpose
- Enforce fuel restrictions based on vehicle age (Diesel: 10 years, Petrol: 15 years)
- Automate license plate recognition at petrol station entrances
- Provide real-time vehicle information and eligibility status
- Maintain vehicle database with registration details

---

## 🛠️ Technology Stack

### **Backend Framework**
- **Flask 2.3.0+** - Python web framework for RESTful API and web application
- **Python 3.11+** - Core programming language

### **Computer Vision & Image Processing**
- **OpenCV (cv2) 4.8.0+** - Image processing, contour detection, edge detection
- **NumPy 1.24.0+** - Numerical computations and array operations
- **Pillow 10.0.0+** - Image manipulation and format conversion
- **imutils 0.5.4+** - OpenCV convenience functions
- **scipy 1.11.0+** - Scientific computing utilities

### **OCR (Optical Character Recognition)**
- **Tesseract OCR** - Primary OCR engine for text extraction
- **EasyOCR 1.7.0+** - Deep learning-based OCR with GPU support
- **pytesseract 0.3.10+** - Python wrapper for Tesseract

### **Machine Learning & AI**
- **PyTorch 2.0.0+** - Deep learning framework
- **torchvision 0.15.0+** - Computer vision utilities for PyTorch
- **Ultralytics YOLO 8.0.0+** - Object detection models (YOLOv8)
- **Google Generative AI 0.3.0+** - Gemini API for advanced OCR

### **Database**
- **MongoDB Atlas** - Cloud-based NoSQL database
- **pymongo 4.5.0+** - MongoDB Python driver
- **CSV Database** - Fallback local storage option

### **Web Technologies**
- **HTML5** - Frontend markup
- **CSS3** - Styling (Bootstrap 5 integration)
- **JavaScript (ES6+)** - Frontend interactivity
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - Icons

### **Utilities & Tools**
- **python-dotenv 1.0.0+** - Environment variable management
- **requests 2.31.0+** - HTTP library for API calls
- **pandas 2.0.0+** - Data manipulation
- **flask-cors** - Cross-Origin Resource Sharing support
- **psutil 5.9.0+** - System and process utilities
- **python-dateutil 2.8.0+** - Date parsing utilities
- **schedule 1.2.0+** - Task scheduling
- **certifi 2023.7.22+** - SSL certificate bundle

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Upload     │  │   Camera     │  │   Check       │    │
│  │   Image      │  │   Capture    │  │   Plate       │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
          ┌─────────────────▼─────────────────┐
          │      FLASK WEB SERVER              │
          │      (Port 5000)                   │
          │  ┌─────────────────────────────┐  │
          │  │   REST API Endpoints         │  │
          │  │   - /api/process             │  │
          │  │   - /api/check-plate         │  │
          │  │   - /api/vehicles            │  │
          │  └──────────────┬───────────────┘  │
          └─────────────────┼──────────────────┘
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
    ┌─────▼─────┐    ┌──────▼──────┐   ┌──────▼──────┐
    │  Plate    │    │  Database   │   │ Performance│
    │ Detector  │    │  Manager     │   │  Monitor   │
    │  Engine   │    │              │   │            │
    └─────┬─────┘    └──────┬───────┘   └────────────┘
          │                 │
    ┌─────▼─────────────────▼──────┐
    │   MongoDB Atlas Database     │
    │   (Cloud Storage)             │
    └──────────────────────────────┘
```

---

## 🧠 Algorithms & Detection Methods

The system implements **multiple plate detection algorithms** with automatic fallback mechanisms:

### **1. Ultra-Fast Detector** (Primary)
- **Method**: Optimized contour detection + Multi-OCR
- **Technologies**: OpenCV, EasyOCR, Tesseract
- **Features**:
  - Lightning-fast preprocessing (bilateral filter, OTSU thresholding)
  - Parallel processing with ThreadPoolExecutor
  - Detection caching (5-second cache)
  - Multiple OCR engines (EasyOCR → Tesseract fallback)
  - Pre-compiled regex patterns for Indian license plates
- **Speed**: Sub-second detection times
- **Use Case**: Production environment, high-speed processing

### **2. Robust Plate Detector**
- **Method**: Simple region detection + Robust OCR
- **Technologies**: OpenCV, EasyOCR, Tesseract
- **Features**:
  - Simple plate region detection
  - Multiple preprocessing methods
  - Robust text extraction with validation
- **Use Case**: Clear, well-lit images

### **3. Optimized Plate Detector**
- **Method**: Specialized for Indian license plates
- **Technologies**: OpenCV, Tesseract
- **Features**:
  - Multiple detection strategies (contours, rectangles, edges)
  - Indian plate format validation
  - Optimized preprocessing pipeline
- **Use Case**: Indian vehicle registration plates

### **4. YOLO Enhanced Detector**
- **Method**: YOLOv8 object detection + EasyOCR
- **Technologies**: Ultralytics YOLO, EasyOCR
- **Features**:
  - Deep learning-based vehicle/plate detection
  - YOLO model for object localization
  - EasyOCR for text recognition
  - Fallback to traditional CV methods
- **Use Case**: Complex scenes with multiple vehicles

### **5. Advanced Plate Detector**
- **Method**: YOLO vehicle detection → Plate search
- **Technologies**: YOLO, OpenCV, EasyOCR
- **Features**:
  - First detects vehicles using YOLO
  - Searches for plates within vehicle regions
  - Reduces false positives
- **Use Case**: Traffic scenes, multiple vehicles

### **6. Contour Plate Detector**
- **Method**: Contour-based detection
- **Technologies**: OpenCV, EasyOCR, Tesseract
- **Features**:
  - Edge detection (Canny)
  - Contour finding and filtering
  - Aspect ratio validation
  - Multiple OCR attempts
- **Use Case**: Standard license plates

### **7. Gemini Plate Detector**
- **Method**: Google Gemini AI Vision API
- **Technologies**: Google Generative AI, YOLO fallback
- **Features**:
  - AI-powered vision recognition
  - Natural language understanding
  - Fallback to traditional methods
- **Use Case**: Challenging images, AI-powered recognition

### **8. Simple Plate Detector**
- **Method**: Basic OCR with validation
- **Technologies**: Tesseract, OpenCV
- **Features**:
  - Simple region detection
  - Full image OCR fallback
  - Format validation
- **Use Case**: Fallback option, simple scenarios

### **Detection Algorithm Selection Logic**
The system automatically selects the best available detector:
```
UltraFastDetector → RobustPlateDetector → OptimizedPlateDetector 
→ YOLOEnhancedDetector → SimplePlateDetector → PlateDetector
```

### **Image Processing Pipeline**
1. **Preprocessing**:
   - Grayscale conversion
   - Noise reduction (bilateral filter)
   - Edge detection (Canny)
   - Thresholding (OTSU, adaptive)

2. **Plate Region Detection**:
   - Contour detection
   - Aspect ratio filtering (2.0-6.0)
   - Area filtering
   - Rectangle validation

3. **Text Extraction**:
   - Multiple OCR engines (EasyOCR, Tesseract)
   - Multiple PSM modes (Page Segmentation Modes)
   - Character whitelisting
   - Text cleaning and normalization

4. **Validation**:
   - Regex pattern matching (Indian plate formats)
   - Length validation (6-13 characters)
   - Alphanumeric checks
   - Format validation (LLDDLLDDDD, etc.)

---

## 🎨 Frontend Technologies

### **HTML Templates** (Jinja2)
- `index.html` - Home page with system overview
- `upload.html` - Image upload interface
- `check.html` - Direct plate number lookup
- `camera_check.html` - Live camera capture
- `add_vehicle.html` - Add vehicle to database
- `about.html` - System information
- `layout.html` - Base template with navigation

### **CSS Styling**
- **Bootstrap 5** - Responsive grid system, components
- **Custom CSS** (`style.css`) - Dark theme, purple/blue gradients
- **Responsive Design** - Mobile-friendly interface

### **JavaScript Features**
- **Fetch API** - Asynchronous API calls
- **FormData** - File upload handling
- **Canvas API** - Image preview and manipulation
- **WebRTC** - Camera access for live capture
- **Error Handling** - Comprehensive error messages
- **Loading States** - Spinner animations
- **Real-time Updates** - Dynamic content updates

### **Frontend Workflow**
1. User uploads image or captures from camera
2. JavaScript creates FormData with image
3. Fetch API sends POST request to `/api/process`
4. Response handling with success/error states
5. Dynamic DOM updates with results
6. Visual feedback (loading spinners, alerts)

---

## 🔌 Backend & APIs

### **Flask Application Structure**

#### **Web Routes** (HTML Pages)
```python
GET  /              - Home page
GET  /upload        - Upload image page
GET  /check         - Check registration page
GET  /camera        - Live camera page
GET  /add           - Add vehicle page
GET  /about         - About page
```

#### **REST API Endpoints**

##### **1. Health Check**
```
GET /health
Response: {
    "status": "ok",
    "timestamp": "2025-12-04T21:48:14.211001"
}
```

##### **2. Process Image** (Main Endpoint)
```
POST /api/process
Content-Type: multipart/form-data
Body: {
    image: <file>
    demo_fallback: "true" (optional)
}

Response (Success): {
    "success": true,
    "registration_number": "DL07KL9988",
    "vehicle_details": {
        "registration_date": "2022-01-01T00:00:00",
        "fuel_type": "PETROL",
        "age_years": 2.89,
        "make": "Kia",
        "model": "Seltos",
        "vehicle_make": "Kia",
        "vehicle_model": "Seltos"
    },
    "fuel_eligibility": {
        "eligible": true,
        "reason": null,
        "age_limit": 15
    },
    "plate_box": {
        "x": 100,
        "y": 200,
        "width": 400,
        "height": 100
    },
    "performance": {
        "detection_time": 3.112,
        "method_used": "ultra_fast"
    }
}

Response (Error): {
    "success": false,
    "message": "Error message here",
    "error": "Error details",
    "type": "ErrorType"
}
```

##### **3. Check Registration Number**
```
GET /api/check-plate?plate=DL07KL9988

Response: {
    "success": true,
    "registration_number": "DL07KL9988",
    "vehicle_details": {...},
    "fuel_eligibility": {...}
}
```

##### **4. Get All Vehicles**
```
GET /api/vehicles?page=1&per_page=20&fuel_type=PETROL&state=DL&make=Kia

Response: {
    "success": true,
    "total_vehicles": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8,
    "vehicles": [...]
}
```

##### **5. Add Vehicle**
```
POST /api/add-vehicle
Content-Type: application/json
Body: {
    "registration_number": "DL07KL9988",
    "registration_date": "2022-01-01",
    "fuel_type": "PETROL",
    "owner_name": "John Doe",
    "vehicle_make": "Kia",
    "vehicle_model": "Seltos",
    "chassis_number": "...",
    "engine_number": "..."
}

Response: {
    "success": true,
    "message": "Vehicle added successfully"
}
```

##### **6. Performance Metrics**
```
GET /api/performance
Response: {
    "total_detections": 150,
    "average_time": 2.5,
    "success_rate": 0.95,
    ...
}

GET /api/performance/realtime
Response: {
    "current_processing_time": 1.2,
    "active_detections": 3,
    ...
}
```

##### **7. MongoDB Atlas Status**
```
GET /api/atlas/status
Response: {
    "success": true,
    "atlas_status": {
        "connected": true,
        "database": "anpr_system",
        "collection": "vehicles"
    }
}

GET /api/atlas/stats
Response: {
    "success": true,
    "database_stats": {
        "total_vehicles": 5000,
        "fuel_types": ["PETROL", "DIESEL"],
        "states": ["DL", "KA", "MH", ...]
    }
}

POST /api/atlas/reconnect
Response: {
    "success": true,
    "message": "Reconnection successful"
}
```

### **Error Handling**
- Comprehensive try-catch blocks
- Detailed error logging
- Graceful error responses
- Connection retry mechanisms
- Timeout handling

---

## 💾 Database Systems

### **Primary Database: MongoDB Atlas**
- **Type**: Cloud-based NoSQL database
- **Connection**: Persistent connection manager with auto-reconnection
- **Collection**: `vehicles`
- **Schema**:
```json
{
    "registration_number": "DL07KL9988",
    "registration_date": ISODate("2022-01-01T00:00:00Z"),
    "fuel_type": "PETROL",
    "owner_name": "John Doe",
    "vehicle_make": "Kia",
    "vehicle_model": "Seltos",
    "state": "DL",
    "district": "New Delhi",
    "chassis_number": "...",
    "engine_number": "...",
    "created_at": ISODate("2025-12-04T...")
}
```

### **Database Features**
- **Persistent Connection**: Auto-reconnect on failure
- **Connection Pooling**: Efficient resource management
- **Indexing**: Fast lookups on registration_number
- **Data Validation**: Format checking before insertion
- **Backup Support**: CSV export functionality

### **Fallback Database: CSV**
- Local CSV file storage (`data/vahan_data.csv`)
- Used when MongoDB is unavailable
- Pandas-based querying

### **Database Operations**
- `get_vehicle_info(registration_number)` - Lookup vehicle
- `add_vehicle(vehicle)` - Add new vehicle
- `search_vehicles(**filters)` - Search with filters
- `list_plate_numbers(limit)` - List all plates
- `get_database_stats()` - Statistics

---

## 🔄 Workflow & Process Flow

### **Complete System Workflow**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
│  1. Upload Image / Capture from Camera                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK WEB SERVER                               │
│  POST /api/process                                          │
│  - Receives image file                                      │
│  - Validates request                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              IMAGE PROCESSING                               │
│  1. Decode image (OpenCV)                                   │
│  2. Validate image format                                   │
│  3. Log image details                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PLATE DETECTION ENGINE                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  UltraFastDetector (Primary)                         │  │
│  │  ├─ Preprocess image                                  │  │
│  │  ├─ Detect plate regions (contours)                  │  │
│  │  ├─ Extract text (EasyOCR → Tesseract)               │  │
│  │  └─ Validate plate format                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  Fallback: Robust → Optimized → YOLO → Simple              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              TEXT PROCESSING                                 │
│  1. Normalize text (uppercase, remove spaces)                │
│  2. Validate format (regex patterns)                         │
│  3. Try variations (OCR error correction)                    │
│     - 0 ↔ O, 1 ↔ I, spaces removal                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE QUERY                                  │
│  MongoDB Atlas:                                              │
│  1. Query by registration_number                             │
│  2. If not found, try variations                             │
│  3. Return Vehicle object or None                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              AGE CALCULATION                                  │
│  Vehicle.age = (today - registration_date) / 365.25         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ELIGIBILITY CHECK                               │
│  if fuel_type == "DIESEL":                                   │
│      eligible = age <= 10 years                              │
│  elif fuel_type == "PETROL":                                 │
│      eligible = age <= 15 years                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              RESPONSE GENERATION                             │
│  JSON Response with:                                          │
│  - Registration number                                        │
│  - Vehicle details                                           │
│  - Fuel eligibility status                                   │
│  - Performance metrics                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND DISPLAY                                │
│  - Show vehicle information                                  │
│  - Display eligibility (ALLOWED/DENIED)                      │
│  - Show performance stats                                    │
└─────────────────────────────────────────────────────────────┘
```

### **Error Handling Flow**
```
Error Occurs
    │
    ├─→ Plate Detection Error
    │   └─→ Return error response, log details
    │
    ├─→ Database Connection Error
    │   └─→ Try reconnection, return 503 if fails
    │
    ├─→ Vehicle Not Found
    │   └─→ Return 200 with success=false, show message
    │
    └─→ Network/Timeout Error
        └─→ Return 500, log full traceback
```

---

## 📁 Project Structure

```
ANPR/
├── src/
│   ├── api/                    # Flask web application
│   │   ├── web_app.py         # Main Flask app (primary)
│   │   ├── app.py             # Alternative Flask app
│   │   └── check_app.py       # Check-specific app
│   │
│   ├── capture/                # Camera/image capture
│   │   ├── camera.py          # Basic camera interface
│   │   └── enhanced_camera.py    # Advanced camera features
│   │
│   ├── processing/             # Plate detection algorithms
│   │   ├── ultra_fast_detector.py      # ⚡ Primary detector
│   │   ├── robust_plate_detector.py    # 💪 Robust detector
│   │   ├── optimized_plate_detector.py # 🎩 Optimized detector
│   │   ├── yolo_enhanced_detector.py   # 🚀 YOLO + EasyOCR
│   │   ├── advanced_plate_detector.py  # 🔬 Advanced methods
│   │   ├── contour_plate_detector.py   # 📐 Contour-based
│   │   ├── gemini_plate_detector.py     # 🤖 AI-powered
│   │   ├── simple_plate_detector.py    # 🔍 Simple fallback
│   │   └── plate_detector.py           # 📋 Traditional
│   │
│   ├── database/              # Database interfaces
│   │   ├── enhanced_mongodb_atlas_db.py  # Primary (Atlas)
│   │   ├── mongodb_atlas_db.py           # Basic Atlas
│   │   ├── persistent_atlas_connection.py # Connection manager
│   │   ├── vehicle_db.py                 # Base interface
│   │   └── csv_vehicle_db.py             # CSV fallback
│   │
│   ├── models/                # Data models
│   │   ├── vehicle.py         # Vehicle data class
│   │   └── license_plate_yolo.pt  # YOLO model weights
│   │
│   ├── config/                 # Configuration
│   │   ├── config.py          # Main config
│   │   └── performance_config.py
│   │
│   ├── utils/                  # Utilities
│   │   └── performance_monitor.py
│   │
│   ├── services/              # Background services
│   │   └── atlas_service.py   # MongoDB Atlas service
│   │
│   ├── templates/             # HTML templates (Jinja2)
│   │   ├── layout.html        # Base template
│   │   ├── index.html         # Home
│   │   ├── upload.html        # Upload page
│   │   ├── check.html         # Check page
│   │   ├── camera_check.html  # Camera page
│   │   ├── add_vehicle.html   # Add vehicle
│   │   └── about.html         # About
│   │
│   ├── static/                # Static assets
│   │   ├── css/
│   │   │   └── style.css     # Custom styles
│   │   └── js/
│   │       └── script.js     # Frontend JavaScript
│   │
│   └── main.py                # CLI entry point
│
├── data/                       # Data storage
│   ├── vahan_data.csv         # Vehicle database (CSV)
│   └── captured/              # Captured images
│
├── config/                     # Config files
│   └── config.py
│
├── scripts/                     # Utility scripts
│   ├── setup_mongodb.py
│   ├── import_csv_to_mongodb.py
│   └── migrate_to_mongodb.py
│
├── tests/                       # Test files
│   └── test_vehicle_model.py
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project readme
├── USAGE.md                    # Usage instructions
├── MONGODB_SETUP.md            # MongoDB setup guide
├── start_anpr_system.bat      # Windows startup script
└── .env                        # Environment variables
```

---

## ✨ Key Features

### **1. Multi-Algorithm Detection**
- 8 different detection algorithms
- Automatic fallback mechanism
- Best algorithm selection based on availability

### **2. Multi-OCR Support**
- EasyOCR (deep learning)
- Tesseract OCR (traditional)
- Google Gemini AI (advanced)
- Automatic fallback between engines

### **3. Real-time Processing**
- Sub-second detection times (Ultra-Fast)
- Performance monitoring
- Caching for repeated images

### **4. Robust Error Handling**
- Connection retry mechanisms
- Graceful degradation
- Detailed error logging
- User-friendly error messages

### **5. Database Flexibility**
- MongoDB Atlas (primary)
- CSV fallback
- Easy migration between systems

### **6. Web Interface**
- Responsive design
- Multiple input methods (upload, camera)
- Real-time feedback
- Performance metrics display

### **7. API-First Design**
- RESTful endpoints
- JSON responses
- Easy integration
- Comprehensive documentation

### **8. Indian License Plate Support**
- Format validation (LLDDLLDDDD, etc.)
- State code recognition
- OCR error correction
- Multiple format support

---

## 🔧 Configuration

### **Environment Variables** (`.env`)
```bash
# Database
DB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=anpr_system

# OCR
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Age Limits
DIESEL_AGE_LIMIT=10
PETROL_AGE_LIMIT=15

# Camera
CAMERA_SOURCE=0
IMAGE_WIDTH=640
IMAGE_HEIGHT=480

# Processing
MIN_CONFIDENCE=0.5
```

---

## 🚀 Performance Metrics

- **Detection Speed**: 1-5 seconds (depending on algorithm)
- **Accuracy**: 85-95% (depending on image quality)
- **Concurrent Requests**: Supports multiple simultaneous requests
- **Database Query Time**: <100ms (MongoDB Atlas)
- **Image Processing**: Real-time for standard images

---

## 📝 License & Credits

This project implements state-of-the-art ANPR technology for fuel eligibility checking at petrol stations.

**Technologies Used:**
- Flask, OpenCV, Tesseract, EasyOCR, YOLO, MongoDB Atlas, Bootstrap

**Algorithms:**
- Contour Detection, Edge Detection, YOLO Object Detection, OCR, Deep Learning

---

*Last Updated: December 2025*


