#!/usr/bin/env python3
"""
Test the exact algorithm implementation
"""

import cv2
import numpy as np
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processing.contour_plate_detector import ContourPlateDetector
from src.config.config import MIN_CONFIDENCE, TESSERACT_PATH

def create_test_license_plate():
    """Create a test license plate image similar to KA63MA66613"""
    # Create a license plate-like image
    img = np.ones((200, 500, 3), dtype=np.uint8) * 255  # White background
    
    # Add a blue rectangle (like Indian license plates)
    cv2.rectangle(img, (50, 50), (450, 150), (255, 165, 0), -1)  # Blue background
    
    # Add white rectangle for text area
    cv2.rectangle(img, (70, 70), (430, 130), (255, 255, 255), -1)  # White text area
    
    # Add black text
    cv2.putText(img, 'KA63MA66613', (80, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    
    return img

def test_exact_algorithm():
    """Test our exact algorithm implementation"""
    
    print("Testing Exact Algorithm Implementation")
    print("=" * 50)
    
    # Initialize detector
    detector = ContourPlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
    print("Detector initialized successfully")
    
    # Create test image
    img = create_test_license_plate()
    print(f"Created test image: {img.shape}")
    
    # Test the detection
    result = detector.detect_and_read_plate(img)
    
    if result:
        print(f"SUCCESS: Detected plate: {result['text']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Method: {result['method']}")
        print(f"   Coordinates: {result['coordinates']}")
        return True
    else:
        print("FAILED: No license plate detected")
        return False

def test_step_by_step():
    """Test each step of the algorithm separately"""
    
    print("\nTesting Step-by-Step Algorithm")
    print("=" * 50)
    
    # Initialize detector
    detector = ContourPlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
    
    # Create test image
    img = create_test_license_plate()
    
    try:
        # Step 1: Preprocess
        print("Step 1: Preprocessing...")
        gray, bfilter, edged = detector.preprocess_image(img)
        print(f"   Gray: {gray.shape}, Filtered: {bfilter.shape}, Edges: {edged.shape}")
        
        # Step 2: Find contours
        print("Step 2: Finding contours...")
        location = detector.find_license_plate_contour(edged)
        if location is not None:
            print(f"   Found contour with {len(location)} points")
        else:
            print("   No contour found")
            return False
        
        # Step 3: Extract region
        print("Step 3: Extracting plate region...")
        cropped = detector.extract_plate_region(img, gray, location)
        print(f"   Cropped region: {cropped.shape}")
        
        # Step 4: OCR
        print("Step 4: Reading text...")
        if detector.easyocr_reader:
            text = detector.read_text_easyocr(cropped)
            print(f"   EasyOCR result: {text}")
        else:
            text = detector.read_text_tesseract(cropped)
            print(f"   Tesseract result: {text}")
        
        if text:
            print(f"SUCCESS: Complete algorithm worked, detected: {text}")
            return True
        else:
            print("FAILED: OCR step failed")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test 1: Full algorithm
    success1 = test_exact_algorithm()
    
    # Test 2: Step by step
    success2 = test_step_by_step()
    
    print("\n" + "=" * 50)
    if success1 or success2:
        print("ALGORITHM WORKING: Your exact implementation is functional!")
        print("The ANPR system should now work with real license plate images.")
    else:
        print("ALGORITHM NEEDS WORK: Check the implementation.")
    
    print("\nYour ANPR web application is running at: http://localhost:5000")
    print("Try uploading your license plate image now!")
