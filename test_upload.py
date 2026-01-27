#!/usr/bin/env python3
"""
Test script to verify the upload endpoint works
"""

import requests
import cv2
import numpy as np
import os

def create_test_image():
    """Create a simple test license plate image"""
    # Create white background
    img = np.ones((100, 400, 3), dtype=np.uint8) * 255
    
    # Add black text
    cv2.putText(img, 'KA01MJ2023', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    
    # Save as test image
    cv2.imwrite('test_upload_image.png', img)
    return 'test_upload_image.png'

def test_upload_endpoint():
    """Test the upload endpoint directly"""
    
    # Create test image
    image_path = create_test_image()
    
    try:
        # Test the upload endpoint
        url = 'http://localhost:5000/api/process'
        
        with open(image_path, 'rb') as f:
            files = {'image': ('test.png', f, 'image/png')}
            
            print(f"🔄 Testing upload to {url}")
            response = requests.post(url, files=files, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Upload test SUCCESSFUL!")
                    print(f"   Detected plate: {data.get('registration_number')}")
                else:
                    print("❌ Upload test FAILED!")
                    print(f"   Error: {data.get('message')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    print("🧪 Testing ANPR Upload Endpoint")
    print("=" * 40)
    test_upload_endpoint()
