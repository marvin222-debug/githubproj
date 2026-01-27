import sys
print("Testing imports...")
try:
    import numpy
    print(f"Numpy version: {numpy.__version__}")
except Exception as e:
    print(f"Numpy failed: {e}")

try:
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
except Exception as e:
    print(f"OpenCV failed: {e}")

try:
    import torch
    print(f"Torch version: {torch.__version__}")
except Exception as e:
    print(f"Torch failed: {e}")

try:
    import torchvision
    print(f"Torchvision version: {torchvision.__version__}")
except Exception as e:
    print(f"Torchvision failed: {e}")

print("Imports finished.")
