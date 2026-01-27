#!/usr/bin/env python3
"""
Simple but Effective License Plate Detector
Uses basic computer vision techniques for reliable plate detection
"""

import cv2
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SimplePlateDetector:
    """Simple but effective license plate detector"""
    
    def __init__(self, min_confidence: float = 0.3):
        self.min_confidence = min_confidence
        
        # License plate validation patterns - Indian format
        # Format: LLDDLLDDDD (e.g., DL07KL9988, KA01AB1234)
        self.plate_patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',      # DL07KL9988, KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$',   # KA01A1234 or KA01AB1234
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$', # KA1A1234 or KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{3,4}$',   # Allow 3-4 digits at end
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{2}[0-9]{3,4}$', # More flexible
        ]
        
        logger.info("🚀 Simple Plate Detector initialized successfully")
    
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect license plates using traditional computer vision
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of (x1, y1, x2, y2, confidence) tuples
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            plates = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio and size (license plates are typically wider than tall)
                aspect_ratio = w / h
                area = w * h
                image_area = image.shape[0] * image.shape[1]
                
                # More lenient criteria for license plates - Indian plates can vary
                if (1.5 <= aspect_ratio <= 8.0 and  # More flexible aspect ratio
                    w > 60 and h > 15 and           # Smaller minimum size
                    w < image.shape[1] * 0.95 and    # Not too wide
                    h < image.shape[0] * 0.5 and     # Not too tall
                    area > 900 and                  # Smaller minimum area (30x30)
                    area < image_area * 0.4):        # Maximum 40% of image
                    
                    # Calculate confidence based on aspect ratio and size
                    ideal_ratio = 4.0  # Ideal license plate ratio
                    ratio_score = 1.0 - abs(aspect_ratio - ideal_ratio) / ideal_ratio
                    size_score = min(1.0, area / 8000)  # Normalize area score
                    confidence = (ratio_score * 0.6 + size_score * 0.4) * 0.7  # Lower base confidence
                    
                    if confidence > self.min_confidence:
                        plates.append((x, y, x + w, y + h, confidence))
            
            # Sort by confidence
            plates.sort(key=lambda x: x[4], reverse=True)
            
            logger.info(f"Simple CV detected {len(plates)} potential license plate regions")
            return plates
            
        except Exception as e:
            logger.error(f"Error in plate detection: {e}")
            return []
    
    def extract_plate_region(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> List[np.ndarray]:
        """
        Extract and preprocess license plate region into multiple variants
        
        Args:
            image: Input image
            x1, y1, x2, y2: Bounding box coordinates
            
        Returns:
            List of preprocessed plate region variants
        """
        # Extract region
        plate_region = image[y1:y2, x1:x2]
        
        if plate_region.size == 0:
            return []
        
        # Preprocess the image for better OCR (returns multiple variants)
        plate_variants = self.preprocess_for_ocr(plate_region)
        
        return plate_variants
    
    def preprocess_for_ocr(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Enhanced preprocessing creating multiple variants for better OCR results
        
        Args:
            image: Input image
            
        Returns:
            List of preprocessed image variants
        """
        variants = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize image if too small (minimum 300px width for better OCR)
        if gray.shape[1] < 300:
            scale_factor = 300 / gray.shape[1]
            new_width = int(gray.shape[1] * scale_factor)
            new_height = int(gray.shape[0] * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Variant 1: CLAHE + Adaptive Threshold
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        thresh1 = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        variants.append(thresh1)
        
        # Variant 2: Bilateral Filter + Otsu
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh2 = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(thresh2)
        
        # Variant 3: Simple threshold with different values
        _, thresh3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        variants.append(thresh3)
        
        # Variant 4: Inverted threshold (for dark text on light background)
        _, thresh4 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        variants.append(thresh4)
        
        # Variant 5: Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        variants.append(morph)
        
        # Variant 6: Original grayscale (sometimes works better)
        variants.append(gray)
        
        return variants
    
    def read_plate_text(self, plate_images: List[np.ndarray]) -> Optional[str]:
        """
        Read license plate text using OCR on multiple preprocessed variants
        
        Args:
            plate_images: List of preprocessed license plate image variants
            
        Returns:
            Detected license plate text or None
        """
        try:
            best_result = None
            best_confidence = 0
            
            # Try OCR on each preprocessed variant
            for i, plate_image in enumerate(plate_images):
                logger.info(f"🔍 Trying OCR on variant {i+1}/{len(plate_images)}")
                
                # Analyze this variant
                plate_text = self.analyze_plate_pattern(plate_image)
                
                if plate_text and self.validate_plate_format(plate_text):
                    # This variant produced a valid result
                    confidence = 80 + (i * 5)  # Prefer earlier variants slightly
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_result = plate_text
                        logger.info(f"✅ Variant {i+1} detected valid plate: {plate_text}")
            
            if best_result:
                logger.info(f"🎯 Final result: {best_result} (confidence: {best_confidence})")
                return best_result
            else:
                logger.warning("❌ No valid plate text detected from any variant")
                return None
                
        except Exception as e:
            logger.error(f"Error reading plate text: {e}")
            return None
    
    def analyze_plate_pattern(self, plate_image: np.ndarray) -> Optional[str]:
        """
        Analyze plate image using multiple OCR strategies for better recognition
        """
        try:
            import pytesseract
            
            # Multiple OCR configurations to try
            configs = [
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single word
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single text line
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single uniform block
                '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Raw line
                '--psm 8',  # Single word without character restriction
                '--psm 7',  # Single text line without character restriction
            ]
            
            best_result = None
            best_confidence = 0
            
            for config in configs:
                try:
                    # Try to read text with current config
                    if 'tessedit_char_whitelist' in config:
                        text = pytesseract.image_to_string(plate_image, config=config).strip().upper()
                        # Get confidence data
                        data = pytesseract.image_to_data(plate_image, config=config, output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    else:
                        text = pytesseract.image_to_string(plate_image, config=config).strip().upper()
                        avg_confidence = 50  # Default confidence for configs without confidence data
                    
                    # Try to extract plate pattern from text (handles spaces)
                    import re
                    plate_match = re.search(r'([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{3,4})', text.upper())
                    if plate_match:
                        cleaned_text = re.sub(r'\s+', '', plate_match.group(1))
                        logger.info(f"Extracted plate pattern: {cleaned_text}")
                    else:
                        # Clean the text - remove spaces and special characters, normalize
                        # Handle formats like "DL 07 KL 9988" -> "DL07KL9988"
                        cleaned_text = ''.join(c for c in text if c.isalnum()).upper()
                    
                    # Additional normalization: handle common OCR errors
                    # But be careful - only fix obvious errors
                    if len(cleaned_text) >= 8:
                        # Indian plates: LLDDLLDDDD format
                        # First 2 should be letters (state code)
                        if cleaned_text[0].isdigit() and cleaned_text[0] in '01':
                            cleaned_text = 'O' + cleaned_text[1:] if cleaned_text[0] == '0' else 'I' + cleaned_text[1:]
                        if len(cleaned_text) > 1 and cleaned_text[1].isdigit() and cleaned_text[1] in '01':
                            cleaned_text = cleaned_text[0] + ('O' if cleaned_text[1] == '0' else 'I') + cleaned_text[2:]
                    
                    # Validate the result
                    if (len(cleaned_text) >= 6 and len(cleaned_text) <= 12 and
                        any(c.isalpha() for c in cleaned_text) and 
                        any(c.isdigit() for c in cleaned_text)):
                        
                        if avg_confidence > best_confidence:
                            best_confidence = avg_confidence
                            best_result = cleaned_text
                            logger.info(f"OCR config '{config[:20]}...' detected: {cleaned_text} (confidence: {avg_confidence:.1f})")
                
                except Exception as config_error:
                    logger.debug(f"OCR config failed: {config_error}")
                    continue
            
            if best_result and best_confidence > 20:  # Even lower threshold for acceptance
                logger.info(f"✅ Best OCR result: {best_result} (confidence: {best_confidence:.1f})")
                return best_result
            elif best_result:  # Return even if confidence is low, let validation decide
                logger.info(f"⚠️ Low confidence OCR result: {best_result} (confidence: {best_confidence:.1f})")
                return best_result
            else:
                logger.info(f"❌ OCR failed to detect valid text (best: {best_result}, conf: {best_confidence:.1f})")
                return None
                
        except Exception as e:
            logger.error(f"Error in OCR analysis: {e}")
            return None
    
    def validate_plate_format(self, plate_text: str) -> bool:
        """
        Validate if the detected text matches Indian license plate format
        
        Args:
            plate_text: Detected text
            
        Returns:
            True if valid format, False otherwise
        """
        if not plate_text or len(plate_text) < 6:
            return False
        
        # Remove spaces and normalize
        plate_text = plate_text.replace(" ", "").upper()
        
        # Check against known patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, plate_text):
                return True
        
        # More lenient check: at least 2 letters, some digits, total length 8-12
        if len(plate_text) >= 8 and len(plate_text) <= 12:
            letter_count = sum(1 for c in plate_text if c.isalpha())
            digit_count = sum(1 for c in plate_text if c.isdigit())
            if letter_count >= 2 and digit_count >= 3:
                logger.info(f"✅ Lenient validation passed for: {plate_text}")
                return True
        
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
            logger.info(f"Starting simple plate detection on image of size: {image.shape}")
            
            # Step 1: Detect license plates
            plates = self.detect_plates(image)
            
            if not plates:
                logger.info("No license plates detected by region detection, trying full image OCR...")
                # Fallback: Try OCR on entire image
                try:
                    import pytesseract
                    from src.config.config import TESSERACT_PATH
                    if TESSERACT_PATH:
                        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
                    
                    # Try OCR on full image
                    full_text = pytesseract.image_to_string(image, config='--psm 7').strip().upper()
                    full_text_clean = ''.join(c for c in full_text if c.isalnum())
                    
                    # Look for plate pattern
                    import re
                    plate_match = re.search(r'([A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4})', full_text_clean)
                    if plate_match:
                        plate_text = plate_match.group(1)
                        logger.info(f"✅ Found plate via full image OCR: {plate_text}")
                        return {
                            "text": plate_text,
                            "coordinates": (0, 0, image.shape[1], image.shape[0]),
                            "confidence": 0.6,
                            "method": "full_image_ocr"
                        }
                    else:
                        logger.info(f"Full image OCR found: {full_text_clean[:30]}...")
                except Exception as e:
                    logger.warning(f"Full image OCR fallback failed: {e}")
                
                logger.info("No license plates detected")
                return None
            
            # Step 2: Process each detected plate
            for i, (x1, y1, x2, y2, confidence) in enumerate(plates):
                logger.info(f"Processing plate region {i}: coords = ({x1}, {y1}, {x2-x1}, {y2-y1})")
                
                # Extract plate region (returns multiple preprocessed variants)
                plate_variants = self.extract_plate_region(image, x1, y1, x2, y2)
                
                if not plate_variants:
                    continue
                
                # Step 3: Read text from all variants
                plate_text = self.read_plate_text(plate_variants)
                
                if plate_text and len(plate_text) >= 6:
                    # Normalize the text (remove spaces, uppercase)
                    plate_text = plate_text.replace(" ", "").upper()
                    
                    # Additional validation: check if the detected text makes sense
                    if self.validate_plate_format(plate_text):
                        logger.info(f"✅ Successfully detected valid plate: {plate_text}")
                        return {
                            "text": plate_text,
                            "coordinates": (x1, y1, x2-x1, y2-y1),
                            "confidence": confidence,
                            "method": "simple_cv"
                        }
                    else:
                        logger.info(f"❌ Detected text doesn't match plate format: {plate_text}")
                        # Even if validation fails, return it if it looks reasonable
                        if len(plate_text) >= 8 and len(plate_text) <= 12:
                            letter_count = sum(1 for c in plate_text if c.isalpha())
                            digit_count = sum(1 for c in plate_text if c.isdigit())
                            if letter_count >= 2 and digit_count >= 3:
                                logger.info(f"⚠️ Using lenient validation for: {plate_text}")
                                return {
                                    "text": plate_text,
                                    "coordinates": (x1, y1, x2-x1, y2-y1),
                                    "confidence": confidence * 0.8,  # Lower confidence
                                    "method": "simple_cv"
                                }
                else:
                    logger.info(f"❌ No valid text detected in plate region {i+1}")
            
            # Last resort: Try full image OCR if no plates found in regions
            logger.info("No valid license plates found in detected regions, trying full image OCR...")
            try:
                import pytesseract
                from src.config.config import TESSERACT_PATH
                if TESSERACT_PATH:
                    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
                
                # Try multiple OCR configs on full image
                ocr_configs = [
                    '--psm 7',  # Single text line
                    '--psm 8',  # Single word
                    '--psm 6',  # Single uniform block
                    '--psm 13', # Raw line
                ]
                
                for config in ocr_configs:
                    try:
                        full_text = pytesseract.image_to_string(image, config=config).strip().upper()
                        full_text_clean = ''.join(c for c in full_text if c.isalnum())
                        
                        # Look for plate pattern
                        import re
                        plate_match = re.search(r'([A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4})', full_text_clean)
                        if plate_match:
                            plate_text = plate_match.group(1)
                            logger.info(f"✅ Found plate via full image OCR (config {config}): {plate_text}")
                            return {
                                "text": plate_text,
                                "coordinates": (0, 0, image.shape[1], image.shape[0]),
                                "confidence": 0.5,
                                "method": "full_image_ocr"
                            }
                    except Exception as e:
                        logger.debug(f"OCR config {config} failed: {e}")
                        continue
                
                logger.info(f"Full image OCR tried but no plate pattern found")
            except Exception as e:
                logger.warning(f"Full image OCR fallback failed: {e}")
            
            logger.info("No valid license plates found")
            return None
            
        except Exception as e:
            logger.error(f"Error in plate detection: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

