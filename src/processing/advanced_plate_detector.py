#!/usr/bin/env python3
"""
Advanced License Plate Detector
Combines YOLO object detection, enhanced OCR, and multiple preprocessing techniques
for highly accurate license plate recognition
"""

import cv2
import numpy as np
import pytesseract
import logging
import re
import os
from typing import List, Tuple, Optional, Dict, Union
import torch
from ultralytics import YOLO

# Try to import EasyOCR (fallback if not available)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
except Exception as e:
    # Handle any other import errors (like dependency conflicts)
    print(f"EasyOCR import failed: {e}")
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedPlateDetector:
    """
    Advanced license plate detector combining multiple detection and OCR methods
    """
    
    def __init__(self, tesseract_path: str = None, min_confidence: float = 0.3):
        """
        Initialize the advanced license plate detector
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            min_confidence: Minimum confidence threshold for detections
        """
        self.min_confidence = min_confidence
        
        # Set up Tesseract
        self._setup_tesseract(tesseract_path)
        
        # Initialize YOLO model
        self._setup_yolo()
        
        # Initialize EasyOCR if available
        self._setup_easyocr()
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$',  # Standard: KA01AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',   # Standard: KA01AB1234
            r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$',  # Old format: KA1AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$',   # Short: KA01A1234
            r'^[A-Z]{2}\d{2}[A-Z]{3}\d{3}$',   # New format: KA01ABC123
        ]
        
        logger.info("🚀 Advanced Plate Detector initialized successfully")
    
    def _setup_tesseract(self, tesseract_path: str = None):
        """Setup Tesseract OCR"""
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"✅ Tesseract path set to: {tesseract_path}")
        else:
            # Try default Windows installation path
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
                logger.info(f"✅ Using default Tesseract path: {default_path}")
            else:
                logger.warning("⚠️ Tesseract path not found, OCR may not work optimally")
    
    def _setup_yolo(self):
        """Setup YOLO model for object detection"""
        try:
            # Check if we have a custom license plate model
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            custom_model_path = os.path.join(models_dir, 'license_plate_yolo.pt')
            
            if os.path.exists(custom_model_path):
                self.yolo_model = YOLO(custom_model_path)
                logger.info("✅ Loaded custom license plate YOLO model")
            else:
                # Use YOLOv8n for general object detection (cars, motorcycles)
                yolo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'yolov8n.pt')
                if os.path.exists(yolo_path):
                    self.yolo_model = YOLO(yolo_path)
                    logger.info("✅ Loaded YOLOv8n model from local file")
                else:
                    self.yolo_model = YOLO('yolov8n.pt')
                    logger.info("✅ Loaded YOLOv8n model (will download if needed)")
            
            # Set device
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"🔧 Using device: {self.device}")
            
        except Exception as e:
            logger.warning(f"⚠️ YOLO initialization failed: {e}")
            self.yolo_model = None
    
    def _setup_easyocr(self):
        """Setup EasyOCR if available"""
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
                logger.info("✅ EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        else:
            logger.info("📝 EasyOCR not available, using Tesseract only")
            self.easyocr_reader = None
    
    def detect_vehicles_yolo(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect vehicles using YOLO to focus plate detection
        
        Args:
            image: Input image
            
        Returns:
            List of vehicle bounding boxes (x1, y1, x2, y2, confidence)
        """
        if self.yolo_model is None:
            return []
        
        try:
            # Run YOLO detection
            results = self.yolo_model(image, conf=0.3, verbose=False)
            
            vehicles = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class ID and confidence
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        # Check if it's a vehicle (car=2, motorcycle=3, bus=5, truck=7)
                        if cls_id in [2, 3, 5, 7] and conf > 0.3:
                            # Get coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            vehicles.append((x1, y1, x2, y2, conf))
            
            logger.info(f"🚗 YOLO detected {len(vehicles)} vehicles")
            return vehicles
            
        except Exception as e:
            logger.error(f"❌ YOLO vehicle detection failed: {e}")
            return []
    
    def detect_plates_traditional(self, image: np.ndarray, roi: Tuple[int, int, int, int] = None) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect license plates using traditional computer vision within ROI
        
        Args:
            image: Input image
            roi: Region of interest (x1, y1, x2, y2) or None for full image
            
        Returns:
            List of plate bounding boxes (x1, y1, x2, y2, confidence)
        """
        try:
            # Extract ROI if specified
            if roi:
                x1, y1, x2, y2 = roi
                roi_image = image[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1
            else:
                roi_image = image
                offset_x, offset_y = 0, 0
            
            # Convert to grayscale
            gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while preserving edges
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Find edges
            edges = cv2.Canny(filtered, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            plates = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size and aspect ratio
                aspect_ratio = w / h if h > 0 else 0
                area = w * h
                
                # License plate criteria
                if (2.0 <= aspect_ratio <= 6.0 and 
                    w > 80 and h > 20 and 
                    area > 2000 and area < 50000):
                    
                    # Calculate confidence based on aspect ratio and size
                    ideal_ratio = 4.5  # Typical license plate ratio
                    ratio_score = 1.0 - abs(aspect_ratio - ideal_ratio) / ideal_ratio
                    size_score = min(1.0, area / 10000)
                    confidence = (ratio_score * 0.6 + size_score * 0.4) * 0.8
                    
                    if confidence > self.min_confidence:
                        # Adjust coordinates back to original image
                        plates.append((
                            x + offset_x, y + offset_y, 
                            x + w + offset_x, y + h + offset_y, 
                            confidence
                        ))
            
            # Sort by confidence and remove overlaps
            plates.sort(key=lambda x: x[4], reverse=True)
            plates = self._remove_overlapping_boxes(plates)
            
            logger.info(f"🔍 Traditional CV detected {len(plates)} potential plates")
            return plates
            
        except Exception as e:
            logger.error(f"❌ Traditional plate detection failed: {e}")
            return []
    
    def _remove_overlapping_boxes(self, boxes: List[Tuple[int, int, int, int, float]], 
                                  overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int, float]]:
        """Remove overlapping bounding boxes using NMS-like approach"""
        if not boxes:
            return []
        
        # Sort by confidence
        boxes = sorted(boxes, key=lambda x: x[4], reverse=True)
        
        keep = []
        for i, box1 in enumerate(boxes):
            x1_1, y1_1, x2_1, y2_1, conf1 = box1
            
            should_keep = True
            for box2 in keep:
                x1_2, y1_2, x2_2, y2_2, conf2 = box2
                
                # Calculate intersection over union
                inter_x1 = max(x1_1, x1_2)
                inter_y1 = max(y1_1, y1_2)
                inter_x2 = min(x2_1, x2_2)
                inter_y2 = min(y2_1, y2_2)
                
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
                    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
                    union_area = box1_area + box2_area - inter_area
                    
                    if union_area > 0:
                        iou = inter_area / union_area
                        if iou > overlap_threshold:
                            should_keep = False
                            break
            
            if should_keep:
                keep.append(box1)
        
        return keep
    
    def preprocess_for_ocr(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Create multiple preprocessed variants for better OCR
        
        Args:
            image: Input license plate image
            
        Returns:
            List of preprocessed image variants
        """
        variants = []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize if too small (minimum 200px width)
        if gray.shape[1] < 200:
            scale_factor = 200 / gray.shape[1]
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
        
        # Variant 3: Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        variants.append(morph)
        
        # Variant 4: Sharpening + threshold
        kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel_sharp)
        _, thresh4 = cv2.threshold(sharpened, 127, 255, cv2.THRESH_BINARY)
        variants.append(thresh4)
        
        return variants
    
    def recognize_text_tesseract(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Recognize text using Tesseract OCR with multiple configurations
        
        Args:
            image: Preprocessed image
            
        Returns:
            List of (text, confidence) tuples
        """
        results = []
        
        # Different Tesseract configurations for license plates
        configs = [
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single word
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single text line
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Single uniform block
            '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Raw line
        ]
        
        for config in configs:
            try:
                # Get text and confidence
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract text with confidence
                text_parts = []
                confidences = []
                
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 30:  # Minimum confidence threshold
                        text = data['text'][i].strip()
                        if text:
                            text_parts.append(text)
                            confidences.append(int(data['conf'][i]))
                
                if text_parts:
                    full_text = ''.join(text_parts).upper()
                    avg_confidence = sum(confidences) / len(confidences) / 100.0
                    results.append((full_text, avg_confidence))
                    
            except Exception as e:
                logger.debug(f"Tesseract config failed: {e}")
                continue
        
        return results
    
    def recognize_text_easyocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Recognize text using EasyOCR
        
        Args:
            image: Preprocessed image
            
        Returns:
            List of (text, confidence) tuples
        """
        if self.easyocr_reader is None:
            return []
        
        try:
            results = self.easyocr_reader.readtext(image, detail=1, paragraph=False)
            
            text_results = []
            for (bbox, text, confidence) in results:
                # Clean text
                clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
                if len(clean_text) >= 6:  # Minimum length for license plate
                    text_results.append((clean_text, confidence))
            
            return text_results
            
        except Exception as e:
            logger.debug(f"EasyOCR failed: {e}")
            return []
    
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
        Main method to detect and read license plate
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with plate information or None
        """
        try:
            logger.info(f"🔍 Starting advanced plate detection on image of size: {image.shape}")
            
            # Step 1: Detect vehicles using YOLO to focus search area
            vehicles = self.detect_vehicles_yolo(image)
            
            all_plates = []
            
            # Step 2: Search for plates in vehicle regions
            if vehicles:
                for i, (vx1, vy1, vx2, vy2, v_conf) in enumerate(vehicles):
                    logger.info(f"🚗 Searching for plates in vehicle {i+1}")
                    
                    # Expand vehicle region slightly for better plate detection
                    margin = 20
                    roi = (
                        max(0, vx1 - margin),
                        max(0, vy1 - margin),
                        min(image.shape[1], vx2 + margin),
                        min(image.shape[0], vy2 + margin)
                    )
                    
                    plates = self.detect_plates_traditional(image, roi)
                    all_plates.extend(plates)
            else:
                # Fallback: search entire image
                logger.info("🔍 No vehicles detected, searching entire image")
                all_plates = self.detect_plates_traditional(image)
            
            if not all_plates:
                logger.info("❌ No license plates detected")
                return None
            
            # Step 3: Process each detected plate
            best_result = None
            best_confidence = 0
            
            for i, (x1, y1, x2, y2, detection_conf) in enumerate(all_plates):
                logger.info(f"📋 Processing plate region {i+1}: ({x1}, {y1}, {x2-x1}, {y2-y1})")
                
                # Extract plate region
                plate_region = image[y1:y2, x1:x2]
                
                if plate_region.size == 0:
                    continue
                
                # Preprocess for OCR
                variants = self.preprocess_for_ocr(plate_region)
                
                # Try OCR on all variants
                all_ocr_results = []
                
                for variant in variants:
                    # Try Tesseract
                    tesseract_results = self.recognize_text_tesseract(variant)
                    all_ocr_results.extend(tesseract_results)
                    
                    # Try EasyOCR
                    easyocr_results = self.recognize_text_easyocr(variant)
                    all_ocr_results.extend(easyocr_results)
                
                # Find best valid result
                for text, ocr_conf in all_ocr_results:
                    if self.validate_plate_format(text):
                        combined_conf = (detection_conf * 0.3 + ocr_conf * 0.7)
                        
                        if combined_conf > best_confidence:
                            best_confidence = combined_conf
                            best_result = {
                                "text": text,
                                "coordinates": (x1, y1, x2-x1, y2-y1),
                                "confidence": combined_conf,
                                "method": "advanced_cv_ocr"
                            }
                            logger.info(f"✅ New best plate: {text} (confidence: {combined_conf:.3f})")
            
            if best_result:
                logger.info(f"🎯 Final result: {best_result['text']} (confidence: {best_result['confidence']:.3f})")
                return best_result
            else:
                logger.info("❌ No valid license plates found")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in advanced plate detection: {e}")
            return None
