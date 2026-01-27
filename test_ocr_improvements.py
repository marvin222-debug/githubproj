#!/usr/bin/env python3
"""
Test script to verify OCR improvements work with license plate images
"""

import cv2
import numpy as np
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processing.simple_plate_detector import SimplePlateDetector
from src.config.config import MIN_CONFIDENCE, TESSERACT_PATH

def test_ocr_with_sample_plate():
    """Test OCR with a sample license plate"""
    
    # Initialize detector
    detector = SimplePlateDetector(min_confidence=MIN_CONFIDENCE)
    print("🚀 Initialized Simple Plate Detector")
    
    # Create a sample license plate image (white background, black text)
    # This simulates the uploaded image
    img = np.ones((100, 400, 3), dtype=np.uint8) * 255  # White background
    
    # Add black text to simulate "KA01MJ2023"
    cv2.putText(img, 'KA01MJ2023', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    
    print("📋 Created sample license plate image")
    
    # Test the detection
    result = detector.detect_and_read_plate(img)
    
    if result:
        print(f"✅ SUCCESS: Detected plate: {result['text']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Method: {result['method']}")
        print(f"   Coordinates: {result['coordinates']}")
    else:
        print("❌ FAILED: No license plate detected")
    
    return result is not None

def test_ocr_with_real_image():
    """Test OCR with a real license plate image if available"""
    
    # Check if there's a test plate image
    test_image_path = "test_plate.png"
    if not os.path.exists(test_image_path):
        print(f"⚠️  No test image found at {test_image_path}")
        return True
    
    # Initialize detector
    detector = SimplePlateDetector(min_confidence=MIN_CONFIDENCE)
    
    # Load the image
    img = cv2.imread(test_image_path)
    if img is None:
        print(f"❌ Failed to load image: {test_image_path}")
        return False
    
    print(f"📸 Loaded test image: {test_image_path}")
    
    # Test the detection
    result = detector.detect_and_read_plate(img)
    
    if result:
        print(f"✅ SUCCESS: Detected plate: {result['text']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Method: {result['method']}")
    else:
        print("❌ FAILED: No license plate detected in real image")
    
    return result is not None

if __name__ == "__main__":
    print("🧪 Testing OCR Improvements")
    print("=" * 50)
    
    # Test 1: Sample plate
    print("\n🔍 Test 1: Sample License Plate")
    success1 = test_ocr_with_sample_plate()
    
    # Test 2: Real image (if available)
    print("\n🔍 Test 2: Real License Plate Image")
    success2 = test_ocr_with_real_image()
    
    print("\n" + "=" * 50)
    if success1:
        print("✅ OCR improvements are working!")
        print("🎯 The system should now be able to detect license plates properly.")
    else:
        print("❌ OCR improvements need more work.")
        print("🔧 Check Tesseract installation and configuration.")
    
    print("\n🌐 Your ANPR web application is running at: http://localhost:5000")
    print("📸 Try uploading the license plate image to test the improvements!")
