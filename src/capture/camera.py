import cv2
import time
import logging
import os
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Camera:
    """
    Camera interface for capturing license plate images
    """
    def __init__(self, camera_source: int = 0, width: int = 640, height: int = 480):
        """
        Initialize the camera interface
        
        Args:
            camera_source: Camera index or video file path
            width: Desired frame width
            height: Desired frame height
        """
        self.camera_source = camera_source
        self.width = width
        self.height = height
        self.cap = None
        
    def open(self) -> bool:
        """
        Open the camera connection
        
        Returns:
            bool: True if camera opened successfully, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_source)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera source: {self.camera_source}")
                return False
                
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            logger.info(f"Camera opened successfully: {self.camera_source}")
            return True
        except Exception as e:
            logger.error(f"Error opening camera: {str(e)}")
            return False
    
    def close(self):
        """
        Close the camera connection
        """
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info("Camera connection closed")
    
    def capture_frame(self) -> Optional[Tuple[bool, cv2.Mat]]:
        """
        Capture a single frame from the camera
        
        Returns:
            Tuple containing success flag and the captured frame
        """
        if not self.cap or not self.cap.isOpened():
            if not self.open():
                return None
        
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            return None
            
        return True, frame
    
    def save_image(self, frame: cv2.Mat, directory: str = "../data/captured") -> Optional[str]:
        """
        Save the captured frame to disk
        
        Args:
            frame: The captured frame
            directory: The directory to save the image
            
        Returns:
            str: The path to the saved image or None if failed
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Generate a unique filename using timestamp
            timestamp = int(time.time() * 1000)
            filename = f"{directory}/plate_{timestamp}.jpg"
            
            # Save the image
            cv2.imwrite(filename, frame)
            logger.info(f"Image saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return None 