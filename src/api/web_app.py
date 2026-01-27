from flask import Flask, render_template, request, jsonify, redirect, url_for
import logging
import os
import sys
import time
import numpy as np
import cv2
from datetime import datetime
import threading

# Add the parent directory to the path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.capture.camera import Camera
from src.processing.plate_detector import PlateDetector
# from src.processing.enhanced_plate_detector import EnhancedPlateDetector  # Temporarily disabled due to dependency issues
from src.processing.simple_plate_detector import SimplePlateDetector
from src.processing.advanced_plate_detector import AdvancedPlateDetector

# Optional imports - handle gracefully if dependencies are missing
GeminiPlateDetector = None
try:
    from src.processing.gemini_plate_detector import GeminiPlateDetector
except Exception as e:
    print(f"⚠️ GeminiPlateDetector not available: {e}")

ContourPlateDetector = None
try:
    from src.processing.contour_plate_detector import ContourPlateDetector
except Exception as e:
    print(f"⚠️ ContourPlateDetector not available: {e}")

YOLOEnhancedDetector = None
try:
    from src.processing.yolo_enhanced_detector import YOLOEnhancedDetector
except Exception as e:
    print(f"⚠️ YOLOEnhancedDetector not available: {e}")

OptimizedPlateDetector = None
try:
    from src.processing.optimized_plate_detector import OptimizedPlateDetector
except Exception as e:
    print(f"⚠️ OptimizedPlateDetector not available: {e}")

RobustPlateDetector = None
try:
    from src.processing.robust_plate_detector import RobustPlateDetector
except Exception as e:
    print(f"⚠️ RobustPlateDetector not available: {e}")

UltraFastDetector = None
try:
    from src.processing.ultra_fast_detector import UltraFastDetector
except Exception as e:
    print(f"⚠️ UltraFastDetector not available: {e}")
from src.models.vehicle import Vehicle
from src.config.config import (
    DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT, MIN_CONFIDENCE, TESSERACT_PATH
)
from src.database.enhanced_mongodb_atlas_db import EnhancedMongoDBAtlasDatabase
from src.utils.performance_monitor import performance_monitor, record_detection_performance

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path of the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Set template and static folders paths
template_dir = os.path.abspath(os.path.join(current_dir, '../../src/templates'))
static_dir = os.path.abspath(os.path.join(current_dir, '../../src/static'))

# Initialize Flask app with correct template and static folders
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

# Enable debugging
app.config['DEBUG'] = True

# Add CORS support if available
try:
    from flask_cors import CORS
    CORS(app)  # Enable CORS for all routes
    logger.info("CORS enabled")
except ImportError:
    logger.warning("flask-cors not available, CORS not enabled")

# Initialize components - Use the ultra-fast detector first for maximum efficiency
try:
    if UltraFastDetector is not None:
        plate_detector = UltraFastDetector(min_confidence=MIN_CONFIDENCE, tesseract_path=TESSERACT_PATH)
        logger.info("⚡ Using Ultra-Fast Detector - Sub-Second Detection Times")
    else:
        raise ImportError("UltraFastDetector not available")
except Exception as e:
    logger.warning(f"Ultra-fast detector failed, trying robust detector: {e}")
    try:
        if RobustPlateDetector is not None:
            plate_detector = RobustPlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
            logger.info("💪 Using Robust Plate Detector - Ultra-Efficient for Clear Plates")
        else:
            raise ImportError("RobustPlateDetector not available")
    except Exception as e2:
        logger.warning(f"Robust detector failed, trying optimized detector: {e2}")
        try:
            if OptimizedPlateDetector is not None:
                plate_detector = OptimizedPlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
                logger.info("🎩 Using Optimized Plate Detector - Specialized for Indian Plates")
            else:
                raise ImportError("OptimizedPlateDetector not available")
        except Exception as e3:
            logger.warning(f"Optimized detector failed, trying YOLO detector: {e3}")
            try:
                if YOLOEnhancedDetector is not None:
                    plate_detector = YOLOEnhancedDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
                    logger.info("🚀 Using YOLO Enhanced Detector with EasyOCR")
                else:
                    raise ImportError("YOLOEnhancedDetector not available")
            except Exception as e4:
                logger.warning(f"YOLO detector failed, trying simple detector: {e4}")
                try:
                    plate_detector = SimplePlateDetector(min_confidence=MIN_CONFIDENCE)
                    logger.info("🔍 Using improved simple plate detector with OCR validation")
                except Exception as e5:
                    logger.warning(f"Simple detector failed, falling back to traditional: {e5}")
                    try:
                        plate_detector = PlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
                        logger.info("Using traditional plate detector")
                    except Exception as e6:
                        logger.error(f"All detectors failed: {e6}")
                        raise

# Mock vehicle database to avoid MongoDB dependency for demo
class MockVehicleDB:
    def __init__(self):
        # Create some sample vehicle data - expanded for testing
        self.vehicles = {
            "KA01MJ2023": {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla"
            },
            # Add variations to handle OCR inconsistencies
            "KA0IMJ2023": {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla"
            },
            "KAOIMJ2023": {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla"
            },
            "DL05AB1234": {
                "registration_number": "DL05AB1234",
                "registration_date": datetime(2010, 6, 10),
                "fuel_type": "DIESEL",
                "owner_name": "Jane Smith",
                "vehicle_make": "Honda",
                "vehicle_model": "City"
            },
            "MH02CD5678": {
                "registration_number": "MH02CD5678",
                "registration_date": datetime(2008, 3, 22),
                "fuel_type": "PETROL",
                "owner_name": "Raj Kumar",
                "vehicle_make": "Maruti",
                "vehicle_model": "Swift"
            },
            "KA63MA6613": {
                "registration_number": "KA63MA6613",
                "registration_date": datetime(2020, 5, 15),
                "fuel_type": "PETROL",
                "owner_name": "Test User",
                "vehicle_make": "Hyundai",
                "vehicle_model": "i20"
            },
            # Additional test data for different scenarios
            "KA05AB1234": {
                "registration_number": "KA05AB1234",
                "registration_date": datetime(2015, 8, 20),
                "fuel_type": "DIESEL",
                "owner_name": "Test Owner 1",
                "vehicle_make": "Tata",
                "vehicle_model": "Nexon"
            },
            "TN09XY5678": {
                "registration_number": "TN09XY5678",
                "registration_date": datetime(2012, 3, 15),
                "fuel_type": "PETROL",
                "owner_name": "Test Owner 2",
                "vehicle_make": "Ford",
                "vehicle_model": "EcoSport"
            },
            "UP16MN9012": {
                "registration_number": "UP16MN9012",
                "registration_date": datetime(2005, 11, 8),
                "fuel_type": "DIESEL",
                "owner_name": "Test Owner 3",
                "vehicle_make": "Mahindra",
                "vehicle_model": "Scorpio"
            },
            "GJ01KL3456": {
                "registration_number": "GJ01KL3456",
                "registration_date": datetime(2018, 9, 12),
                "fuel_type": "PETROL",
                "owner_name": "Test Owner 4",
                "vehicle_make": "Volkswagen",
                "vehicle_model": "Polo"
            },
            "RJ14PQ7890": {
                "registration_number": "RJ14PQ7890",
                "registration_date": datetime(2003, 4, 25),
                "fuel_type": "DIESEL",
                "owner_name": "Test Owner 5",
                "vehicle_make": "Hyundai",
                "vehicle_model": "Accent"
            },
            "AP31RS2345": {
                "registration_number": "AP31RS2345",
                "registration_date": datetime(2019, 7, 30),
                "fuel_type": "PETROL",
                "owner_name": "Test Owner 6",
                "vehicle_make": "Maruti Suzuki",
                "vehicle_model": "Baleno"
            },
            "DL07KL9988": {
                "registration_number": "DL07KL9988",
                "registration_date": datetime(2022, 1, 1),
                "fuel_type": "PETROL",
                "owner_name": "New User",
                "vehicle_make": "Kia",
                "vehicle_model": "Seltos"
            }
        }
        
    def get_vehicle_info(self, registration_number):
        """Mock implementation that returns vehicle info from our sample data"""
        # Normalize the registration number
        original_number = registration_number
        registration_number = registration_number.replace(" ", "").upper()
        
        # Log the registration number being searched
        logger.info(f"Looking up vehicle with registration number: {registration_number}")
        
        # Look for the vehicle in our sample data
        vehicle_data = self.vehicles.get(registration_number)
        
        # If not found, try fuzzy matching for common OCR errors
        if not vehicle_data:
            logger.info(f"Exact match not found, trying fuzzy matching...")
            
            # Try common OCR corrections
            variations = [
                registration_number.replace('0', 'O'),  # 0 -> O
                registration_number.replace('O', '0'),  # O -> 0
                registration_number.replace('1', 'I'),  # 1 -> I
                registration_number.replace('I', '1'),  # I -> 1
                registration_number.replace('5', 'S'),  # 5 -> S
                registration_number.replace('S', '5'),  # S -> 5
            ]
            
            for variation in variations:
                if variation in self.vehicles:
                    logger.info(f"Found match with variation: {variation}")
                    vehicle_data = self.vehicles[variation]
                    break
        
        if not vehicle_data:
            logger.warning(f"Vehicle not found even with fuzzy matching: {registration_number}")
            return None
            
        # Create a Vehicle object from the data
        vehicle = Vehicle(
            registration_number=vehicle_data["registration_number"],
            registration_date=vehicle_data["registration_date"],
            fuel_type=vehicle_data["fuel_type"],
            owner_name=vehicle_data.get("owner_name"),
            vehicle_make=vehicle_data.get("vehicle_make"),
            vehicle_model=vehicle_data.get("vehicle_model")
        )
        
        # Log that the vehicle was found
        logger.info(f"Vehicle found: {vehicle.registration_number} ({vehicle.fuel_type}, Age: {vehicle.age:.1f} years)")
        
        return vehicle
        
    def search_vehicles(self, **filters):
        """
        Search vehicles with filters - mock implementation
        """
        results = []
        for plate, vehicle_data in self.vehicles.items():
            match = True
            for key, value in filters.items():
                if key == "fuel_type" and vehicle_data.get("fuel_type", "").upper() != value:
                    match = False
                    break
                elif key == "vehicle_make" and vehicle_data.get("vehicle_make", "").lower() != value.lower():
                    match = False
                    break
                # Add more filter types as needed
            if match:
                results.append(vehicle_data)

        logger.info(f"Mock search found {len(results)} vehicles matching filters: {filters}")
        return results

# Database connection management
_vehicle_db = None
_db_lock = threading.Lock()

def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    global _vehicle_db
    with _db_lock:
        if _vehicle_db is None:
            try:
                logger.info("Initializing new database connection...")
                _vehicle_db = EnhancedMongoDBAtlasDatabase()
                logger.info("✅ Database connection successful.")
            except Exception as e:
                logger.critical(f"CRITICAL: Failed to initialize database connection. Error: {e}")
                _vehicle_db = None # Ensure it's None on failure
    return _vehicle_db

# ----- Web Routes -----

@app.route('/')
def index():
    """Home page with connection status"""
    db = get_db()
    if db is None:
        return "MongoDB Atlas: ❌ Not Connected"
    return render_template('index.html')

@app.route('/upload')
def upload():
    """Upload image page"""
    return render_template('upload.html')

@app.route('/check')
def check():
    """Check registration page"""
    return render_template('check.html')

@app.route('/camera')
def camera():
    """Live camera capture and ANPR page"""
    return render_template('camera_check.html')

@app.route('/add')
def add_vehicle():
    """Add vehicle page"""
    return render_template('add_vehicle.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# ----- API Routes -----

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route("/api/process", methods=["POST"])
def process_image():
    """
    Process an uploaded image to detect a license plate and check fuel eligibility
    """
    try:
        logger.info("=== API PROCESS REQUEST RECEIVED ===")
        logger.info(f"Request method: {request.method}, Content-Type: {request.content_type}")
        logger.info(f"Files in request: {list(request.files.keys())}")
        
        # Check if image is in the request
        if "image" not in request.files:
            logger.warning("No image file in request")
            logger.warning(f"Available files: {list(request.files.keys())}")
            return jsonify({"success": False, "message": "No image uploaded"}), 400
            
        file = request.files["image"]
        logger.info(f"Received image file: {file.filename}, size: {file.content_length}")
        
        # Read the image
        img_array = np.frombuffer(file.read(), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            return jsonify({"success": False, "message": "Invalid image format"}), 400
            
        logger.info(f"Image decoded successfully, shape: {image.shape}")
        
        # Check if plate detector is initialized
        if plate_detector is None:
            logger.error("Plate detector is not initialized")
            return jsonify({
                "success": False,
                "message": "Plate detection system is not available. Please contact administrator."
            }), 503
            
        # Detect and read license plate with performance monitoring
        detection_start_time = time.time()
        try:
            logger.info(f"Calling plate detector: {type(plate_detector).__name__}")
            plate_result = plate_detector.detect_and_read_plate(image)
            logger.info(f"Plate detection completed, result: {plate_result}")
        except Exception as det_error:
            logger.error(f"Error in plate detection: {det_error}", exc_info=True)
            import traceback
            logger.error(f"Detection error traceback: {traceback.format_exc()}")
            # Return a safe error response instead of crashing
            return jsonify({
                "success": False,
                "message": f"Error during plate detection: {str(det_error)}. Please try again with a clearer image."
            }), 500
        detection_time = time.time() - detection_start_time

        # Determine registration number and optional box
        registration_number = None
        plate_box = None

        if plate_result and isinstance(plate_result, dict) and plate_result.get("text"):
            registration_number = plate_result["text"]
            coords = plate_result.get("coordinates")
            if coords and isinstance(coords, (list, tuple)) and len(coords) == 4:
                x, y, w, h = coords
                plate_box = {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
            logger.info(f"Detected plate: {registration_number}")
        else:
            logger.info("No plate detected in image")
        
        # Only use fallback if explicitly requested (for testing)
        use_demo_fallback = request.form.get('demo_fallback', 'false').lower() == 'true'
        if use_demo_fallback and (not registration_number or len(registration_number) < 5):
            registration_number = "KA01MJ2023"
            logger.info(f"Using sample plate {registration_number} for demo fallback")
        
        # Normalize registration number (remove spaces, uppercase)
        if registration_number:
            registration_number = registration_number.replace(" ", "").upper()
        
        # Check if we have a valid registration number
        if not registration_number or len(registration_number) < 6:
            # Try full image OCR as last resort
            logger.info("Trying full image OCR as fallback...")
            try:
                import pytesseract
                from src.config.config import TESSERACT_PATH
                if TESSERACT_PATH:
                    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
                
                # Try OCR on full image with different configs
                full_text = pytesseract.image_to_string(image, config='--psm 7').strip().upper()
                full_text_clean = ''.join(c for c in full_text if c.isalnum())
                
                # Look for plate pattern
                import re
                plate_match = re.search(r'([A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4})', full_text_clean)
                if plate_match:
                    registration_number = plate_match.group(1)
                    logger.info(f"✅ Found plate via full image OCR: {registration_number}")
                else:
                    logger.info(f"Full image OCR found: {full_text_clean[:20]}...")
            except Exception as e:
                logger.warning(f"Full image OCR fallback failed: {e}")
            
            if not registration_number or len(registration_number) < 6:
                detected_text = plate_result.get('text', 'N/A') if (plate_result and isinstance(plate_result, dict)) else 'None'
                return jsonify({
                    "success": False,
                    "message": f"No valid license plate detected in the image. Detected text: {detected_text}"
                }), 200
        
        vehicle_db = get_db()
        if not vehicle_db:
            logger.error("Database not available. Check Atlas connection.")
            return jsonify({
                "success": False,
                "message": "Database connection is not available. Please check the server logs."
            }), 503 # Service Unavailable

        # Get vehicle info from database
        vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        # If not found, try variations (remove spaces, common OCR errors)
        if not vehicle:
            # Try variations: remove spaces, fix common OCR errors
            variations = [
                registration_number.replace(" ", ""),  # Remove spaces: "DL 07 KL 9988" -> "DL07KL9988"
                registration_number.replace("0", "O"),  # Try O instead of 0
                registration_number.replace("O", "0"),  # Try 0 instead of O
                registration_number.replace("1", "I"),  # Try I instead of 1
                registration_number.replace("I", "1"),  # Try 1 instead of I
            ]
            
            for variation in variations:
                if variation != registration_number:
                    logger.info(f"Trying variation: {variation}")
                    vehicle = vehicle_db.get_vehicle_info(variation)
                    if vehicle:
                        logger.info(f"Found vehicle with variation: {variation}")
                        registration_number = variation  # Update to the found variation
                        break
        
        if not vehicle:
            # Gracefully return a 200 with success false so the UI can show a message
            detected_text = plate_result.get('text', 'N/A') if (plate_result and isinstance(plate_result, dict)) else 'None'
            return jsonify({
                "success": False,
                "message": f"Vehicle information not found for registration number: {registration_number}. Detected text: {detected_text}"
            }), 200
            
        # Check fuel eligibility based on age
        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
        
        # Format the response with consistent field names
        response = {
            "success": True,
            "registration_number": vehicle.registration_number,
            "vehicle_details": {
                "registration_date": vehicle.registration_date.isoformat(),
                "fuel_type": vehicle.fuel_type,
                "age_years": round(vehicle.age, 2),
                "make": vehicle.vehicle_make,
                "model": vehicle.vehicle_model,
                "vehicle_make": vehicle.vehicle_make,  # Keep both for compatibility
                "vehicle_model": vehicle.vehicle_model
            },
            "fuel_eligibility": {
                "eligible": eligible,
                "reason": None if eligible else f"Vehicle exceeds age limit for {vehicle.fuel_type.lower()} vehicles",
                "age_limit": DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
            }
        }
        if plate_box:
            response["plate_box"] = plate_box
        
        # Record performance metrics
        method_used = plate_result.get("method", type(plate_detector).__name__) if (plate_result and isinstance(plate_result, dict)) else type(plate_detector).__name__
        confidence = plate_result.get("confidence", 0.0) if (plate_result and isinstance(plate_result, dict)) else 0.0
        record_detection_performance(
            method=method_used,
            processing_time=detection_time,
            success=bool(registration_number),
            confidence=confidence,
            plate_text=registration_number
        )
        
        # Add performance info to response
        response["performance"] = {
            "detection_time": round(detection_time, 3),
            "method_used": method_used
        }
        
        # Log the response
        logger.info(f"API response: {response}")
        
        return jsonify(response), 200
        
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        logger.error(error_msg, exc_info=True)  # Include full traceback in logs
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return a structured error response with more details
        # Make sure we always return a valid JSON response
        try:
            error_details = {
                "success": False,
                "message": f"An error occurred while processing the image: {str(e)}",
                "error": str(e),
                "type": type(e).__name__
            }
            logger.error(f"Returning error response: {error_details}")
            return jsonify(error_details), 500
        except Exception as json_error:
            # If even JSON serialization fails, return a simple text response
            logger.critical(f"Failed to serialize error response: {json_error}")
            return f"Internal server error: {str(e)}", 500

@app.route("/api/check-plate", methods=["GET"])
def check_registration():
    """
    Check a registration number against the database
    """
    try:
        # Get registration number from query parameters
        registration_number = request.args.get("plate", "").replace(" ", "").upper()
        
        if not registration_number:
            return jsonify({"success": False, "message": "No registration number provided"}), 400
            
        vehicle_db = get_db()
        if not vehicle_db:
            logger.error("Database not available. Check Atlas connection.")
            return jsonify({
                "success": False,
                "message": "Database connection is not available. Please check the server logs."
            }), 503 # Service Unavailable

        # Get vehicle information
        vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        if not vehicle:
            return jsonify({
                "success": False,
                "message": f"Vehicle information not found for registration number: {registration_number}"
            }), 404
            
        # Check fuel eligibility based on age
        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
        
        # Format the response with consistent field names
        response = {
            "success": True,
            "registration_number": vehicle.registration_number,
            "vehicle_details": {
                "registration_date": vehicle.registration_date.isoformat(),
                "fuel_type": vehicle.fuel_type,
                "age_years": round(vehicle.age, 2),
                "make": vehicle.vehicle_make,
                "model": vehicle.vehicle_model,
                "vehicle_make": vehicle.vehicle_make,  # Keep both for compatibility
                "vehicle_model": vehicle.vehicle_model
            },
            "fuel_eligibility": {
                "eligible": eligible,
                "reason": None if eligible else f"Vehicle exceeds age limit for {vehicle.fuel_type.lower()} vehicles",
                "age_limit": DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error checking registration: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/vehicles", methods=["GET"])
def get_all_vehicles():
    """List vehicles from MongoDB Atlas with pagination and optional filters"""
    try:
        # Query params
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        fuel_type = request.args.get("fuel_type")
        state = request.args.get("state")
        make = request.args.get("make")

        # Build filters
        filters = {}
        if fuel_type:
            filters["fuel_type"] = fuel_type.upper()
        if state:
            filters["state"] = state
        if make:
            filters["vehicle_make"] = make

        # Ensure the db supports listing
        vehicle_db = get_db()
        if not vehicle_db or not hasattr(vehicle_db, "search_vehicles"):
            return jsonify({"success": False, "message": "Vehicle listing not available. Check database connection."}), 503

        # Fetch vehicles
        vehicles = vehicle_db.search_vehicles(**filters) or []

        total = len(vehicles)
        start_idx = max((page - 1) * per_page, 0)
        end_idx = start_idx + per_page
        paginated = vehicles[start_idx:end_idx]

        # Normalize and compute eligibility
        from datetime import datetime
        response_items = []
        for v in paginated:
            # registration_date may be datetime or string
            reg = v.get("registration_date")
            if isinstance(reg, str):
                try:
                    reg_date = datetime.fromisoformat(reg)
                except Exception:
                    reg_date = None
            else:
                reg_date = reg

            if reg_date:
                age = (datetime.now() - reg_date).days / 365.25
            else:
                age = None

            ft = (v.get("fuel_type") or "").upper()
            if ft == "DIESEL" and age is not None:
                eligible = age <= DIESEL_AGE_LIMIT
                age_limit = DIESEL_AGE_LIMIT
            elif ft == "PETROL" and age is not None:
                eligible = age <= PETROL_AGE_LIMIT
                age_limit = PETROL_AGE_LIMIT
            else:
                eligible = True
                age_limit = None

            response_items.append({
                "registration_number": v.get("registration_number"),
                "registration_date": reg_date.isoformat() if reg_date else None,
                "fuel_type": v.get("fuel_type"),
                "owner_name": v.get("owner_name"),
                "vehicle_make": v.get("vehicle_make"),
                "vehicle_model": v.get("vehicle_model"),
                "state": v.get("state"),
                "district": v.get("district"),
                "chassis_number": v.get("chassis_number"),
                "engine_number": v.get("engine_number"),
                "age_years": round(age, 2) if age is not None else None,
                "fuel_eligibility": {
                    "eligible": eligible,
                    "age_limit": age_limit
                }
            })

        return jsonify({
            "success": True,
            "total_vehicles": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "vehicles": response_items
        }), 200

    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/test-yolo", methods=["GET"])
def test_yolo():
    """
    Test endpoint to verify YOLO detector is working
    """
    try:
        logger.info("Testing YOLO detector...")
        
        # Create a simple test image
        import numpy as np
        test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "KA01MJ2023", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # Test detection
        result = plate_detector.detect_and_read_plate(test_image)
        
        return jsonify({
            "success": True,
            "test_result": result,
            "message": "YOLO detector test completed"
        }), 200
        
    except Exception as e:
        logger.error(f"YOLO test error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/test-detection", methods=["POST"])
def test_detection():
    """
    Test endpoint to debug plate detection
    """
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "message": "No image uploaded"}), 400
            
        file = request.files["image"]
        
        # Read the image
        img_array = np.frombuffer(file.read(), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({"success": False, "message": "Invalid image format"}), 400
        
        logger.info(f"Test detection - Image shape: {image.shape}")
        
        # Test plate detection
        plate_result = plate_detector.detect_and_read_plate(image)
        
        return jsonify({
            "success": True,
            "image_shape": image.shape,
            "detection_result": plate_result,
            "detector_type": type(plate_detector).__name__,
            "message": "Detection test completed"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test detection: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/test-gemini", methods=["GET"])
def test_gemini():
    """
    Test endpoint to verify Gemini detector is working
    """
    try:
        logger.info("Testing Gemini detector...")
        
        # Check if we're using Gemini detector
        if GeminiPlateDetector is None or not isinstance(plate_detector, GeminiPlateDetector):
            return jsonify({
                "success": False,
                "message": f"Gemini detector not available. Current detector: {type(plate_detector).__name__}"
            }), 400
        
        # Test Gemini connection
        gemini_working = plate_detector.test_gemini_connection()
        
        # Create a simple test image
        import numpy as np
        test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "KA01AB1234", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # Test detection
        result = plate_detector.detect_and_read_plate(test_image)
        
        return jsonify({
            "success": True,
            "gemini_connection": gemini_working,
            "test_result": result,
            "detector_type": "GeminiPlateDetector",
            "message": "Gemini detector test completed"
        }), 200
        
    except Exception as e:
        logger.error(f"Gemini test error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/add-vehicle", methods=["POST"])
def add_vehicle_api():
    """
    Add a new vehicle to the database
    """
    try:
        # Get vehicle data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Check required fields
        required_fields = ['registration_number', 'registration_date', 'fuel_type', 
                          'owner_name', 'vehicle_make', 'vehicle_model']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Convert registration date string to datetime
        registration_date = datetime.fromisoformat(data['registration_date'])
        
        # Create vehicle object
        vehicle = Vehicle(
            registration_number=data['registration_number'].replace(" ", "").upper(),
            registration_date=registration_date,
            fuel_type=data['fuel_type'].upper(),
            owner_name=data['owner_name'],
            vehicle_make=data['vehicle_make'],
            vehicle_model=data['vehicle_model'],
            chassis_number=data.get('chassis_number', ''),
            engine_number=data.get('engine_number', '')
        )
        
        # Persist the vehicle
        saved = False
        vehicle_db = get_db()
        if vehicle_db and hasattr(vehicle_db, "add_vehicle"):
            # Use MongoDB Atlas adapter
            try:
                saved = vehicle_db.add_vehicle(vehicle)
            except Exception as e:
                logger.error(f"Error saving vehicle using MongoDB Atlas adapter: {str(e)}")
                return jsonify({"success": False, "message": str(e)}), 500
        elif vehicle_db and hasattr(vehicle_db, "vehicles"):
            # Fallback to in-memory mock
            try:
                vehicle_db.vehicles[vehicle.registration_number] = {
                    "registration_number": vehicle.registration_number,
                    "registration_date": vehicle.registration_date,
                    "fuel_type": vehicle.fuel_type,
                    "owner_name": vehicle.owner_name,
                    "vehicle_make": vehicle.vehicle_make,
                    "vehicle_model": vehicle.vehicle_model,
                    "chassis_number": vehicle.chassis_number,
                    "engine_number": vehicle.engine_number
                }
                saved = True
            except Exception as e:
                logger.error(f"Error saving vehicle using in-memory mock: {str(e)}")
                return jsonify({"success": False, "message": str(e)}), 500
        else:
            logger.error("No database available for saving vehicle")
            return jsonify({"success": False, "message": "Database not available"}), 503
        
        logger.info(f"Vehicle added to database: {vehicle.registration_number}")
        return jsonify({"success": True, "message": "Vehicle added successfully"}), 201
        
    except Exception as e:
        logger.error(f"Error adding vehicle: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/performance", methods=["GET"])
def get_performance_metrics():
    """
    Get system performance metrics
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/performance/realtime", methods=["GET"])
def get_realtime_metrics():
    """
    Get real-time performance metrics
    """
    try:
        metrics = performance_monitor.get_real_time_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/performance/reset", methods=["POST"])
def reset_performance_metrics():
    """
    Reset performance metrics
    """
    try:
        performance_monitor.reset_metrics()
        return jsonify({"success": True, "message": "Performance metrics reset"}), 200
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/atlas/status", methods=["GET"])
def get_atlas_status():
    """
    Get MongoDB Atlas connection status
    """
    try:
        vehicle_db = get_db()
        if vehicle_db and hasattr(vehicle_db, 'get_connection_status'):
            status = vehicle_db.get_connection_status()
            return jsonify({
                "success": True,
                "atlas_status": status,
                "database_type": "Enhanced MongoDB Atlas"
            }), 200
        elif vehicle_db:
            return jsonify({
                "success": True,
                "atlas_status": {"connected": False, "reason": "Using mock database"},
                "database_type": "Mock Database"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Database not available"
            }), 503
    except Exception as e:
        logger.error(f"Error getting Atlas status: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/atlas/reconnect", methods=["POST"])
def force_atlas_reconnect():
    """
    Force Atlas reconnection
    """
    try:
        vehicle_db = get_db()
        if vehicle_db and hasattr(vehicle_db, 'force_reconnect'):
            success = vehicle_db.force_reconnect()
            return jsonify({
                "success": success,
                "message": "Reconnection successful" if success else "Reconnection failed"
            }), 200
        elif vehicle_db:
            return jsonify({
                "success": False,
                "message": "Atlas reconnection not available with current database"
            }), 400
        else:
            return jsonify({
                "success": False,
                "message": "Database not available"
            }), 503
    except Exception as e:
        logger.error(f"Error forcing Atlas reconnect: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/atlas/stats", methods=["GET"])
def get_atlas_stats():
    """
    Get Atlas database statistics
    """
    try:
        vehicle_db = get_db()
        if vehicle_db and hasattr(vehicle_db, 'get_database_stats'):
            stats = vehicle_db.get_database_stats()
            return jsonify({
                "success": True,
                "database_stats": stats
            }), 200
        elif vehicle_db and hasattr(vehicle_db, 'connection'):
            # Try to get stats from connection
            try:
                if hasattr(vehicle_db.connection, 'collection'):
                    collection = vehicle_db.connection.collection
                    total_count = collection.count_documents({})
                    
                    # Get sample vehicles
                    sample_vehicles = list(collection.find({}).limit(10))
                    
                    # Get unique fuel types
                    fuel_types = collection.distinct("fuel_type")
                    
                    # Get unique states
                    states = collection.distinct("state")
                    
                    return jsonify({
                        "success": True,
                        "database_stats": {
                            "total_vehicles": total_count,
                            "database_type": "MongoDB Atlas",
                            "fuel_types": fuel_types,
                            "states": states,
                            "sample_count": len(sample_vehicles),
                            "connection_status": vehicle_db.connection.is_connected if hasattr(vehicle_db.connection, 'is_connected') else "Unknown"
                        }
                    }), 200
            except Exception as e:
                logger.error(f"Error getting stats from connection: {e}")
                return jsonify({
                    "success": True,
                    "database_stats": {
                        "total_vehicles": "Unknown",
                        "database_type": "MongoDB Atlas (Connection Error)",
                        "error": str(e)
                    }
                }), 200
        elif vehicle_db and hasattr(vehicle_db, 'connection'):
            # Try to get stats from connection
            try:
                if hasattr(vehicle_db.connection, 'collection') and vehicle_db.connection.collection:
                    collection = vehicle_db.connection.collection
                    total_count = collection.count_documents({})
                    
                    # Get sample vehicles
                    sample_vehicles = list(collection.find({}).limit(10))
                    
                    # Get unique fuel types
                    fuel_types = collection.distinct("fuel_type")
                    
                    # Get unique states
                    states = collection.distinct("state")
                    
                    return jsonify({
                        "success": True,
                        "database_stats": {
                            "total_vehicles": total_count,
                            "database_type": "MongoDB Atlas",
                            "fuel_types": fuel_types,
                            "states": states,
                            "sample_count": len(sample_vehicles),
                            "connection_status": vehicle_db.connection.is_connected if hasattr(vehicle_db.connection, 'is_connected') else "Unknown"
                        }
                    }), 200
            except Exception as e:
                logger.error(f"Error getting stats from connection: {e}")
                return jsonify({
                    "success": True,
                    "database_stats": {
                        "total_vehicles": "Unknown",
                        "database_type": "MongoDB Atlas (Connection Error)",
                        "error": str(e)
                    }
                }), 200
        elif vehicle_db and hasattr(vehicle_db, 'vehicles'):
            return jsonify({
                "success": True,
                "database_stats": {
                    "total_vehicles": len(vehicle_db.vehicles),
                    "database_type": "Mock Database"
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Database not available"
            }), 503
    except Exception as e:
        logger.error(f"Error getting Atlas stats: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/atlas/plates", methods=["GET"])
def list_atlas_plates():
    """
    List registration numbers present in Atlas
    """
    try:
        vehicle_db = get_db()
        if vehicle_db and hasattr(vehicle_db, 'list_plate_numbers'):
            plates = vehicle_db.list_plate_numbers(limit=2000)
            return jsonify({
                "success": True,
                "count": len(plates),
                "plates": plates
            }), 200
        elif vehicle_db:
            return jsonify({
                "success": False,
                "message": "Listing plates not supported by current database"
            }), 400
        else:
            return jsonify({
                "success": False,
                "message": "Database not available"
            }), 503
    except Exception as e:
        logger.error(f"Error listing Atlas plates: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    print(f"Available sample plates: KA01MJ2023, DL05AB1234, MH02CD5678, KA63MA6613, KA05AB1234, TN09XY5678, UP16MN9012, GJ01KL3456, RJ14PQ7890, AP31RS2345")
    print("Note: System is currently using mock database due to MongoDB Atlas connection issues")
    app.run(host="0.0.0.0", port=5000, debug=True) 
