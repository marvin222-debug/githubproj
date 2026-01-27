import cv2
import numpy as np
import pytesseract
import logging
import os
from typing import List, Tuple, Optional, Dict
from ultralytics import YOLO
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YOLOPlateDetector:
    """
    YOLO-based license plate detection and OCR processing
    """
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.5, model_path: str = None):
        """
        Initialize the YOLO license plate detector
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
            model_path: Path to custom YOLO model (optional)
        """
        # Set Tesseract executable path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Tesseract path set to: {tesseract_path}")
        else:
            # Try default Windows installation path
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
                logger.info(f"Using default Tesseract path: {default_path}")
            else:
                logger.warning("Tesseract path not found, OCR may not work")
            
        self.min_confidence = min_confidence
        
        # Initialize YOLO model
        try:
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                logger.info(f"Loaded custom YOLO model from {model_path}")
            else:
                # Try to load the downloaded license plate model
                plate_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'license_plate_yolo.pt')
                if os.path.exists(plate_model_path):
                    self.model = YOLO(plate_model_path)
                    logger.info(f"Loaded license plate YOLO model from {plate_model_path}")
                else:
                    # Use pre-trained YOLOv8 model optimized for small objects
                    self.model = YOLO('yolov8s.pt')  # small version for better accuracy on small objects
                    logger.info("Loaded YOLOv8s pre-trained model")
                
            # Check if CUDA is available
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {str(e)}")
            raise
            
        logger.info("YOLO license plate detector initialized")
        
    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Enhanced preprocessing specifically for OCR
        
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
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding for better text contrast
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def recognize_text(self, plate_img: np.ndarray) -> str:
        """
        Perform OCR on the license plate image with multiple strategies
        
        Args:
            plate_img: License plate image
            
        Returns:
            Extracted text (license plate number)
        """
        try:
            # Strategy 1: Enhanced preprocessing
            processed_img = self.preprocess_for_ocr(plate_img)
            
            # Try multiple OCR configurations
            configs = [
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                r'--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    # Get text with confidence
                    data = pytesseract.image_to_data(processed_img, config=config, output_type=pytesseract.Output.DICT)
                    
                    # Extract text and calculate average confidence
                    text_parts = []
                    confidences = []
                    
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 30:  # Only consider high confidence detections
                            text_parts.append(data['text'][i])
                            confidences.append(int(data['conf'][i]))
                    
                    if text_parts:
                        text = ''.join(text_parts).strip()
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        
                        # Clean text
                        text = ''.join(char for char in text if char.isalnum())
                        
                        if len(text) >= 3 and avg_confidence > best_confidence:
                            best_text = text
                            best_confidence = avg_confidence
                            
                except Exception as e:
                    logger.warning(f"OCR config failed: {config}, error: {str(e)}")
                    continue
            
            # Fallback to simple OCR if enhanced methods fail
            if not best_text:
                simple_config = r'--oem 3 --psm 7'
                best_text = pytesseract.image_to_string(processed_img, config=simple_config).strip()
                best_text = ''.join(char for char in best_text if char.isalnum())
            
            logger.info(f"OCR result: '{best_text}' (confidence: {best_confidence:.1f})")
            return best_text
            
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    def detect_plates_yolo(self, image: np.ndarray) -> List[Dict]:
        """
        Detect license plates using YOLO
        
        Args:
            image: Input image
            
        Returns:
            List of detected plates with coordinates and confidence
        """
        try:
            # Run YOLO inference with higher confidence for better results
            results = self.model(image, conf=max(0.3, self.min_confidence), device=self.device, verbose=False)
            
            detected_plates = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Convert to integer coordinates
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Filter for relevant classes (cars, trucks, buses, motorcycles)
                        # COCO class IDs: 2=car, 3=motorcycle, 5=bus, 7=truck
                        relevant_classes = [2, 3, 5, 7]
                        
                        if class_id in relevant_classes:
                            # Extract a larger region around the vehicle to find license plates
                            # License plates are typically at the front/rear of vehicles
                            h, w = image.shape[:2]
                            
                            # Expand the bounding box to include potential plate areas
                            expand_factor = 0.2
                            x1_exp = max(0, int(x1 - (x2-x1) * expand_factor))
                            y1_exp = max(0, int(y1 - (y2-y1) * expand_factor))
                            x2_exp = min(w, int(x2 + (x2-x1) * expand_factor))
                            y2_exp = min(h, int(y2 + (y2-y1) * expand_factor))
                            
                            # Extract expanded region
                            expanded_img = image[y1_exp:y2_exp, x1_exp:x2_exp]
                            
                            if expanded_img.size > 0:
                                detected_plates.append({
                                    'image': expanded_img,
                                    'coordinates': (x1_exp, y1_exp, x2_exp-x1_exp, y2_exp-y1_exp),
                                    'confidence': float(confidence),
                                    'class_id': class_id
                                })
            
            # If no vehicles detected, try to detect any rectangular objects
            if not detected_plates:
                logger.info("No vehicles detected, trying general object detection...")
                # Run with lower confidence to catch more objects
                results = self.model(image, conf=0.1, device=self.device, verbose=False)
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = box.conf[0].cpu().numpy()
                            
                            # Check if the detected object has license plate-like dimensions
                            w, h = x2-x1, y2-y1
                            aspect_ratio = w / h
                            
                            # License plates typically have aspect ratio between 2-5
                            if 1.5 < aspect_ratio < 6 and w > 50 and h > 20:
                                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                plate_img = image[y1:y2, x1:x2]
                                
                                detected_plates.append({
                                    'image': plate_img,
                                    'coordinates': (x1, y1, x2-x1, y2-y1),
                                    'confidence': float(confidence),
                                    'class_id': -1  # Unknown class
                                })
            
            return detected_plates
            
        except Exception as e:
            logger.error(f"YOLO detection error: {str(e)}")
            return []
    
    def detect_plates_fallback(self, image: np.ndarray) -> List[Dict]:
        """
        Fallback detection using traditional CV methods
        
        Args:
            image: Input image
            
        Returns:
            List of detected plates
        """
        detected_plates = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Find edges
        edges = cv2.Canny(bilateral, 30, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = float(w) / h
                
                if aspect_ratio > 1.2 and aspect_ratio < 8 and area > 500:
                    plate_img = image[y:y+h, x:x+w]
                    detected_plates.append({
                        'image': plate_img,
                        'coordinates': (x, y, w, h),
                        'confidence': 0.5,  # Default confidence for fallback
                        'class_id': 0
                    })
        
        return detected_plates
    
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main function to detect and read license plate using YOLO + fallback
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate text and coordinates or None if no plate found
        """
        logger.info(f"Starting YOLO plate detection on image of size: {image.shape}")
        
        # Try YOLO detection first
        detected_plates = self.detect_plates_yolo(image)
        logger.info(f"YOLO detected {len(detected_plates)} potential plates")
        
        # If no plates found by YOLO, try fallback method
        if not detected_plates:
            logger.info("No plates found by YOLO, trying fallback detection...")
            detected_plates = self.detect_plates_fallback(image)
            logger.info(f"Fallback detected {len(detected_plates)} potential plates")
        
        # If still no plates, try full image OCR
        if not detected_plates:
            logger.info("No plates found by detection methods, trying full image OCR")
            full_text = self.recognize_text(image)
            if len(full_text) >= 3:
                logger.info(f"Full image OCR found: {full_text}")
                return {
                    "text": full_text,
                    "confidence": 0.3,
                    "coordinates": (0, 0, image.shape[1], image.shape[0])
                }
            return None
        
        # Process all detected plate regions
        best_result = None
        max_confidence = 0
        
        for i, plate_data in enumerate(detected_plates):
            plate_img = plate_data['image']
            coords = plate_data['coordinates']
            detection_confidence = plate_data['confidence']
            
            # OCR to extract text
            plate_text = self.recognize_text(plate_img)
            logger.info(f"Plate region {i}: OCR result = '{plate_text}', coords = {coords}, detection confidence = {detection_confidence:.2f}")
            
            # Enhanced confidence estimation
            if len(plate_text) >= 3:
                # Base confidence on text length and detection confidence
                base_confidence = min(1.0, len(plate_text) / 10)
                
                # Combine detection confidence with OCR confidence
                combined_confidence = (detection_confidence + base_confidence) / 2
                
                # Bonus for common plate patterns (Indian plates: XX##XX####)
                if len(plate_text) >= 8 and plate_text[:2].isalpha() and plate_text[2:4].isdigit():
                    combined_confidence += 0.2
                
                confidence = min(1.0, combined_confidence)
                logger.info(f"Plate region {i}: combined confidence = {confidence:.2f}")
                
                if confidence > max_confidence and confidence >= (self.min_confidence * 0.3):
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
