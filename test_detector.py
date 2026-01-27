import sys
sys.path.append('.')
from src.processing.ultra_fast_detector import UltraFastDetector
import cv2
import numpy as np

# Test the detector
detector = UltraFastDetector()
print('UltraFastDetector initialized')

# Create a test image with text
test_img = np.ones((200, 400, 3), dtype=np.uint8) * 255
cv2.putText(test_img, 'KA01MJ2023', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

# Test detection
result = detector.detect_and_read_plate(test_img)
print(f'Detection result: {result}')
