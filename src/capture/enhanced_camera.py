#!/usr/bin/env python3
"""
Enhanced Camera Interface for ANPR System
Improved camera handling with better error recovery and auto-scan functionality
"""

import cv2
import time
import logging
import os
import threading
from typing import Optional, Tuple, Callable
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCamera:
    """
    Enhanced camera interface with improved error handling and auto-scan functionality
    """
    
    def __init__(self, camera_source: int = 0, width: int = 1280, height: int = 720):
        """
        Initialize the enhanced camera interface
        
        Args:
            camera_source: Camera index or video file path
            width: Desired frame width
            height: Desired frame height
        """
        self.camera_source = camera_source
        self.width = width
        self.height = height
        self.cap = None
        self.is_active = False
        self.auto_scan_active = False
        self.auto_scan_thread = None
        self.last_frame = None
        self.frame_lock = threading.Lock()
        
        # Auto-scan settings
        self.scan_interval = 2.0  # seconds
        self.scan_callback = None
        
    def open(self) -> bool:
        """
        Open the camera connection with enhanced error handling
        
        Returns:
            bool: True if camera opened successfully, False otherwise
        """
        try:
            # Try different camera backends for better compatibility
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_source, backend)
                    if self.cap.isOpened():
                        logger.info(f"✅ Camera opened with backend: {backend}")
                        break
                except Exception as e:
                    logger.warning(f"Backend {backend} failed: {e}")
                    continue
            
            if not self.cap or not self.cap.isOpened():
                logger.error(f"❌ Failed to open camera source: {self.camera_source}")
                return False
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"📹 Camera settings: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            # Test capture to ensure camera is working
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                logger.error("❌ Camera test capture failed")
                self.close()
                return False
            
            self.is_active = True
            logger.info(f"✅ Camera opened successfully: {self.camera_source}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error opening camera: {str(e)}")
            return False
    
    def close(self):
        """
        Close the camera connection and cleanup resources
        """
        self.is_active = False
        
        # Stop auto-scan if active
        if self.auto_scan_active:
            self.stop_auto_scan()
        
        # Close camera
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info("📹 Camera connection closed")
        
        self.cap = None
    
    def capture_frame(self) -> Optional[Tuple[bool, np.ndarray]]:
        """
        Capture a single frame from the camera with error recovery
        
        Returns:
            Tuple containing success flag and the captured frame
        """
        if not self.is_active or not self.cap or not self.cap.isOpened():
            if not self.open():
                return None
        
        try:
            # Clear buffer to get latest frame
            for _ in range(3):  # Skip a few frames to get the latest
                ret, frame = self.cap.read()
                if not ret:
                    break
            
            if not ret or frame is None:
                logger.warning("⚠️ Failed to capture frame, attempting recovery")
                
                # Try to recover by reopening camera
                self.close()
                if self.open():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        logger.info("✅ Camera recovery successful")
                    else:
                        logger.error("❌ Camera recovery failed")
                        return None
                else:
                    return None
            
            # Store last successful frame
            with self.frame_lock:
                self.last_frame = frame.copy()
            
            return True, frame
            
        except Exception as e:
            logger.error(f"❌ Error capturing frame: {str(e)}")
            return None
    
    def get_last_frame(self) -> Optional[np.ndarray]:
        """
        Get the last successfully captured frame
        
        Returns:
            Last captured frame or None
        """
        with self.frame_lock:
            return self.last_frame.copy() if self.last_frame is not None else None
    
    def save_image(self, frame: np.ndarray, directory: str = "data/captured", 
                   prefix: str = "plate") -> Optional[str]:
        """
        Save the captured frame to disk with enhanced naming
        
        Args:
            frame: The captured frame
            directory: The directory to save the image
            prefix: Filename prefix
            
        Returns:
            str: The path to the saved image or None if failed
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Generate a unique filename using timestamp
            timestamp = int(time.time() * 1000)
            filename = os.path.join(directory, f"{prefix}_{timestamp}.jpg")
            
            # Save the image with high quality
            cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            logger.info(f"💾 Image saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error saving image: {str(e)}")
            return None
    
    def start_auto_scan(self, callback: Callable[[np.ndarray], None], 
                       interval: float = 2.0) -> bool:
        """
        Start auto-scanning mode
        
        Args:
            callback: Function to call with each captured frame
            interval: Time interval between scans in seconds
            
        Returns:
            bool: True if auto-scan started successfully
        """
        if self.auto_scan_active:
            logger.warning("⚠️ Auto-scan already active")
            return False
        
        if not self.is_active:
            if not self.open():
                logger.error("❌ Cannot start auto-scan: camera not available")
                return False
        
        self.scan_callback = callback
        self.scan_interval = interval
        self.auto_scan_active = True
        
        # Start auto-scan thread
        self.auto_scan_thread = threading.Thread(target=self._auto_scan_worker, daemon=True)
        self.auto_scan_thread.start()
        
        logger.info(f"🔄 Auto-scan started with {interval}s interval")
        return True
    
    def stop_auto_scan(self):
        """
        Stop auto-scanning mode
        """
        if not self.auto_scan_active:
            return
        
        self.auto_scan_active = False
        
        if self.auto_scan_thread and self.auto_scan_thread.is_alive():
            self.auto_scan_thread.join(timeout=5.0)
        
        logger.info("⏹️ Auto-scan stopped")
    
    def _auto_scan_worker(self):
        """
        Worker thread for auto-scanning
        """
        last_scan_time = 0
        
        while self.auto_scan_active:
            try:
                current_time = time.time()
                
                # Check if it's time for next scan
                if current_time - last_scan_time >= self.scan_interval:
                    result = self.capture_frame()
                    
                    if result and self.scan_callback:
                        _, frame = result
                        try:
                            self.scan_callback(frame)
                        except Exception as e:
                            logger.error(f"❌ Auto-scan callback error: {e}")
                    
                    last_scan_time = current_time
                
                # Small sleep to prevent high CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Auto-scan worker error: {e}")
                time.sleep(1.0)  # Wait before retrying
    
    def is_camera_available(self) -> bool:
        """
        Check if camera is available and working
        
        Returns:
            bool: True if camera is available
        """
        return self.is_active and self.cap and self.cap.isOpened()
    
    def get_camera_info(self) -> dict:
        """
        Get camera information and settings
        
        Returns:
            dict: Camera information
        """
        if not self.is_camera_available():
            return {"available": False}
        
        try:
            info = {
                "available": True,
                "source": self.camera_source,
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.cap.get(cv2.CAP_PROP_FPS),
                "auto_scan_active": self.auto_scan_active,
                "scan_interval": self.scan_interval
            }
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting camera info: {e}")
            return {"available": False, "error": str(e)}
    
    def __del__(self):
        """
        Cleanup when object is destroyed
        """
        self.close()
