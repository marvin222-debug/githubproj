import cv2
import numpy as np
import pytesseract
import easyocr
import logging
import re
import os
from typing import List, Tuple, Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPlateDetector:
    """
    Enhanced license plate detection and OCR processing with EasyOCR and strict validation
    """
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.5):
        """
        Initialize the enhanced license plate detector
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
        """
        # Set Tesseract executable path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        self.min_confidence = min_confidence
        
        # Initialize EasyOCR reader
        try:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")
            self.easyocr_reader = None
            
        logger.info("Enhanced license plate detector initialized")
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # Standard: KA01AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',   # Standard: KA01AB1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # Old format: KA1AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$',   # Short: KA01A1234
        ]
        
    def validate_plate_format(self, text: str) -> bool:
        """
        Validate if text matches Indian license plate format
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid Indian plate format
        """
        if not text or len(text) < 6 or len(text) > 12:
            return False
            
        text = text.upper().replace(' ', '').replace('-', '')
        
        # Check against known patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
                
        # Additional checks
        if len(text) >= 8:
            # Must have at least 2 letters at start (state code)
            if not re.match(r'^[A-Z]{2}', text):
                return False
            # Must have digits
            if not re.search(r'\d', text):
                return False
            # Must have letters and digits mixed
            has_alpha = any(c.isalpha() for c in text)
            has_digit = any(c.isdigit() for c in text)
            if not (has_alpha and has_digit):
                return False
                
        return True
        
    def preprocess_for_ocr(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Create multiple preprocessed variants for better OCR
        
        Args:
            image: Input image
            
        Returns:
            List of preprocessed images
        """
        variants = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize if too small
        height, width = gray.shape
        if height < 100 or width < 300:
            scale_factor = max(100/height, 300/width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Variant 1: Original
        variants.append(gray)
        
        # Variant 2: CLAHE enhanced
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        variants.append(enhanced)
        
        # Variant 3: Gaussian blur + threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(thresh)
        
        # Variant 4: Adaptive threshold
        adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        variants.append(adaptive)
        
        # Variant 5: Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morphed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
        variants.append(morphed)
        
        return variants
        
    def extract_text_easyocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Extract text using EasyOCR
        
        Args:
            image: Input image
            
        Returns:
            List of (text, confidence) tuples
        """
        if not self.easyocr_reader:
            return []
            
        try:
            results = self.easyocr_reader.readtext(image)
            text_results = []
            
            for (bbox, text, confidence) in results:
                # Clean text
                clean_text = re.sub(r'[^A-Za-z0-9]', '', text.upper())
                if len(clean_text) >= 4:  # Minimum length for plate
                    text_results.append((clean_text, confidence))
                    
            return text_results
        except Exception as e:
            logger.warning(f"EasyOCR failed: {e}")
            return []
            
    def extract_text_tesseract(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Extract text using Tesseract with multiple configurations
        
        Args:
            image: Input image
            
        Returns:
            List of (text, confidence) tuples
        """
        configs = [
            r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            r'--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            r'--oem 3 --psm 7',  # No whitelist
            r'--oem 3 --psm 8',  # No whitelist
        ]
        
        text_results = []
        
        for config in configs:
            try:
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                
                text_parts = []
                confidences = []
                
                for i in range(len(data['text'])):
                    try:
                        conf_val = int(float(data['conf'][i]))
                    except Exception:
                        conf_val = -1
                        
                    if conf_val > 20:  # Lower threshold
                        text_parts.append(data['text'][i])
                        confidences.append(conf_val)
                        
                if text_parts:
                    text = ''.join(text_parts).strip()
                    text = re.sub(r'[^A-Za-z0-9]', '', text.upper())
                    if len(text) >= 4:
                        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                        text_results.append((text, avg_conf))
                        
            except Exception as e:
                logger.warning(f"Tesseract config failed: {config}, error: {e}")
                continue
                
        return text_results
        
    def detect_plate_regions(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Detect potential license plate regions in image
        
        Args:
            image: Input image
            
        Returns:
            List of (plate_image, coordinates) tuples
        """
        plate_regions = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size
            aspect_ratio = w / h
            area = w * h
            
            # License plates typically have aspect ratio between 2:1 and 5:1
            if (2.0 <= aspect_ratio <= 5.0 and 
                area > 2000 and 
                w > 100 and h > 30):
                
                # Extract region
                plate_region = image[y:y+h, x:x+w]
                plate_regions.append((plate_region, (x, y, w, h)))
                
        return plate_regions
        
    def read_plate_text(self, plate_img: np.ndarray) -> str:
        """
        Read text from license plate image using multiple methods
        
        Args:
            plate_img: License plate image
            
        Returns:
            Detected plate text
        """
        if plate_img is None or plate_img.size == 0:
            return ""
            
        # Get preprocessed variants
        variants = self.preprocess_for_ocr(plate_img)
        
        all_candidates = []
        
        # Try EasyOCR on each variant
        for i, variant in enumerate(variants):
            easyocr_results = self.extract_text_easyocr(variant)
            for text, conf in easyocr_results:
                if self.validate_plate_format(text):
                    all_candidates.append((text, conf, f"easyocr_variant_{i}"))
                    
        # Try Tesseract on each variant
        for i, variant in enumerate(variants):
            tesseract_results = self.extract_text_tesseract(variant)
            for text, conf in tesseract_results:
                if self.validate_plate_format(text):
                    all_candidates.append((text, conf, f"tesseract_variant_{i}"))
                    
        # Sort by confidence and return best valid result
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for text, conf, method in all_candidates:
            logger.info(f"Valid plate candidate: '{text}' (confidence: {conf:.1f}, method: {method})")
            return text
            
        # If no valid candidates, try without strict validation
        logger.warning("No valid plate format found, trying relaxed validation...")
        
        for variant in variants:
            # Try EasyOCR
            if self.easyocr_reader:
                try:
                    results = self.easyocr_reader.readtext(variant)
                    for (bbox, text, confidence) in results:
                        clean_text = re.sub(r'[^A-Za-z0-9]', '', text.upper())
                        if len(clean_text) >= 6 and confidence > 0.3:
                            logger.info(f"Relaxed candidate: '{clean_text}' (confidence: {confidence:.1f})")
                            return clean_text
                except Exception:
                    continue
                    
        return ""
        
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main function to detect and read license plate
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate text and coordinates or None if no plate found
        """
        logger.info(f"Starting enhanced plate detection on image of size: {image.shape}")
        
        # First try to detect plate regions
        plate_regions = self.detect_plate_regions(image)
        logger.info(f"Found {len(plate_regions)} potential plate regions")
        
        # Try OCR on detected regions
        for i, (plate_img, coords) in enumerate(plate_regions):
            logger.info(f"Processing plate region {i}: coords = {coords}")
            text = self.read_plate_text(plate_img)
            
            if text and self.validate_plate_format(text):
                logger.info(f"Successfully detected plate: {text}")
                return {
                    "plate_text": text,
                    "coordinates": coords,
                    "confidence": 0.8  # High confidence for validated plates
                }
                
        # If no regions found or no valid text, try full image OCR
        logger.info("No valid plates found in regions, trying full image OCR...")
        text = self.read_plate_text(image)
        
        if text and self.validate_plate_format(text):
            logger.info(f"Full image OCR found valid plate: {text}")
            return {
                "plate_text": text,
                "coordinates": (0, 0, image.shape[1], image.shape[0]),
                "confidence": 0.6  # Lower confidence for full image
            }
            
        logger.info("No valid license plate detected")
        return None
