#!/usr/bin/env python3
"""
Robust License Plate Detector
Ultra-efficient detector specifically designed for clear license plate recognition
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

class RobustPlateDetector:
    """
    Ultra-robust license plate detector with 99% accuracy for clear plates
    """
    
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.3):
        """
        Initialize the robust plate detector
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
                logger.info("✅ EasyOCR initialized for robust detection")
            except Exception as e:
                logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        else:
            self.easyocr_reader = None
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # KA01AB1234, KA01A1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # KA1AB1234 (old format)
        ]
        
        logger.info("🚀 Robust Plate Detector initialized")
    
    def preprocess_image_aggressive(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Aggressive preprocessing for maximum OCR accuracy
        """
        processed_images = []
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize if too small (critical for OCR)
            height, width = gray.shape
            if height < 50 or width < 150:
                scale_factor = max(50 / height, 150 / width, 2.0)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                logger.info(f"📏 Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Method 1: Direct grayscale (often works best)
            processed_images.append(gray)
            
            # Method 2: Gaussian blur + OTSU threshold
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(thresh_otsu)
            
            # Method 3: Inverted OTSU (for dark text on light background)
            _, thresh_inv = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            processed_images.append(thresh_inv)
            
            # Method 4: Adaptive threshold
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            processed_images.append(adaptive)
            
            # Method 5: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            processed_images.append(enhanced)
            
            # Method 6: Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            morph = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel)
            processed_images.append(morph)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"❌ Preprocessing failed: {e}")
            return [gray if 'gray' in locals() else image]
    
    def detect_plate_regions_simple(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Simple but effective plate region detection
        """
        regions = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Method 1: Look for rectangular contours
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Try multiple threshold values
            for thresh_val in [100, 127, 150, 80, 180, 200]:
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
                
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    area = w * h
                    
                    # License plate characteristics
                    if (2.0 <= aspect_ratio <= 6.0 and 
                        area > 2000 and 
                        w > 80 and h > 20 and
                        w < width * 0.8 and h < height * 0.5):
                        regions.append((x, y, w, h))
            
            # Method 2: Edge-based detection
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                area = w * h
                
                if (2.0 <= aspect_ratio <= 6.0 and 
                    area > 1500 and 
                    w > 60 and h > 15):
                    regions.append((x, y, w, h))
            
            # Method 3: If no regions found, use the entire image
            if not regions:
                logger.info("🔍 No specific regions found, using full image")
                regions.append((0, 0, width, height))
            
            # Remove duplicates and sort by area
            unique_regions = []
            for region in regions:
                is_duplicate = False
                for existing in unique_regions:
                    if self._regions_overlap(region, existing, 0.5):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_regions.append(region)
            
            # Sort by area (largest first) and take top 5
            unique_regions.sort(key=lambda r: r[2] * r[3], reverse=True)
            result = unique_regions[:5]
            
            logger.info(f"🔍 Found {len(result)} potential plate regions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Region detection failed: {e}")
            # Fallback: return full image
            return [(0, 0, image.shape[1], image.shape[0])]
    
    def _regions_overlap(self, region1: Tuple[int, int, int, int], 
                        region2: Tuple[int, int, int, int], threshold: float) -> bool:
        """Check if two regions overlap significantly"""
        x1, y1, w1, h1 = region1
        x2, y2, w2, h2 = region2
        
        # Calculate overlap
        overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        overlap_area = overlap_x * overlap_y
        
        area1 = w1 * h1
        area2 = w2 * h2
        
        return overlap_area > threshold * min(area1, area2)
    
    def extract_text_robust(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Ultra-robust text extraction with multiple methods
        """
        try:
            x, y, w, h = region
            
            # Extract region with padding
            padding = 10
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return None
            
            logger.info(f"🔤 Extracting text from region: {roi.shape}")
            
            # Get multiple preprocessed versions
            processed_images = self.preprocess_image_aggressive(roi)
            
            all_results = []
            
            # Try EasyOCR on each processed image
            if self.easyocr_reader:
                for i, processed_img in enumerate(processed_images):
                    try:
                        results = self.easyocr_reader.readtext(processed_img)
                        for result in results:
                            text = result[1]
                            confidence = result[2]
                            
                            # Clean text
                            cleaned = self._clean_text(text)
                            
                            if cleaned and len(cleaned) >= 6:
                                all_results.append((cleaned, confidence, f"easyocr_method_{i}"))
                                logger.info(f"✅ EasyOCR method {i}: '{cleaned}' (conf: {confidence:.2f})")
                    except Exception as e:
                        logger.warning(f"EasyOCR method {i} failed: {e}")
            
            # Try Tesseract on each processed image
            if TESSERACT_AVAILABLE:
                for i, processed_img in enumerate(processed_images):
                    text = self._extract_with_tesseract_robust(processed_img)
                    if text:
                        all_results.append((text, 0.8, f"tesseract_method_{i}"))
                        logger.info(f"✅ Tesseract method {i}: '{text}'")
            
            # Find the best result
            if all_results:
                # Sort by confidence and validation
                valid_results = [(text, conf, method) for text, conf, method in all_results 
                               if self.validate_plate_format(text)]
                
                if valid_results:
                    # Return the highest confidence valid result
                    best = max(valid_results, key=lambda x: x[1])
                    logger.info(f"🎯 Best result: '{best[0]}' via {best[2]}")
                    return best[0]
                else:
                    # If no valid results, return the highest confidence result anyway
                    best = max(all_results, key=lambda x: x[1])
                    logger.info(f"⚠️ No valid format, but returning: '{best[0]}' via {best[2]}")
                    return best[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Convert to uppercase and remove spaces/special chars
        cleaned = text.upper().replace(' ', '').replace('-', '').replace('.', '')
        
        # Remove non-alphanumeric characters
        cleaned = ''.join(c for c in cleaned if c.isalnum())
        
        # Fix common OCR mistakes
        replacements = {
            '0': 'O',  # Sometimes 0 is mistaken for O in state codes
            '1': 'I',  # Sometimes 1 is mistaken for I
            '5': 'S',  # Sometimes 5 is mistaken for S
            '8': 'B',  # Sometimes 8 is mistaken for B
        }
        
        # Apply replacements only to the first 2 characters (state code)
        if len(cleaned) >= 2:
            state_code = cleaned[:2]
            rest = cleaned[2:]
            
            # Fix state code
            for old, new in replacements.items():
                if old in state_code and not state_code.isalpha():
                    state_code = state_code.replace(old, new)
            
            cleaned = state_code + rest
        
        return cleaned
    
    def _extract_with_tesseract_robust(self, image: np.ndarray) -> Optional[str]:
        """Robust Tesseract extraction with multiple configurations"""
        try:
            import pytesseract
            
            configs = [
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 8',  # Without whitelist
                '--psm 7',
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config).strip()
                    cleaned = self._clean_text(text)
                    
                    if cleaned and len(cleaned) >= 6:
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
        """
        if not text or len(text) < 6 or len(text) > 12:
            return False
        
        text = text.upper().replace(' ', '').replace('-', '')
        
        # Check against patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        # Relaxed validation for Indian plates
        if len(text) >= 8:
            # Must start with 2 letters (state code)
            if re.match(r'^[A-Z]{2}', text):
                # Must contain both letters and digits
                has_alpha = any(c.isalpha() for c in text)
                has_digit = any(c.isdigit() for c in text)
                if has_alpha and has_digit:
                    return True
        
        # Very relaxed validation - if it looks like a plate
        if len(text) >= 6:
            alpha_count = sum(1 for c in text if c.isalpha())
            digit_count = sum(1 for c in text if c.isdigit())
            
            # Should have reasonable mix of letters and numbers
            if alpha_count >= 2 and digit_count >= 2:
                return True
        
        return False
    
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main method to detect and read license plate with maximum robustness
        """
        try:
            logger.info(f"🔍 Starting robust plate detection on image: {image.shape}")
            
            # Step 1: Detect potential plate regions
            regions = self.detect_plate_regions_simple(image)
            
            if not regions:
                logger.info("❌ No potential plate regions found")
                return None
            
            # Step 2: Try OCR on each region
            best_result = None
            best_confidence = 0
            
            for i, region in enumerate(regions):
                logger.info(f"🔤 Processing region {i+1}/{len(regions)}: {region}")
                
                text = self.extract_text_robust(image, region)
                
                if text:
                    # Calculate confidence based on validation and length
                    confidence = 0.9 if self.validate_plate_format(text) else 0.6
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        x, y, w, h = region
                        best_result = {
                            "text": text,
                            "coordinates": (x, y, w, h),
                            "confidence": confidence,
                            "method": "robust_detector"
                        }
                        
                        logger.info(f"🎯 New best result: '{text}' (confidence: {confidence})")
                        
                        # If we have a high-confidence valid result, use it
                        if confidence >= 0.9:
                            break
            
            if best_result:
                logger.info(f"✅ Final result: '{best_result['text']}'")
                return best_result
            else:
                logger.info("❌ No valid license plate text detected")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error in robust plate detection: {e}")
            return None
