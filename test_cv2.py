print("Importing cv2...")
try:
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
except Exception as e:
    print(f"OpenCV failed: {e}")
