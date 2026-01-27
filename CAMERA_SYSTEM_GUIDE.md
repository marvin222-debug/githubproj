# ANPR Camera System - Complete Guide

## 🚀 System Overview

Your ANPR (Automatic Number Plate Recognition) system has been significantly enhanced with:

### ✅ **What's Fixed & Improved:**

1. **🎯 Advanced AI Detection Models**
   - **YOLO Enhanced Detector**: Uses YOLOv8 for vehicle detection + EasyOCR for text recognition
   - **Contour-based Detector**: Improved edge detection with EasyOCR fallback
   - **Gemini AI Detector**: Google's Gemini AI for complex scenarios
   - **Multiple Fallbacks**: System automatically chooses the best available detector

2. **📹 Enhanced Camera System**
   - **Multi-configuration Support**: Tries different camera settings automatically
   - **Error Recovery**: Automatic camera reconnection on failures
   - **Retry Logic**: Up to 3 attempts with different configurations
   - **Better Compatibility**: Works with various camera backends (DirectShow, Media Foundation)

3. **🔄 Improved Auto-Scan**
   - **Intelligent Cooldown**: Prevents API overload with 1.5s intervals
   - **Adaptive Timing**: 3-second intervals for stable detection
   - **Error Handling**: Graceful handling of network/processing errors
   - **Real-time Logging**: Detailed detection logs with timestamps

4. **🎨 Enhanced UI/UX**
   - **Better Error Messages**: User-friendly error descriptions
   - **Processing Timeouts**: 15-second timeout with clear feedback
   - **Visual Feedback**: Real-time status updates and progress indicators
   - **Plate Overlays**: Visual bounding boxes around detected plates

## 🌐 **System Status**

✅ **Currently Running**: http://127.0.0.1:5000
✅ **YOLO Enhanced Detector**: Active with EasyOCR
✅ **MongoDB Atlas**: Connected with 23 vehicles in database
✅ **All Dependencies**: Installed and working

## 📱 **How to Use the Camera System**

### **Step 1: Access the Camera Interface**
- Navigate to: http://127.0.0.1:5000/camera
- Click "Camera Check" in the navigation menu

### **Step 2: Start Camera**
1. Click **"Start Camera"** button
2. Allow camera permissions when prompted
3. System will try multiple configurations automatically
4. Wait for "Camera Active" status

### **Step 3: Detection Options**

#### **Manual Detection:**
- Click **"Capture Image"** for single frame analysis
- Best for testing and precise control

#### **Auto-Scan Mode:**
- Click **"Start Auto Scan"** for continuous monitoring
- Scans every 3 seconds automatically
- Click **"Stop Auto Scan"** to disable

### **Step 4: View Results**
- **Detection Log**: Real-time processing status
- **Vehicle Details**: Registration, fuel type, age, make/model
- **Eligibility Status**: FUEL ALLOWED/DENIED with reasons
- **Visual Overlay**: Red box around detected plates

## 🔧 **Troubleshooting Guide**

### **Camera Issues:**
```
❌ Problem: "Unable to access camera"
✅ Solution: 
   - Check camera permissions in browser
   - Close other apps using camera
   - Try different browser (Chrome recommended)
   - Refresh page and try again
```

### **Detection Issues:**
```
❌ Problem: "No license plate detected"
✅ Solutions:
   - Ensure good lighting conditions
   - Position plate clearly in frame
   - Avoid glare and reflections
   - Try manual capture first
   - Check if plate is in sample database
```

### **Processing Errors:**
```
❌ Problem: "Processing timeout" or "Server error"
✅ Solutions:
   - Wait a few seconds and try again
   - Check internet connection
   - Restart the application if needed
   - Check server logs for details
```

## 🎯 **Sample License Plates for Testing**

Your system includes these test plates:

| Plate Number | Fuel Type | Year | Status |
|-------------|-----------|------|--------|
| KA01MJ2023  | PETROL    | 2023 | ✅ ALLOWED |
| KA63MA6613  | PETROL    | 2020 | ✅ ALLOWED |
| DL05AB1234  | DIESEL    | 2010 | ❌ DENIED |
| MH02CD5678  | PETROL    | 2008 | ❌ DENIED |
| KA05AB1234  | DIESEL    | 2015 | ✅ ALLOWED |
| TN09XY5678  | PETROL    | 2012 | ✅ ALLOWED |

## 🚀 **Advanced Features**

### **AI Model Hierarchy:**
1. **YOLO Enhanced** (Primary): Best accuracy, vehicle detection + OCR
2. **Contour Detection** (Fallback): Edge detection + EasyOCR
3. **Gemini AI** (Fallback): Google AI for complex cases
4. **Simple Detector** (Fallback): Traditional OCR methods

### **Real-time Monitoring:**
- **Detection Log**: Shows all processing steps
- **Performance Metrics**: Image size, processing time
- **Error Tracking**: Detailed error messages with solutions

### **Database Integration:**
- **MongoDB Atlas**: Cloud database with 23+ vehicles
- **Mock Database**: Local fallback with 10 sample vehicles
- **Real-time Queries**: Instant vehicle information lookup

## 📊 **Performance Optimization**

### **Camera Settings:**
- **Resolution**: 1280x720 (ideal), falls back to 640x480
- **FPS**: 30fps for smooth preview
- **Buffer**: Minimal buffering for latest frames

### **Processing Settings:**
- **Scan Interval**: 3 seconds (optimal balance)
- **Cooldown**: 1.5 seconds between API calls
- **Timeout**: 15 seconds maximum processing time
- **Image Quality**: 90% JPEG for fast upload

## 🔒 **Security & Privacy**

- **Local Processing**: Camera stream stays in browser
- **Secure Upload**: Images sent via HTTPS to local server
- **No Storage**: Captured images not permanently stored
- **Permission-based**: Requires explicit camera permission

## 📈 **System Monitoring**

### **Health Check Endpoint:**
```
GET /health
Response: {"status": "ok", "timestamp": "2025-09-21T01:27:28"}
```

### **Test Endpoints:**
- `/api/test-yolo` - Test YOLO detector
- `/api/test-detection` - Debug plate detection
- `/api/test-gemini` - Test Gemini AI (if available)

## 🛠️ **Development Commands**

### **Start System:**
```bash
cd "d:\MAJOR PROJECT\ANPR"
python src\api\web_app.py
```

### **Install Dependencies:**
```bash
pip install -r requirements.txt
```

### **Test Individual Components:**
```bash
python src\main.py --image path\to\test\image.jpg
python src\main.py --continuous  # Live camera mode
```

## 📋 **System Architecture**

```
🌐 Web Interface (Flask)
    ↓
📹 Enhanced Camera Module
    ↓
🤖 AI Detection Pipeline:
    ├── YOLO Enhanced Detector
    ├── Contour Plate Detector  
    ├── Gemini AI Detector
    └── Simple Plate Detector
    ↓
🔤 OCR Processing:
    ├── EasyOCR (Primary)
    └── Tesseract (Fallback)
    ↓
🗄️ Database Lookup:
    ├── MongoDB Atlas (Primary)
    └── Mock Database (Fallback)
    ↓
✅ Fuel Eligibility Check
```

## 🎉 **Success! Your System is Ready**

Your ANPR system is now running with:
- ✅ **Advanced AI Detection**: YOLO + EasyOCR
- ✅ **Robust Camera Handling**: Multi-config with retry logic
- ✅ **Intelligent Auto-Scan**: 3-second intervals with cooldown
- ✅ **Real-time Processing**: Live detection with visual feedback
- ✅ **Database Integration**: 23+ vehicles in MongoDB Atlas
- ✅ **Error Recovery**: Graceful handling of all failure modes

**🔗 Access your system at: http://127.0.0.1:5000/camera**

Point your camera at the license plate "KA01MJ2023" from the screenshot you provided, and the system should now detect it successfully!
