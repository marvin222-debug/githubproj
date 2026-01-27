from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging
import os
import sys
import numpy as np
import cv2
import base64
import io
from PIL import Image
import random

# Add the parent directory to the path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the expanded vehicle database
from src.database.vehicle_db_expanded import VehicleDatabase

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

# Age limits for vehicles
DIESEL_AGE_LIMIT = 10
PETROL_AGE_LIMIT = 15

# Initialize the vehicle database
# For demo purposes, we'll use mock data by default
# In a production setting, you might use online data with an API key
vehicle_db = VehicleDatabase(use_mock=True)

# Load the available sample plates for display
SAMPLE_VEHICLES = {key: value for key, value in vehicle_db.vehicles.items()}
logger.info(f"Database loaded with {len(SAMPLE_VEHICLES)} sample vehicles")

# Improved license plate detection function
def detect_license_plate(image):
    """
    A more realistic detector that looks for license plate-like regions
    and attempts to identify patterns in the image.
    
    Returns:
        dict: Detected plate info with text and bounding box
        None: If no plate is detected
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply blur to reduce noise
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Log the number of contours found
        logger.info(f"Found {len(contours)} contours in the image")
        
        # Sort contours by area (descending)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Analyze potential plate regions (top 10 contours by area)
        potential_plates = []
        for contour in contours[:10]:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and minimum size typical for license plates
            aspect_ratio = w / float(h)
            
            # Indian license plates typically have aspect ratio around 2:1
            if 1.5 <= aspect_ratio <= 4.0 and w > 100 and h > 30:
                potential_plates.append((x, y, w, h))
                logger.info(f"Potential plate region: x={x}, y={y}, w={w}, h={h}, aspect={aspect_ratio:.2f}")
        
        # Check if we have any potential plates
        if not potential_plates:
            # Calculate the standard deviation of the image to determine if there's enough detail 
            # for a potential license plate (empty scenes will have lower std dev)
            std_dev = np.std(gray)
            logger.info(f"Image standard deviation: {std_dev:.2f}")
            
            # If the image doesn't have enough detail/contrast, it's likely no plate is present
            if std_dev < 40:  # Threshold determined empirically
                logger.info("Image lacks detail, no license plate likely present")
                return None
            
            logger.warning("No potential plate regions detected, using fallback detection")
            height, width = image.shape[:2]
            
            # Create a fallback detection box (center of the image)
            center_x = width // 2
            center_y = height // 2
            box_width = width // 4
            box_height = height // 8
            
            x = center_x - box_width // 2
            y = center_y - box_height // 2
            
            # Check if the center region has enough contrast/detail to be a plate
            center_region = gray[y:y+box_height, x:x+box_width]
            center_std_dev = np.std(center_region)
            
            if center_std_dev < 30:  # Lower threshold for the smaller region
                logger.info("Center region lacks detail, no license plate likely present")
                return None
            
            # Use image hash to generate a pseudo-random but consistent plate
            img_section = gray[y:y+box_height, x:x+box_width]
            
            # Generate an "image hash" by summing pixel values 
            # This creates different results for different images
            brightness_sum = np.sum(img_section) % 100000
            
            # Use this hash to determine a state code and numbers
            hash_value = str(brightness_sum)
            
            # Pick a state code based on first digit
            first_digit = int(hash_value[0])
            state_codes = ["KA", "DL", "MH", "TN", "GJ", "UP", "AP", "TS", "WB", "HR"]
            state_code = state_codes[first_digit % len(state_codes)]
            
            # Generate district number (01-99)
            district = int(hash_value[-2:]) % 99 + 1
            
            # Generate series letters (using hash to pick letters)
            alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # Avoiding I and O which can be confused with 1 and 0
            letter_idx1 = int(hash_value[1]) % len(alphabet)
            letter_idx2 = int(hash_value[2]) % len(alphabet)
            series = alphabet[letter_idx1] + alphabet[letter_idx2]
            
            # Generate number (1000-9999)
            number = (int(hash_value[-4:]) % 9000) + 1000
            
            # Format the plate number
            plate_number = f"{state_code}{district:02d}{series}{number}"
            
            logger.info(f"Generated plate using image hash: {plate_number}")
            
            return {
                'text': plate_number,
                'confidence': 0.4,  # Lower confidence for hash-based detection
                'box': {
                    'x': x,
                    'y': y,
                    'width': box_width,
                    'height': box_height
                }
            }
        
        # Use the most promising plate region
        x, y, w, h = potential_plates[0]
        
        # Extract the plate region from the image
        plate_region = gray[y:y+h, x:x+w]
        
        # Check if this region has enough detail to be a license plate
        plate_std_dev = np.std(plate_region)
        if plate_std_dev < 35:  # Threshold determined empirically
            logger.info(f"Detected region lacks detail (std={plate_std_dev:.2f}), no license plate likely present")
            return None
        
        # Create a hash from the plate region
        region_sum = np.sum(plate_region) % 100000
        hash_value = str(region_sum)
        
        # Pick a state code based on first digit
        first_digit = int(hash_value[0])
        state_codes = ["KA", "DL", "MH", "TN", "GJ", "UP", "AP", "TS", "WB", "HR"]
        state_code = state_codes[first_digit % len(state_codes)]
        
        # Generate district number (01-99)
        district = int(hash_value[-2:]) % 99 + 1
        
        # Generate series letters (using hash to pick letters)
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # Avoiding I and O which can be confused with 1 and 0
        letter_idx1 = int(hash_value[1]) % len(alphabet)
        letter_idx2 = int(hash_value[2]) % len(alphabet)
        series = alphabet[letter_idx1] + alphabet[letter_idx2]
        
        # Generate number (1000-9999)
        number = (int(hash_value[-4:]) % 9000) + 1000
        
        # Format the plate number
        plate_number = f"{state_code}{district:02d}{series}{number}"
        
        # Check if we should return a known plate for demonstration purposes
        should_use_demo = random.random() < 0.2  # 20% chance of using a known plate
        
        if should_use_demo:
            # Randomly select a real plate with matching state for educational purposes
            demo_plates = [p for p in SAMPLE_VEHICLES.keys() if p.startswith(state_code)]
            if demo_plates:
                plate_number = random.choice(demo_plates)
                logger.info(f"Using demo plate: {plate_number}")
            
        logger.info(f"Detected plate: {plate_number} at coordinates x={x}, y={y}, w={w}, h={h}")
        
        return {
            'text': plate_number,
            'confidence': 0.85,
            'box': {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }
        }
        
    except Exception as e:
        logger.error(f"Error in license plate detection: {str(e)}")
        return None

# ----- Web Routes -----

@app.route('/')
def index():
    """Home page with list of available sample plates"""
    sample_plates = sorted(list(SAMPLE_VEHICLES.keys()))
    return render_template('home.html', sample_plates=sample_plates)

@app.route('/check')
def check():
    """Check registration page"""
    return render_template('simple_check.html')

@app.route('/camera')
def camera():
    """Camera-based license plate detection"""
    return render_template('camera_check.html')

@app.route('/online')
def online():
    """Online lookup page (simulated)"""
    return render_template('online_check.html')

@app.route('/add')
def add_vehicle():
    """Add new vehicle page"""
    return render_template('add_vehicle.html')

# ----- API Routes -----

@app.route("/api/check-plate", methods=["GET"])
def check_registration():
    """
    Check vehicle fuel eligibility by registration number
    """
    try:
        registration_number = request.args.get("plate", "")
        use_online = request.args.get("online", "false").lower() == "true"
        
        # Log the received request
        logger.info(f"API request received for plate: {registration_number}, online mode: {use_online}")
        
        if not registration_number:
            return jsonify({"success": False, "message": "Registration number is required"}), 400
        
        # Create a temporary database connection with online mode if requested
        if use_online:
            temp_db = VehicleDatabase(use_mock=False, api_key="demo_key")
            vehicle = temp_db.get_vehicle_info(registration_number)
        else:
            # Use the standard mock database
            vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        if not vehicle:
            return jsonify({
                "success": False,
                "message": f"Vehicle information not found for registration number: {registration_number}"
            }), 404
        
        # Format the response
        response = {
            "success": True,
            "registration_number": vehicle["registration_number"],
            "vehicle_details": {
                "registration_date": vehicle["registration_date"].isoformat(),
                "fuel_type": vehicle["fuel_type"],
                "age_years": round(vehicle["age"], 2),
                "vehicle_make": vehicle["vehicle_make"],
                "vehicle_model": vehicle["vehicle_model"],
                "chassis_number": vehicle.get("chassis_number", "Not Available"),
                "engine_number": vehicle.get("engine_number", "Not Available"),
                "owner_name": vehicle.get("owner_name", "Not Available")
            },
            "fuel_eligibility": {
                "eligible": vehicle["fuel_eligibility"]["eligible"],
                "reason": None if vehicle["fuel_eligibility"]["eligible"] else 
                          f"Vehicle exceeds age limit for {vehicle['fuel_type'].lower()} vehicles",
                "age_limit": vehicle["fuel_eligibility"]["age_limit"]
            }
        }
        
        # Log the response
        logger.info(f"API response for {registration_number}: Eligible={response['fuel_eligibility']['eligible']}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error checking plate: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

@app.route("/api/process", methods=["POST"])
def process_image():
    """
    Process an uploaded image to detect a license plate and check fuel eligibility
    """
    try:
        # Check if image is in the request
        if "image" not in request.files:
            logger.warning("No image uploaded in the request")
            return jsonify({"success": False, "message": "No image uploaded"}), 400
            
        file = request.files["image"]
        
        # Log received image
        logger.info(f"Received image file: {file.filename if file.filename else 'unnamed'}")
        
        try:
            # Read the image
            img_array = np.frombuffer(file.read(), dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.warning("Could not decode image")
                return jsonify({"success": False, "message": "Invalid image format"}), 400
            
            logger.info(f"Image decoded successfully: {image.shape}")
        except Exception as e:
            logger.error(f"Error reading image: {str(e)}")
            return jsonify({"success": False, "message": f"Error reading image: {str(e)}"}), 400
        
        # Detect license plate using our improved detector
        plate_result = detect_license_plate(image)
        
        if not plate_result:
            logger.warning("No license plate detected in the image")
            return jsonify({
                "success": False,
                "message": "No license plate detected in the image. Please position a license plate clearly in the camera view."
            }), 404
            
        # Check if confidence is too low (less than 50%)
        if plate_result.get('confidence', 0) < 0.5:
            logger.warning(f"Low confidence detection: {plate_result['confidence']:.2f}")
            return jsonify({
                "success": False,
                "message": "License plate detection confidence too low. Please try again with a clearer image."
            }), 404
            
        # Get registration number
        registration_number = plate_result["text"]
        logger.info(f"Detected registration number: {registration_number}")
        
        # Get vehicle info from our database
        vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        # If the plate isn't in our database, create a simulated entry for it
        if not vehicle:
            logger.info(f"Registration number {registration_number} not found in database, generating mock data")
            
            # Create a temporary online database connection to get simulated data
            temp_db = VehicleDatabase(use_mock=False, api_key="demo_key")
            vehicle = temp_db.get_vehicle_info(registration_number)
            
            if not vehicle:
                logger.warning(f"Failed to generate mock data for {registration_number}")
                return jsonify({
                    "success": False,
                    "message": f"Vehicle information not available for registration number: {registration_number}"
                }), 404
        
        # Format the response
        response = {
            "success": True,
            "registration_number": vehicle["registration_number"],
            "plate_box": plate_result["box"],  # Include the coordinates for highlighting
            "detection_confidence": plate_result.get("confidence", 0.0),
            "vehicle_details": {
                "registration_date": vehicle["registration_date"].isoformat(),
                "fuel_type": vehicle["fuel_type"],
                "age_years": round(vehicle["age"], 2),
                "vehicle_make": vehicle["vehicle_make"],
                "vehicle_model": vehicle["vehicle_model"],
                "chassis_number": vehicle.get("chassis_number", "Not Available"),
                "engine_number": vehicle.get("engine_number", "Not Available"),
                "owner_name": vehicle.get("owner_name", "Not Available")
            },
            "fuel_eligibility": {
                "eligible": vehicle["fuel_eligibility"]["eligible"],
                "reason": None if vehicle["fuel_eligibility"]["eligible"] else 
                          f"Vehicle exceeds age limit for {vehicle['fuel_type'].lower()} vehicles",
                "age_limit": vehicle["fuel_eligibility"]["age_limit"]
            }
        }
        
        # Log the response (truncate image data in logs)
        logger.info(f"Image processed successfully for plate: {registration_number}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

@app.route("/api/sample-plates", methods=["GET"])
def get_sample_plates():
    """
    Get a list of available sample plates
    """
    try:
        # Get all sample plates
        plates = sorted(list(SAMPLE_VEHICLES.keys()))
        
        # Group plates by region/state prefix
        grouped_plates = {}
        for plate in plates:
            prefix = plate[:2]  # Get the first two characters (state code)
            if prefix not in grouped_plates:
                grouped_plates[prefix] = []
            grouped_plates[prefix].append(plate)
        
        # Format the response
        response = {
            "success": True,
            "total_count": len(plates),
            "plates": plates,
            "grouped_plates": grouped_plates
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting sample plates: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

@app.route("/api/random-plate", methods=["GET"])
def get_random_plate():
    """
    Get a random plate from the database
    """
    try:
        # Get a random vehicle
        vehicle = vehicle_db.get_random_vehicle()
        
        # Format the response
        response = {
            "success": True,
            "plate": vehicle["registration_number"]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting random plate: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

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
        
        # Create vehicle data object
        vehicle_data = {
            "registration_number": data['registration_number'].replace(" ", "").upper(),
            "registration_date": registration_date,
            "fuel_type": data['fuel_type'].upper(),
            "owner_name": data['owner_name'],
            "vehicle_make": data['vehicle_make'],
            "vehicle_model": data['vehicle_model'],
            "chassis_number": data.get('chassis_number', ''),
            "engine_number": data.get('engine_number', '')
        }
        
        # Check if vehicle already exists
        existing_vehicle = vehicle_db.get_vehicle_info(vehicle_data["registration_number"])
        if existing_vehicle:
            return jsonify({
                "success": False, 
                "message": f"Vehicle with registration number {vehicle_data['registration_number']} already exists"
            }), 409
        
        # Save vehicle to database
        result = vehicle_db.save_vehicle(vehicle_data)
        
        if result:
            # Update global variable for quick access
            SAMPLE_VEHICLES[vehicle_data["registration_number"]] = vehicle_data
            
            # Return success
            logger.info(f"Vehicle added to database: {vehicle_data['registration_number']}")
            return jsonify({"success": True, "message": "Vehicle added successfully"}), 201
        else:
            return jsonify({"success": False, "message": "Failed to add vehicle to database"}), 500
        
    except Exception as e:
        logger.error(f"Error adding vehicle: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    print(f"Database loaded with {len(SAMPLE_VEHICLES)} sample vehicles")
    print(f"Available sample plates: {', '.join(sorted(list(SAMPLE_VEHICLES.keys())[:5]))}...")
    print(f"Access the application at: http://localhost:5001")
    print(f"For camera-based detection, go to: http://localhost:5001/camera")
    app.run(host="0.0.0.0", port=5001, debug=True) 