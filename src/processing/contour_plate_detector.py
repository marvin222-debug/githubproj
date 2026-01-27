#!/usr/bin/env python3
"""
Contour-based License Plate Detector
Based on the improved algorithm using contour detection and EasyOCR
"""

import cv2
import numpy as np
import logging
import re
from typing import List, Tuple, Optional, Dict
import imutils

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

class ContourPlateDetector:
    """
    Advanced license plate detector using contour detection and EasyOCR
    """
    
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.3):
        """
        Initialize the contour-based plate detector
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
        """
        self.min_confidence = min_confidence
        
        # Set up Tesseract if available
        if TESSERACT_AVAILABLE and tesseract_path:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Initialize EasyOCR if available
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("✅ EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        else:
            self.easyocr_reader = None
            logger.info("📝 EasyOCR not available, using Tesseract only")
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # Standard: KA01AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',   # Standard: KA01AB1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # Old format: KA1AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$',   # Short: KA01A1234
        ]
        
        logger.info("🚀 Contour Plate Detector initialized successfully")
    
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Preprocess image for contour detection - EXACT implementation from your code
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (gray, filtered, edges)
        """
        # Convert to grayscale - exactly like your code
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter - exactly like your code with same parameters
        bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Apply Canny edge detection - exactly like your code with same parameters
        edged = cv2.Canny(bfilter, 30, 200)
        
        logger.info(f"📸 Preprocessed image: gray={gray.shape}, filtered={bfilter.shape}, edges={edged.shape}")
        
        return gray, bfilter, edged
    
    def find_license_plate_contour(self, edged: np.ndarray) -> Optional[np.ndarray]:
        """
        Find the license plate contour using edge detection - EXACT implementation from your code
        
        Args:
            edged: Edge-detected image
            
        Returns:
            License plate contour or None
        """
        # Find contours - exactly like your code
        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        logger.info(f"🔍 Found {len(contours)} contours, checking top 10")
        
        # Loop through contours to find the best possible approximation of the license plate - improved version
        location = None
        best_contour = None
        best_score = 0
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            # Try different approximation values
            for epsilon_factor in [0.01, 0.02, 0.03, 0.05]:
                epsilon = epsilon_factor * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                logger.info(f"   Contour {i} (ε={epsilon_factor}): {len(approx)} points, area: {area}")
                
                # Accept 4-point contours (rectangles) - original approach
                if len(approx) == 4 and area > 5000:
                    location = approx
                    logger.info(f"✅ Found 4-point contour at index {i} with area {area}")
                    break
                
                # Also accept contours that look like license plates (rectangular shape)
                if 4 <= len(approx) <= 8 and area > 10000:
                    # Check if it's roughly rectangular by aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # License plates typically have aspect ratio between 2:1 and 5:1
                    if 2.0 <= aspect_ratio <= 5.5:
                        score = area / (len(approx) - 4 + 1)  # Prefer fewer points and larger area
                        if score > best_score:
                            best_score = score
                            best_contour = contour
                            logger.info(f"🔍 Better candidate at index {i}: {len(approx)} points, area: {area}, ratio: {aspect_ratio:.2f}")
            
            if location is not None:
                break
        
        # If no perfect 4-point contour found, use the best candidate
        if location is None and best_contour is not None:
            # Convert the best contour to a 4-point approximation
            x, y, w, h = cv2.boundingRect(best_contour)
            location = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]], dtype=np.int32)
            logger.info(f"✅ Using best rectangular candidate as 4-point approximation: ({x}, {y}, {w}, {h})")
        
        if location is not None:
            logger.info(f"🎯 License plate location found: {location.flatten()}")
        else:
            logger.info("❌ No 4-point contour found")
        
        return location
    
    def fallback_rectangle_detection(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """
        Fallback method using traditional rectangle detection
        
        Args:
            gray: Grayscale image
            
        Returns:
            License plate contour or None
        """
        try:
            # Apply additional preprocessing for rectangle detection
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Try different threshold values
            for thresh_val in [127, 100, 150, 80, 180]:
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Check if it looks like a license plate
                    if (2.0 <= aspect_ratio <= 5.5 and 
                        area > 5000 and 
                        w > 100 and h > 30):
                        
                        logger.info(f"🔍 Fallback found rectangle: ({x}, {y}, {w}, {h}), ratio: {aspect_ratio:.2f}")
                        
                        # Create 4-point contour from rectangle
                        location = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]], dtype=np.int32)
                        return location
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fallback detection failed: {e}")
            return None
    
    def extract_plate_region(self, image: np.ndarray, gray: np.ndarray, location: np.ndarray) -> np.ndarray:
        """
        Extract the license plate region using the detected contour - EXACT implementation from your code
        
        Args:
            image: Original image
            gray: Grayscale image
            location: License plate contour
            
        Returns:
            Cropped license plate image
        """
        # Create mask - exactly like your code
        mask = np.zeros(gray.shape, np.uint8)
        new_image = cv2.drawContours(mask, [location], 0, 255, -1)  # Draw contours on the mask image
        new_image = cv2.bitwise_and(image, image, mask=mask)  # Apply the mask to the original image
        
        # Get coordinates of the number plate area - exactly like your code
        (x, y) = np.where(mask == 255)  # Find coordinates of the white pixels
        (x1, y1) = (np.min(x), np.min(y))  # Top-left corner
        (x2, y2) = (np.max(x), np.max(y))  # Bottom-right corner
        
        # Crop the image to get the number plate region - exactly like your code
        cropped_image = gray[x1:x2+1, y1:y2+1]
        
        logger.info(f"📋 Extracted plate region: ({x1}, {y1}) to ({x2}, {y2}), size: {cropped_image.shape}")
        
        return cropped_image
    
    def read_text_easyocr(self, image: np.ndarray) -> Optional[str]:
        """
        Read text using EasyOCR - EXACT implementation from your code
        
        Args:
            image: License plate image
            
        Returns:
            Detected text or None
        """
        if not self.easyocr_reader:
            return None
        
        try:
            # Use EasyOCR to read the text from the cropped image - exactly like your code
            result = self.easyocr_reader.readtext(image)
            
            if result and len(result) > 0:
                # Extract the text from the OCR result - exactly like your code
                text = result[0][-2]  # This is exactly how you extract text: result[0][-2]
                
                logger.info(f"✅ EasyOCR raw result: {result}")
                logger.info(f"✅ EasyOCR detected text: {text}")
                
                # Clean the text - remove spaces and special characters
                cleaned_text = text.upper().replace(' ', '').replace('-', '')
                cleaned_text = ''.join(c for c in cleaned_text if c.isalnum())
                
                if len(cleaned_text) >= 6:
                    logger.info(f"🎯 Final cleaned text: {cleaned_text}")
                    return cleaned_text
            
            logger.info("❌ No text detected by EasyOCR")
            return None
            
        except Exception as e:
            logger.error(f"❌ EasyOCR failed: {e}")
            return None
    
    def read_text_tesseract(self, image: np.ndarray) -> Optional[str]:
        """
        Read text using Tesseract OCR
        
        Args:
            image: License plate image
            
        Returns:
            Detected text or None
        """
        if not TESSERACT_AVAILABLE:
            return None
        
        try:
            import pytesseract
            
            # Multiple configurations to try
            configs = [
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config).strip().upper()
                    cleaned_text = ''.join(c for c in text if c.isalnum())
                    
                    if len(cleaned_text) >= 6:
                        logger.info(f"✅ Tesseract detected: {cleaned_text}")
                        return cleaned_text
                        
                except Exception:
                    continue
            
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
        
        # Additional validation
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
        Main method to detect and read license plate using contour detection
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate information or None
        """
        try:
            logger.info(f"🔍 Starting contour-based plate detection on image of size: {image.shape}")
            
            # Step 1: Preprocess the image
            gray, bfilter, edged = self.preprocess_image(image)
            logger.info("📸 Image preprocessed successfully")
            
            # Step 2: Find license plate contour
            location = self.find_license_plate_contour(edged)
            
            if location is None:
                logger.info("❌ No license plate contour found, trying fallback detection")
                # Fallback: Use traditional rectangle detection
                location = self.fallback_rectangle_detection(gray)
                
                if location is None:
                    logger.info("❌ Fallback detection also failed")
                    return None
            
            logger.info("✅ License plate contour detected")
            
            # Step 3: Extract plate region
            cropped_image = self.extract_plate_region(image, gray, location)
            
            if cropped_image.size == 0:
                logger.info("❌ Failed to extract plate region")
                return None
            
            logger.info(f"📋 Plate region extracted: {cropped_image.shape}")
            
            # Step 4: Read text using OCR
            detected_text = None
            
            # Try EasyOCR first
            if self.easyocr_reader:
                detected_text = self.read_text_easyocr(cropped_image)
            
            # Fallback to Tesseract if EasyOCR fails
            if not detected_text and TESSERACT_AVAILABLE:
                detected_text = self.read_text_tesseract(cropped_image)
            
            if not detected_text:
                logger.info("❌ No text detected by OCR")
                return None
            
            # Step 5: Validate the detected text
            if not self.validate_plate_format(detected_text):
                logger.info(f"❌ Invalid plate format: {detected_text}")
                return None
            
            # Calculate bounding box from contour
            x, y, w, h = cv2.boundingRect(location)
            
            result = {
                "text": detected_text,
                "coordinates": (x, y, w, h),
                "confidence": 0.8,  # High confidence for contour-based detection
                "method": "contour_easyocr" if self.easyocr_reader else "contour_tesseract"
            }
            
            logger.info(f"🎯 Successfully detected plate: {detected_text}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in contour-based plate detection: {e}")
            return None
