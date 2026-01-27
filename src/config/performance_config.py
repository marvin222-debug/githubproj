#!/usr/bin/env python3
"""
Performance Configuration for ANPR System
Optimized settings for maximum efficiency
"""

import os
import multiprocessing

# Performance Settings
PERFORMANCE_CONFIG = {
    # Detection Settings
    "MAX_IMAGE_SIZE": (1280, 720),  # Resize large images for faster processing
    "MIN_IMAGE_SIZE": (640, 480),   # Minimum size for reliable detection
    "DETECTION_TIMEOUT": 8.0,       # Reduced timeout for faster response
    "CACHE_ENABLED": True,
    "CACHE_SIZE": 100,
    "CACHE_TTL": 10.0,              # Cache time-to-live in seconds
    
    # Model Settings
    "YOLO_CONFIDENCE": 0.4,         # Lower confidence for faster detection
    "YOLO_IOU_THRESHOLD": 0.5,
    "YOLO_MAX_DETECTIONS": 5,       # Limit detections for speed
    "OCR_CONFIDENCE": 0.3,
    "PARALLEL_OCR": True,           # Run multiple OCR methods in parallel
    
    # Processing Settings
    "MAX_WORKERS": min(4, multiprocessing.cpu_count()),
    "PREPROCESSING_THREADS": 2,
    "BATCH_SIZE": 1,                # Process one image at a time for real-time
    "GPU_ENABLED": False,           # Disable GPU for consistency (enable if available)
    
    # Camera Settings
    "FRAME_SKIP": 2,                # Skip frames for real-time processing
    "AUTO_SCAN_INTERVAL": 4.0,      # 4 seconds for better result visibility
    "COOLDOWN_PERIOD": 3.0,         # 3 seconds for better user experience
    "MAX_RETRY_ATTEMPTS": 2,        # Reduced retries for faster response
    
    # Quality vs Speed Trade-offs
    "FAST_MODE": True,              # Enable fast mode optimizations
    "SKIP_COMPLEX_PREPROCESSING": True,  # Skip heavy preprocessing
    "USE_SIMPLE_CONTOURS": True,    # Use faster contour detection
    "EARLY_EXIT_ON_SUCCESS": True,  # Stop processing once plate is found
    
    # Detector Priority (fastest first)
    "DETECTOR_PRIORITY": [
        "ultra_fast",
        "robust", 
        "optimized",
        "yolo_enhanced",
        "contour",
        "simple"
    ],
    
    # Feature Flags
    "ENABLE_LOGGING": True,
    "ENABLE_METRICS": True,
    "ENABLE_DEBUG_IMAGES": False,   # Disable for production speed
    "ENABLE_PLATE_OVERLAY": True,
    "ENABLE_CONFIDENCE_DISPLAY": True
}

# Environment-specific overrides
if os.getenv('ANPR_FAST_MODE', 'true').lower() == 'true':
    PERFORMANCE_CONFIG.update({
        "DETECTION_TIMEOUT": 5.0,
        "MAX_WORKERS": 2,
        "FRAME_SKIP": 3,
        "AUTO_SCAN_INTERVAL": 4.0,  # Keep user-friendly timing even in fast mode
        "COOLDOWN_PERIOD": 3.0
    })

# Hardware-specific optimizations
def get_optimized_config():
    """Get configuration optimized for current hardware"""
    config = PERFORMANCE_CONFIG.copy()
    
    # CPU optimization
    cpu_count = multiprocessing.cpu_count()
    if cpu_count >= 8:
        config["MAX_WORKERS"] = 6
        config["PREPROCESSING_THREADS"] = 3
    elif cpu_count >= 4:
        config["MAX_WORKERS"] = 3
        config["PREPROCESSING_THREADS"] = 2
    else:
        config["MAX_WORKERS"] = 2
        config["PREPROCESSING_THREADS"] = 1
    
    # Memory optimization
    try:
        import psutil
        available_memory = psutil.virtual_memory().available / (1024**3)  # GB
        
        if available_memory < 4:  # Less than 4GB RAM
            config.update({
                "CACHE_SIZE": 50,
                "MAX_IMAGE_SIZE": (960, 540),
                "YOLO_MAX_DETECTIONS": 3
            })
        elif available_memory > 8:  # More than 8GB RAM
            config.update({
                "CACHE_SIZE": 200,
                "MAX_IMAGE_SIZE": (1920, 1080),
                "YOLO_MAX_DETECTIONS": 10
            })
    except ImportError:
        pass  # psutil not available
    
    return config

# Export optimized configuration
OPTIMIZED_CONFIG = get_optimized_config()
