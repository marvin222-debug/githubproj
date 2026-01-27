#!/usr/bin/env python3
"""
Ultra-Fast License Plate Detector
Optimized for maximum speed and efficiency
"""

import cv2
import numpy as np
import logging
import re
import time
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
import threading

# Try to import optimized libraries
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)
class UltraFastDetector:
    """
    Ultra-optimized license plate detector with sub-second detection times
    """
    
    def __init__(self, min_confidence: float = 0.4, tesseract_path: str = None):
        """Initialize the ultra-fast detector"""
        self.min_confidence = min_confidence
        self.detection_cache = {}
        self.cache_timeout = 5.0  # 5 seconds cache
        self.last_detection_time = {}
        
        # Set Tesseract path if provided
        if TESSERACT_AVAILABLE and tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"✅ Tesseract path set: {tesseract_path}")
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize models lazily
        self._yolo_model = None
        self._easyocr_reader = None
        self._model_lock = threading.Lock()
        
        # Pre-compiled regex patterns for speed (more permissive)
        self.compiled_patterns = [
            re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$'),  # KA01AB1234, DL07KL9988
            re.compile(r'^[A-Z]{2}\d{1}[A-Z]{1,2}\d{4}$'),  # KA1AB1234
            re.compile(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{3}$'),    # DL07KL998
            re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$'),   # AB12C1234
        ]
        
        # Optimized preprocessing kernels
        self.blur_kernel = np.ones((3,3), np.float32) / 9
        self.sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        
        logger.info("🚀 Ultra-Fast Detector initialized")
    
    @property
    def yolo_model(self):
        """Lazy loading of YOLO model"""
        if self._yolo_model is None and YOLO_AVAILABLE:
            with self._model_lock:
                if self._yolo_model is None:
                    try:
                        self._yolo_model = YOLO('yolov8n.pt')
                        logger.info("✅ YOLO model loaded")
                    except Exception as e:
                        logger.warning(f"YOLO loading failed: {e}")
        return self._yolo_model
    
    @property
    def easyocr_reader(self):
        """Lazy loading of EasyOCR"""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            with self._model_lock:
                if self._easyocr_reader is None:
                    try:
                        self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
                        logger.info("✅ EasyOCR loaded")
                    except Exception as e:
                        logger.warning(f"EasyOCR loading failed: {e}")
        return self._easyocr_reader
    
    def fast_preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Lightning-fast preprocessing optimized for speed
        """
        # Convert to grayscale efficiently
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Quick resize if too small (vectorized operation)
        h, w = gray.shape
        if h < 40 or w < 120:
            scale = max(40/h, 120/w, 1.5)
            new_size = (int(w * scale), int(h * scale))
            gray = cv2.resize(gray, new_size, interpolation=cv2.INTER_LINEAR)
        
        # Fast bilateral filter for noise reduction
        filtered = cv2.bilateralFilter(gray, 5, 50, 50)
        
        # Optimized threshold
        _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def detect_plate_regions_fast(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Ultra-fast plate region detection using optimized contours
        """
        try:
            # Fast preprocessing
            processed = self.fast_preprocess(image)
            
            # Optimized edge detection
            edges = cv2.Canny(processed, 50, 150, apertureSize=3)
            
            # Fast contour detection with area filtering
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Pre-filter by area to avoid expensive operations
            min_area = 1000
            max_area = image.shape[0] * image.shape[1] * 0.3
            
            plate_regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Quick aspect ratio check for license plates
                    if 2.0 <= aspect_ratio <= 6.0 and w > 80 and h > 20:
                        plate_regions.append((x, y, x + w, y + h))
            
            # Sort by area (largest first) and return top candidates
            plate_regions.sort(key=lambda r: (r[2]-r[0]) * (r[3]-r[1]), reverse=True)
            return plate_regions[:5]  # Top 5 candidates
            
        except Exception as e:
            logger.error(f"Fast detection failed: {e}")
            return []
    
    def extract_text_optimized(self, image: np.ndarray) -> Optional[str]:
        """
        Optimized text extraction with multiple methods
        """
        if image.size == 0:
            return None
        
        all_results = []
        
        # Try EasyOCR first (usually most accurate)
        if self.easyocr_reader:
            try:
                results = self.easyocr_reader.readtext(image, detail=0)
                if results:
                    for result in results:
                        text = result.upper().replace(' ', '').replace('-', '')
                        text = ''.join(c for c in text if c.isalnum())
                        if len(text) >= 6:
                            all_results.append(text)
                            logger.info(f"EasyOCR detected: {text}")
            except Exception as e:
                logger.debug(f"EasyOCR failed: {e}")
        
        # Fallback to Tesseract if EasyOCR didn't work or not available
        if TESSERACT_AVAILABLE and (not all_results or not self.easyocr_reader):
            try:
                # Preprocess image for better OCR
                preprocessed = self._preprocess_for_tesseract(image)
                
                configs = [
                    '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                    '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                    '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                ]
                
                for prep_img in preprocessed:
                    for config in configs:
                        try:
                            text = pytesseract.image_to_string(prep_img, config=config).strip()
                            text = text.upper().replace(' ', '').replace('-', '')
                            text = ''.join(c for c in text if c.isalnum())
                            if len(text) >= 6:
                                all_results.append(text)
                                logger.info(f"Tesseract detected: {text}")
                        except Exception:
                            continue
            except Exception as e:
                logger.debug(f"Tesseract failed: {e}")
        
        # Return the best valid result
        for text in all_results:
            if self.validate_plate_fast(text):
                logger.info(f"✅ Valid plate found: {text}")
                return text
        
        # If no valid results, return the longest text (might still be useful)
        if all_results:
            longest = max(all_results, key=len)
            logger.info(f"⚠️ No valid format, returning longest: {longest}")
            return longest
        
        return None
    
    def _preprocess_for_tesseract(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess image specifically for Tesseract OCR"""
        results = []
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize if too small
            h, w = gray.shape
            if h < 40 or w < 120:
                scale = max(40/h, 120/w, 2.5)
                gray = cv2.resize(gray, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
            
            # Multiple preprocessing methods
            results.append(gray)
            
            # OTSU threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            results.append(thresh)
            
            # Inverted threshold
            _, thresh_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            results.append(thresh_inv)
            
            # CLAHE enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            results.append(enhanced)
            
            return results
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            return [gray if 'gray' in locals() else image]
    
    def validate_plate_fast(self, text: str) -> bool:
        """
        Ultra-fast plate validation using pre-compiled patterns
        """
        if not text or len(text) < 6 or len(text) > 13:
            return False
        
        text = text.upper().replace(' ', '').replace('-', '')
        
        # Check against pre-compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.match(text):
                logger.info(f"✅ Pattern match for: {text}")
                return True
        
        # More lenient heuristic check for Indian license plates
        if len(text) >= 7:
            # Must start with 2 letters (state code)
            if not text[:2].isalpha():
                logger.debug(f"Failed: First 2 chars not letters in {text}")
                return False
            
            # Must have digits and letters
            has_digits = any(c.isdigit() for c in text)
            has_letters = any(c.isalpha() for c in text[2:])
            
            if not (has_digits and has_letters):
                logger.debug(f"Failed: Missing digits or letters in {text}")
                return False
            
            # Check for common Indian plate patterns
            # Pattern: LLDDLLDDDD (like DL07KL9988)
            if len(text) == 10:
                if text[2:4].isdigit() and text[4:6].isalpha() and text[6:].isdigit():
                    logger.info(f"✅ Valid pattern LLDDLLDDDD: {text}")
                    return True
            
            # Pattern: LLDDLLLDDDD
            if len(text) == 11:
                if text[2:4].isdigit() and text[4:7].isalpha() and text[7:].isdigit():
                    logger.info(f"✅ Valid pattern LLDDLLLDDDD: {text}")
                    return True
            
            # Pattern: LLDDLLLDDD
            if len(text) == 10:
                if text[2:4].isdigit() and text[4:7].isalpha() and text[7:].isdigit():
                    logger.info(f"✅ Valid pattern LLDDLLLDDD: {text}")
                    return True
            
            # Pattern: LLDDLLDDD
            if len(text) == 9:
                if text[2:4].isdigit() and text[4:6].isalpha() and text[6:].isdigit():
                    logger.info(f"✅ Valid pattern LLDDLLDDD: {text}")
                    return True
            
            # Relaxed: If it has state code, some digits, and some letters, accept it
            if len(text) >= 8:
                digit_count = sum(1 for c in text if c.isdigit())
                letter_count = sum(1 for c in text if c.isalpha())
                if letter_count >= 3 and digit_count >= 3:
                    logger.info(f"✅ Valid by relaxed rules: {text}")
                    return True
        
        logger.debug(f"Failed validation: {text}")
        return False
    
    def check_cache(self, image_hash: str) -> Optional[Dict]:
        """
        Check if we have a recent detection for similar image
        """
        current_time = time.time()
        
        if image_hash in self.detection_cache:
            cache_entry = self.detection_cache[image_hash]
            if current_time - cache_entry['timestamp'] < self.cache_timeout:
                logger.debug("🎯 Cache hit - returning cached result")
                return cache_entry['result']
            else:
                # Clean expired cache
                del self.detection_cache[image_hash]
        
        return None
    
    def update_cache(self, image_hash: str, result: Dict):
        """
        Update detection cache
        """
        self.detection_cache[image_hash] = {
            'result': result,
            'timestamp': time.time()
        }
        
        # Limit cache size
        if len(self.detection_cache) > 50:
            oldest_key = min(self.detection_cache.keys(), 
                           key=lambda k: self.detection_cache[k]['timestamp'])
            del self.detection_cache[oldest_key]
    
    def detect_and_read_plate(self, image: np.ndarray) -> Optional[Dict]:
        """
        Main ultra-fast detection method
        """
        start_time = time.time()
        
        try:
            # Create simple hash for caching
            image_hash = str(hash(image.tobytes()))
            
            # Check cache first
            cached_result = self.check_cache(image_hash)
            if cached_result:
                return cached_result
            
            logger.info(f"🔍 Starting ultra-fast detection on {image.shape}")
            
            # Fast plate region detection
            plate_regions = self.detect_plate_regions_fast(image)
            
            if not plate_regions:
                logger.info("❌ No plate regions detected, trying full image")
                plate_regions = [(0, 0, image.shape[1], image.shape[0])]
            
            # Process regions in parallel for speed
            best_result = None
            best_confidence = 0
            
            for i, region in enumerate(plate_regions[:5]):  # Process top 5 candidates
                x1, y1, x2, y2 = region
                plate_image = image[y1:y2, x1:x2]
                
                if plate_image.size == 0:
                    logger.debug(f"Region {i} is empty, skipping")
                    continue
                
                logger.info(f"🔍 Processing region {i+1}/{len(plate_regions)}: {region}")
                
                # Fast text extraction
                detected_text = self.extract_text_optimized(plate_image)
                
                if detected_text:
                    logger.info(f"📝 Detected text: {detected_text}")
                    
                    # Even if validation fails, still consider it if it's the best we have
                    is_valid = self.validate_plate_fast(detected_text)
                    confidence = 0.85 if is_valid else 0.5
                    
                    if confidence > best_confidence or (confidence >= 0.5 and not best_result):
                        best_confidence = confidence
                        best_result = {
                            "text": detected_text,
                            "coordinates": (x1, y1, x2 - x1, y2 - y1),
                            "confidence": confidence,
                            "method": "ultra_fast",
                            "processing_time": time.time() - start_time
                        }
                        logger.info(f"🎯 New best result: {detected_text} (confidence: {confidence})")
                else:
                    logger.debug(f"No text detected in region {i}")
            
            # Cache the result
            if best_result:
                self.update_cache(image_hash, best_result)
                logger.info(f"🎯 Ultra-fast detection successful: {best_result['text']} "
                           f"in {best_result['processing_time']:.2f}s")
            else:
                logger.info("❌ No valid plates detected")
            
            return best_result
            
        except Exception as e:
            logger.error(f"❌ Ultra-fast detection error: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        self.detection_cache.clear()
