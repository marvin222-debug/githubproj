import cv2
import numpy as np
import pytesseract
import logging
import os
from typing import List, Tuple, Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlateDetector:
    """
    License plate detection and OCR processing
    """
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.5):
        """
        Initialize the license plate detector
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
        """
        # Set Tesseract executable path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        self.min_confidence = min_confidence
        logger.info("License plate detector initialized")
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for better plate detection
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to remove noise while keeping edges sharp
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Find edges using Canny
        edges = cv2.Canny(bilateral, 30, 200)
        
        return edges
    
    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Enhanced preprocessing specifically for OCR with multiple approaches
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image optimized for text recognition
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize if too small - make it larger for better OCR
        height, width = gray.shape
        if height < 80 or width < 200:
            scale_factor = max(80/height, 200/width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Try CLAHE (Contrast Limited Adaptive Histogram Equalization) first
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(blurred)
        
        # Apply adaptive thresholding for better text contrast
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to image
        
        Args:
            image: Input image
            
        Returns:
            CLAHE enhanced image
        """
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels and convert back to BGR
            enhanced = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            return clahe.apply(image)
    
    def detect_plates_by_color(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Alternative detection method using color-based segmentation
        License plates often have white/yellow background with dark text
        
        Args:
            image: Input image
            
        Returns:
            List of potential plate regions
        """
        plates = []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define ranges for white and yellow (common plate colors)
        # White range
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # Yellow range  
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        
        # Create masks
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Combine masks
        combined_mask = cv2.bitwise_or(white_mask, yellow_mask)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = float(w) / h
            
            # Filter by size and aspect ratio
            if area > 1000 and 1.5 < aspect_ratio < 6:
                plate_img = image[y:y+h, x:x+w]
                plates.append((plate_img, (x, y, w, h)))
        
        return plates
    
    def find_plate_contours(self, preprocessed_img: np.ndarray) -> List[np.ndarray]:
        """
        Find contours that might be license plates
        
        Args:
            preprocessed_img: Preprocessed image
            
        Returns:
            List of contours
        """
        # Find contours
        contours, _ = cv2.findContours(preprocessed_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find license plate candidates
        plate_contours = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            # License plates typically have 4 corners (rectangle)
            if len(approx) == 4:
                # Check area ratio and aspect ratio to filter out non-plates
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = float(w) / h
                
                # License plates typically have aspect ratio between 2 and 5
                # Reduced area threshold for better detection
                if aspect_ratio > 1.2 and aspect_ratio < 8 and area > 500:
                    plate_contours.append(contour)
        
        return plate_contours
    
    def extract_plate_regions(self, image: np.ndarray, contours: List[np.ndarray]) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Extract regions of interest containing license plates
        
        Args:
            image: Original image
            contours: List of contours
            
        Returns:
            List of tuples with plate image and its coordinates (x, y, w, h)
        """
        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract plate region
            plate_img = image[y:y+h, x:x+w]
            plates.append((plate_img, (x, y, w, h)))
            
        return plates
    
    def recognize_text(self, plate_img: np.ndarray) -> str:
        """
        Perform OCR on the license plate image with multiple strategies
        
        Args:
            plate_img: License plate image
            
        Returns:
            Extracted text (license plate number)
        """
        try:
            # Prepare image variants to handle mirrored/rotated plates
            variants = [
                ("original", plate_img),
                ("resized", cv2.resize(plate_img, (plate_img.shape[1]*2, plate_img.shape[0]*2), interpolation=cv2.INTER_CUBIC)),
                ("clahe", self.apply_clahe(plate_img)),
                ("denoised", cv2.fastNlMeansDenoising(plate_img))
            ]
            try:
                variants.append(("flip_horizontal", cv2.flip(plate_img, 1)))
                variants.append(("rot_180", cv2.rotate(plate_img, cv2.ROTATE_180)))
            except Exception:
                pass

            # OCR configurations
            configs = [
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ]

            def is_plausible(text: str) -> bool:
                # Require mix of letters and digits and reasonable length
                text = text.upper()
                if not (4 <= len(text) <= 10):
                    return False
                has_alpha = any(ch.isalpha() for ch in text)
                has_digit = any(ch.isdigit() for ch in text)
                if not (has_alpha and has_digit):
                    return False
                return True

            best_text = ""
            best_confidence = 0.0

            for variant_name, variant_img in variants:
                processed_img = self.preprocess_for_ocr(variant_img)
                for config in configs:
                    try:
                        data = pytesseract.image_to_data(processed_img, config=config, output_type=pytesseract.Output.DICT)
                        text_parts = []
                        confidences = []
                        for i in range(len(data['text'])):
                            try:
                                conf_val = int(float(data['conf'][i]))
                            except Exception:
                                conf_val = -1
                            if conf_val > 30:  # More lenient threshold
                                text_parts.append(data['text'][i])
                                confidences.append(conf_val)
                        if text_parts:
                            text = ''.join(text_parts).strip()
                            text = ''.join(ch for ch in text if ch.isalnum()).upper()
                            avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

                            # Boost if matches typical Indian pattern: XX##XX####
                            import re
                            if re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$', text):
                                avg_conf += 10

                            if is_plausible(text) and avg_conf > best_confidence:
                                best_text = text
                                best_confidence = avg_conf
                                logger.info(f"Variant {variant_name} produced candidate '{best_text}' (avg_conf={avg_conf:.1f})")
                    except Exception as e:
                        logger.warning(f"OCR config failed ({variant_name}): {config}, error: {str(e)}")
                        continue

            # Fallback to simple OCR if enhanced methods fail
            if not best_text:
                processed_img = self.preprocess_for_ocr(plate_img)
                simple_config = r'--oem 3 --psm 7'
                text = pytesseract.image_to_string(processed_img, config=simple_config).strip()
                text = ''.join(char for char in text if char.isalnum()).upper()
                best_text = text if is_plausible(text) else ""

            logger.info(f"OCR result: '{best_text}' (confidence: {best_confidence:.1f})")
            return best_text
            
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main function to detect and read license plate using multiple strategies
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate text and coordinates or None if no plate found
        """
        logger.info(f"Starting plate detection on image of size: {image.shape}")
        
        all_plates = []
        
        # Strategy 1: Edge-based contour detection
        logger.info("Trying edge-based contour detection...")
        processed_img = self.preprocess_image(image)
        plate_contours = self.find_plate_contours(processed_img)
        logger.info(f"Found {len(plate_contours)} potential plate contours")
        
        if plate_contours:
            edge_plates = self.extract_plate_regions(image, plate_contours)
            all_plates.extend(edge_plates)
        
        # Strategy 2: Color-based detection
        logger.info("Trying color-based detection...")
        color_plates = self.detect_plates_by_color(image)
        logger.info(f"Found {len(color_plates)} potential plates by color")
        all_plates.extend(color_plates)
        
        # Strategy 3: Full image OCR as fallback
        if not all_plates:
            logger.info("No plates found by detection methods, trying full image OCR")
            full_text = self.recognize_text(image)
            if len(full_text) >= 3:
                logger.info(f"Full image OCR found: {full_text}")
                return {
                    "text": full_text,
                    "confidence": 0.3,  # Lower confidence for full image
                    "coordinates": (0, 0, image.shape[1], image.shape[0])
                }
            return None
        
        # Process all detected plate regions
        best_result = None
        max_confidence = 0
        
        for i, (plate_img, coords) in enumerate(all_plates):
            # OCR to extract text
            plate_text = self.recognize_text(plate_img)
            logger.info(f"Plate region {i}: OCR result = '{plate_text}', coords = {coords}")
            
            # Enhanced confidence estimation
            if len(plate_text) >= 3:
                # Base confidence on text length and character validity
                base_confidence = min(1.0, len(plate_text) / 10)
                
                # Bonus for common plate patterns (Indian plates: XX##XX####)
                if len(plate_text) >= 8 and plate_text[:2].isalpha() and plate_text[2:4].isdigit():
                    base_confidence += 0.2
                
                confidence = min(1.0, base_confidence)
                logger.info(f"Plate region {i}: confidence = {confidence:.2f}, min_confidence = {self.min_confidence * 0.3:.2f}")
                
                if confidence > max_confidence and confidence >= (self.min_confidence * 0.3):  # Even more lenient
                    max_confidence = confidence
                    best_result = {
                        "text": plate_text,
                        "confidence": confidence,
                        "coordinates": coords
                    }
                    logger.info(f"New best result: {plate_text} with confidence {confidence:.2f}")
        
        if best_result:
            logger.info(f"License plate detected: {best_result['text']} (Confidence: {best_result['confidence']:.2f})")
            return best_result
        else:
            logger.info("No valid license plate text detected")
            return None 