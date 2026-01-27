#!/usr/bin/env python3
"""
Optimized License Plate Detector
Specifically designed for Indian license plates with high accuracy
"""

import cv2
import numpy as np
import logging
import re
from typing import List, Tuple, Optional, Dict
import os

# Try to import EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Fallback to Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OptimizedPlateDetector:
    """
    Highly optimized license plate detector for Indian plates
    Uses multiple detection strategies for maximum accuracy
    """
    
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.3):
        """
        Initialize the optimized plate detector
        
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
                logger.info("✅ EasyOCR initialized for optimized detection")
            except Exception as e:
                logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        else:
            self.easyocr_reader = None
        
        # Indian license plate patterns (comprehensive)
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # KA01AB1234, KA01A1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # KA1AB1234 (old format)
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',   # Standard format
        ]
        
        logger.info("🚀 Optimized Plate Detector initialized")
    
    def preprocess_for_ocr(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Create multiple preprocessed versions for better OCR accuracy
        
        Args:
            image: Input license plate region
            
        Returns:
            List of preprocessed images
        """
        processed_images = []
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Original grayscale
            processed_images.append(gray)
            
            # Method 1: Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh1 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(thresh1)
            
            # Method 2: Adaptive threshold
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            processed_images.append(adaptive)
            
            # Method 3: Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morph = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
            processed_images.append(morph)
            
            # Method 4: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, thresh_enhanced = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(thresh_enhanced)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"❌ Preprocessing failed: {e}")
            return [image]
    
    def detect_plate_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect potential license plate regions using multiple methods
        
        Args:
            image: Input image
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        regions = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Contour-based detection
            regions.extend(self._detect_by_contours(gray))
            
            # Method 2: Rectangle detection
            regions.extend(self._detect_by_rectangles(gray))
            
            # Method 3: Edge-based detection
            regions.extend(self._detect_by_edges(gray))
            
            # Remove duplicates and filter by size
            regions = self._filter_regions(regions, image.shape)
            
            logger.info(f"🔍 Found {len(regions)} potential plate regions")
            return regions
            
        except Exception as e:
            logger.error(f"❌ Region detection failed: {e}")
            return []
    
    def _detect_by_contours(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Contour-based detection method"""
        regions = []
        
        try:
            # Apply bilateral filter
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Edge detection
            edges = cv2.Canny(filtered, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]
            
            for contour in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check for rectangular shape
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    area = w * h
                    
                    # License plate characteristics
                    if (2.0 <= aspect_ratio <= 5.5 and 
                        area > 1000 and 
                        w > 60 and h > 15):
                        regions.append((x, y, w, h))
            
            return regions
            
        except Exception as e:
            logger.error(f"❌ Contour detection failed: {e}")
            return []
    
    def _detect_by_rectangles(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Rectangle detection method"""
        regions = []
        
        try:
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Try different threshold values
            for thresh_val in [100, 127, 150, 80, 180]:
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    area = w * h
                    
                    # Check license plate characteristics
                    if (2.0 <= aspect_ratio <= 5.5 and 
                        area > 1000 and 
                        w > 60 and h > 15):
                        regions.append((x, y, w, h))
            
            return regions
            
        except Exception as e:
            logger.error(f"❌ Rectangle detection failed: {e}")
            return []
    
    def _detect_by_edges(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Edge-based detection method"""
        regions = []
        
        try:
            # Apply different edge detection methods
            edges1 = cv2.Canny(gray, 50, 150)
            edges2 = cv2.Canny(gray, 100, 200)
            
            for edges in [edges1, edges2]:
                # Find lines using HoughLines
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                       minLineLength=30, maxLineGap=10)
                
                if lines is not None:
                    # Group lines to find rectangular regions
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        
                        # Create bounding box around line
                        x = min(x1, x2) - 10
                        y = min(y1, y2) - 10
                        w = abs(x2 - x1) + 20
                        h = abs(y2 - y1) + 20
                        
                        # Ensure minimum dimensions
                        if w < 60:
                            w = 60
                        if h < 15:
                            h = 15
                        
                        aspect_ratio = w / h if h > 0 else 0
                        
                        if 2.0 <= aspect_ratio <= 5.5:
                            regions.append((max(0, x), max(0, y), w, h))
            
            return regions
            
        except Exception as e:
            logger.error(f"❌ Edge detection failed: {e}")
            return []
    
    def _filter_regions(self, regions: List[Tuple[int, int, int, int]], 
                       image_shape: Tuple[int, int]) -> List[Tuple[int, int, int, int]]:
        """Filter and deduplicate regions"""
        if not regions:
            return []
        
        height, width = image_shape[:2]
        filtered = []
        
        # Remove duplicates and invalid regions
        for x, y, w, h in regions:
            # Ensure region is within image bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = min(w, width - x)
            h = min(h, height - y)
            
            # Check minimum size
            if w > 60 and h > 15:
                # Check for duplicates
                is_duplicate = False
                for fx, fy, fw, fh in filtered:
                    # Calculate overlap
                    overlap_x = max(0, min(x + w, fx + fw) - max(x, fx))
                    overlap_y = max(0, min(y + h, fy + fh) - max(y, fy))
                    overlap_area = overlap_x * overlap_y
                    
                    area1 = w * h
                    area2 = fw * fh
                    
                    if overlap_area > 0.5 * min(area1, area2):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered.append((x, y, w, h))
        
        # Sort by area (largest first)
        filtered.sort(key=lambda r: r[2] * r[3], reverse=True)
        
        return filtered[:10]  # Return top 10 regions
    
    def extract_text_from_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Extract text from a specific region using multiple OCR methods
        
        Args:
            image: Full image
            region: Bounding box (x, y, w, h)
            
        Returns:
            Detected text or None
        """
        try:
            x, y, w, h = region
            
            # Extract region with padding
            padding = 5
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return None
            
            # Resize if too small
            if roi.shape[0] < 30 or roi.shape[1] < 100:
                scale_factor = max(30 / roi.shape[0], 100 / roi.shape[1])
                new_width = int(roi.shape[1] * scale_factor)
                new_height = int(roi.shape[0] * scale_factor)
                roi = cv2.resize(roi, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Try multiple preprocessing methods
            processed_images = self.preprocess_for_ocr(roi)
            
            best_text = None
            best_confidence = 0
            
            for processed_img in processed_images:
                # Try EasyOCR first
                if self.easyocr_reader:
                    text = self._extract_with_easyocr(processed_img)
                    if text and self.validate_plate_format(text):
                        return text
                
                # Try Tesseract
                if TESSERACT_AVAILABLE:
                    text = self._extract_with_tesseract(processed_img)
                    if text and self.validate_plate_format(text):
                        return text
            
            return best_text
            
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return None
    
    def _extract_with_easyocr(self, image: np.ndarray) -> Optional[str]:
        """Extract text using EasyOCR"""
        try:
            results = self.easyocr_reader.readtext(image)
            
            if results:
                # Get result with highest confidence
                best_result = max(results, key=lambda x: x[2])
                text = best_result[1]
                confidence = best_result[2]
                
                if confidence > 0.3:
                    # Clean text
                    cleaned = text.upper().replace(' ', '').replace('-', '')
                    cleaned = ''.join(c for c in cleaned if c.isalnum())
                    
                    if len(cleaned) >= 6:
                        logger.info(f"✅ EasyOCR: {cleaned} (conf: {confidence:.2f})")
                        return cleaned
            
            return None
            
        except Exception as e:
            logger.error(f"❌ EasyOCR extraction failed: {e}")
            return None
    
    def _extract_with_tesseract(self, image: np.ndarray) -> Optional[str]:
        """Extract text using Tesseract"""
        try:
            import pytesseract
            
            # Multiple configurations for Indian plates
            configs = [
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config).strip().upper()
                    cleaned = ''.join(c for c in text if c.isalnum())
                    
                    if len(cleaned) >= 6:
                        logger.info(f"✅ Tesseract: {cleaned}")
                        return cleaned
                        
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Tesseract extraction failed: {e}")
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
            logger.info(f"🔍 Starting optimized plate detection on image: {image.shape}")
            
            # Step 1: Detect potential plate regions
            regions = self.detect_plate_regions(image)
            
            if not regions:
                logger.info("❌ No potential plate regions found")
                return None
            
            # Step 2: Try OCR on each region
            for i, region in enumerate(regions):
                logger.info(f"🔤 Trying OCR on region {i+1}/{len(regions)}: {region}")
                
                text = self.extract_text_from_region(image, region)
                
                if text and self.validate_plate_format(text):
                    x, y, w, h = region
                    
                    result = {
                        "text": text,
                        "coordinates": (x, y, w, h),
                        "confidence": 0.9,  # High confidence for successful detection
                        "method": "optimized_detector"
                    }
                    
                    logger.info(f"🎯 Successfully detected plate: {text}")
                    return result
            
            logger.info("❌ No valid license plate text detected")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in optimized plate detection: {e}")
            return None
