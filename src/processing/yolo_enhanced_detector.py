#!/usr/bin/env python3
"""
Enhanced YOLO-based License Plate Detector
Uses YOLOv8 for plate detection and EasyOCR for text recognition
"""

import cv2
import numpy as np
import logging
import re
from typing import List, Tuple, Optional, Dict
import os

# Try to import YOLOv8
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLOv8 not available, falling back to contour detection")

# Try to import EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available, falling back to Tesseract")

# Fallback to Tesseract if EasyOCR is not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class YOLOEnhancedDetector:
    """
    Enhanced YOLO-based license plate detector with multiple fallback options
    """
    
    def __init__(self, model_path: str = None, tesseract_path: str = None, min_confidence: float = 0.3):
        """
        Initialize the YOLO enhanced detector
        
        Args:
            model_path: Path to YOLO model (will download if not provided)
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
        """
        self.min_confidence = min_confidence
        self.yolo_model = None
        self.easyocr_reader = None
        
        # Set up Tesseract if available
        if TESSERACT_AVAILABLE and tesseract_path:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Initialize YOLO model
        if YOLO_AVAILABLE:
            try:
                # Use YOLOv8n (nano) for faster inference
                if model_path and os.path.exists(model_path):
                    self.yolo_model = YOLO(model_path)
                else:
                    # Download YOLOv8n if not available
                    self.yolo_model = YOLO('yolov8n.pt')
                logger.info("✅ YOLOv8 model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ YOLO initialization failed: {e}")
                self.yolo_model = None
        
        # Initialize EasyOCR if available
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("✅ EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # Standard: KA01AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',   # Standard: KA01AB1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # Old format: KA1AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$',   # Short: KA01A1234
        ]
        
        logger.info("🚀 YOLO Enhanced Detector initialized successfully")
    
    def detect_vehicles_yolo(self, image: np.ndarray) -> List[Dict]:
        """
        Detect vehicles using YOLO and extract potential license plate regions
        
        Args:
            image: Input image
            
        Returns:
            List of detected vehicle regions with bounding boxes
        """
        if not self.yolo_model:
            return []
        
        try:
            # Run YOLO detection
            results = self.yolo_model(image, conf=0.3, classes=[2, 3, 5, 7])  # car, motorcycle, bus, truck
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Focus on the lower part of the vehicle for license plates
                        height = y2 - y1
                        plate_y1 = int(y1 + height * 0.6)  # Lower 40% of vehicle
                        plate_y2 = int(y2)
                        
                        # Expand horizontally for better plate capture
                        width = x2 - x1
                        plate_x1 = max(0, int(x1 - width * 0.1))
                        plate_x2 = min(image.shape[1], int(x2 + width * 0.1))
                        
                        detections.append({
                            'bbox': (int(plate_x1), int(plate_y1), int(plate_x2), int(plate_y2)),
                            'confidence': float(confidence),
                            'class_id': class_id
                        })
            
            logger.info(f"🚗 YOLO detected {len(detections)} vehicles")
            return detections
            
        except Exception as e:
            logger.error(f"❌ YOLO vehicle detection failed: {e}")
            return []
    
    def detect_license_plates_contour(self, image: np.ndarray) -> List[Dict]:
        """
        Fallback contour-based license plate detection
        
        Args:
            image: Input image
            
        Returns:
            List of potential license plate regions
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Apply Canny edge detection
            edged = cv2.Canny(filtered, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]
            
            detections = []
            for contour in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if contour has 4 points (rectangle-like)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    area = w * h
                    
                    # License plate characteristics
                    if (2.0 <= aspect_ratio <= 5.5 and 
                        area > 2000 and 
                        w > 50 and h > 15):
                        
                        detections.append({
                            'bbox': (x, y, x + w, y + h),
                            'confidence': 0.7,
                            'method': 'contour'
                        })
            
            logger.info(f"🔍 Contour detection found {len(detections)} potential plates")
            return detections
            
        except Exception as e:
            logger.error(f"❌ Contour detection failed: {e}")
            return []
    
    def extract_text_easyocr(self, image: np.ndarray) -> Optional[str]:
        """
        Extract text using EasyOCR
        
        Args:
            image: License plate image
            
        Returns:
            Detected text or None
        """
        if not self.easyocr_reader:
            return None
        
        try:
            # Use EasyOCR to read the text
            results = self.easyocr_reader.readtext(image)
            
            if results:
                # Get the text with highest confidence
                best_result = max(results, key=lambda x: x[2])
                text = best_result[1]
                confidence = best_result[2]
                
                if confidence > 0.3:  # Minimum confidence threshold
                    # Clean the text
                    cleaned_text = text.upper().replace(' ', '').replace('-', '')
                    cleaned_text = ''.join(c for c in cleaned_text if c.isalnum())
                    
                    if len(cleaned_text) >= 6:
                        logger.info(f"✅ EasyOCR detected: {cleaned_text} (confidence: {confidence:.2f})")
                        return cleaned_text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ EasyOCR failed: {e}")
            return None
    
    def extract_text_tesseract(self, image: np.ndarray) -> Optional[str]:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: License plate image
            
        Returns:
            Detected text or None
        """
        if not TESSERACT_AVAILABLE:
            return None
        
        try:
            import pytesseract
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR configuration for license plates
            config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            
            text = pytesseract.image_to_string(thresh, config=config).strip().upper()
            cleaned_text = ''.join(c for c in text if c.isalnum())
            
            if len(cleaned_text) >= 6:
                logger.info(f"✅ Tesseract detected: {cleaned_text}")
                return cleaned_text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Tesseract failed: {e}")
            return None
    
    def validate_plate_format(self, text: str) -> bool:
        """
        Validate if text matches Indian license plate format
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid format
        """
        if not text or len(text) < 6 or len(text) > 12:
            return False
        
        text = text.upper().replace(' ', '').replace('-', '')
        
        # Check against patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        # Additional validation for Indian plates
        if len(text) >= 8:
            # Must start with 2 letters (state code)
            if not re.match(r'^[A-Z]{2}', text):
                return False
            # Must contain both letters and digits
            has_alpha = any(c.isalpha() for c in text)
            has_digit = any(c.isdigit() for c in text)
            return has_alpha and has_digit
        
        return False
    
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main method to detect and read license plate
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate information or None
        """
        try:
            logger.info(f"🔍 Starting enhanced plate detection on image of size: {image.shape}")
            
            # Method 1: Try YOLO-based vehicle detection first
            vehicle_detections = self.detect_vehicles_yolo(image)
            
            # Method 2: Fallback to contour detection
            if not vehicle_detections:
                logger.info("🔄 No vehicles detected by YOLO, trying contour detection")
                plate_detections = self.detect_license_plates_contour(image)
            else:
                plate_detections = vehicle_detections
            
            if not plate_detections:
                logger.info("❌ No potential license plate regions found")
                return None
            
            # Process each detection
            best_result = None
            best_confidence = 0
            
            for detection in plate_detections:
                bbox = detection['bbox']
                x1, y1, x2, y2 = bbox
                
                # Extract region
                plate_region = image[y1:y2, x1:x2]
                
                if plate_region.size == 0:
                    continue
                
                # Try OCR methods
                detected_text = None
                
                # Try EasyOCR first
                if self.easyocr_reader:
                    detected_text = self.extract_text_easyocr(plate_region)
                
                # Fallback to Tesseract
                if not detected_text and TESSERACT_AVAILABLE:
                    detected_text = self.extract_text_tesseract(plate_region)
                
                if detected_text and self.validate_plate_format(detected_text):
                    confidence = detection.get('confidence', 0.8)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_result = {
                            "text": detected_text,
                            "coordinates": (x1, y1, x2 - x1, y2 - y1),
                            "confidence": confidence,
                            "method": "yolo_enhanced" if self.yolo_model else "contour_enhanced"
                        }
            
            if best_result:
                logger.info(f"🎯 Successfully detected plate: {best_result['text']}")
                return best_result
            else:
                logger.info("❌ No valid license plate text detected")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced plate detection: {e}")
            return None
