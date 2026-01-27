#!/usr/bin/env python3
"""
Test script for simple license plate detector
"""

import os
import sys
import cv2
import numpy as np

# Add the project root to Python path
sys.path.append(os.path.abspath('.'))

def create_test_image():
    """Create a test image with a license plate"""
    # Create a white background
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    
    # Add some background noise
    noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    
    # Draw a license plate
    plate_x, plate_y = 50, 80
    plate_w, plate_h = 300, 60
    
    # Draw plate background
    cv2.rectangle(img, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (255, 255, 255), -1)
    cv2.rectangle(img, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (0, 0, 0), 2)
    
    # Add "IND" text
    cv2.putText(img, "IND", (plate_x + 10, plate_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Add main license plate number
    cv2.putText(img, "KA01MJ2023", (plate_x + 80, plate_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    
    return img

def test_detection():
    """Test the simple detection system"""
    print("🧪 Testing Simple License Plate Detection")
    print("=" * 50)
    
    try:
        from src.processing.simple_plate_detector import SimplePlateDetector
        
        # Initialize detector
        detector = SimplePlateDetector()
        
        # Create test image
        test_image = create_test_image()
        
        # Save test image for debugging
        cv2.imwrite("test_plate_simple.png", test_image)
        print("✅ Test image created: test_plate_simple.png")
        
        # Test detection
        print("🔍 Testing plate detection...")
        result = detector.detect_and_read_plate(test_image)
        
        if result:
            print(f"✅ Detection successful!")
            print(f"   Plate: {result['text']}")
            print(f"   Method: {result['method']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Coordinates: {result['coordinates']}")
        else:
            print("❌ No plate detected")
            
        # Test plate detection only
        print("\n🔍 Testing plate region detection...")
        plates = detector.detect_plates(test_image)
        print(f"Found {len(plates)} potential plates")
        
        for i, (x1, y1, x2, y2, conf) in enumerate(plates):
            print(f"   Plate {i}: ({x1}, {y1}, {x2}, {y2}) confidence: {conf:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detection()

