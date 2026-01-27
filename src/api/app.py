from flask import Flask, request, jsonify
import logging
import os
import numpy as np
import cv2
from datetime import datetime

from src.capture.camera import Camera
from src.processing.plate_detector import PlateDetector
from src.database.vehicle_db import VehicleDatabase
from src.config.config import (
    DB_URI, DB_NAME, VAHAN_API_URL, VAHAN_API_KEY, TESSERACT_PATH,
    DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT, MIN_CONFIDENCE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize components
plate_detector = PlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
vehicle_db = VehicleDatabase(DB_URI, DB_NAME, VAHAN_API_URL, VAHAN_API_KEY)

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
        # Check if image is in the request
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
            
        file = request.files["image"]
        
        # Read the image
        img_array = np.frombuffer(file.read(), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({"error": "Invalid image format"}), 400
            
        # Detect and read license plate
        plate_result = plate_detector.detect_and_read_plate(image)
        
        if not plate_result:
            return jsonify({
                "success": False,
                "message": "No license plate detected in the image"
            }), 400
            
        # Get registration number
        registration_number = plate_result["text"]
        
        # Get vehicle info from database
        vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        if not vehicle:
            return jsonify({
                "success": False,
                "message": f"Vehicle information not found for registration number: {registration_number}"
            }), 404
            
        # Check fuel eligibility based on age
        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
        
        # Format the response
        response = {
            "success": True,
            "registration_number": vehicle.registration_number,
            "vehicle_details": {
                "registration_date": vehicle.registration_date.isoformat(),
                "fuel_type": vehicle.fuel_type,
                "age_years": round(vehicle.age, 2),
                "make": vehicle.vehicle_make,
                "model": vehicle.vehicle_model
            },
            "fuel_eligibility": {
                "eligible": eligible,
                "reason": None if eligible else f"Vehicle exceeds age limit for {vehicle.fuel_type.lower()} vehicles",
                "age_limit": DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route("/api/check-plate", methods=["GET"])
def check_registration():
    """
    Check vehicle fuel eligibility by registration number
    """
    try:
        registration_number = request.args.get("plate")
        
        if not registration_number:
            return jsonify({"error": "Registration number is required"}), 400
            
        # Get vehicle info from database
        vehicle = vehicle_db.get_vehicle_info(registration_number)
        
        if not vehicle:
            return jsonify({
                "success": False,
                "message": f"Vehicle information not found for registration number: {registration_number}"
            }), 404
            
        # Check fuel eligibility based on age
        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
        
        # Format the response
        response = {
            "success": True,
            "registration_number": vehicle.registration_number,
            "vehicle_details": {
                "registration_date": vehicle.registration_date.isoformat(),
                "fuel_type": vehicle.fuel_type,
                "age_years": round(vehicle.age, 2),
                "make": vehicle.vehicle_make,
                "model": vehicle.vehicle_model
            },
            "fuel_eligibility": {
                "eligible": eligible,
                "reason": None if eligible else f"Vehicle exceeds age limit for {vehicle.fuel_type.lower()} vehicles",
                "age_limit": DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error checking plate: {str(e)}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route("/api/vehicles", methods=["GET"])
def get_all_vehicles():
    """
    Get all vehicles with optional pagination and filtering
    """
    try:
        # Get query parameters
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        fuel_type = request.args.get("fuel_type")
        state = request.args.get("state")
        
        # Build filters
        filters = {}
        if fuel_type:
            filters["fuel_type"] = fuel_type.upper()
        if state:
            filters["state"] = state
        
        # Get vehicles from database
        vehicles = vehicle_db.search_vehicles(**filters)
        
        # Calculate pagination
        total = len(vehicles)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_vehicles = vehicles[start_idx:end_idx]
        
        # Format response
        response = {
            "success": True,
            "total_vehicles": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "vehicles": []
        }
        
        for vehicle in paginated_vehicles:
            # Calculate age and fuel eligibility
            from datetime import datetime
            if isinstance(vehicle.get('registration_date'), str):
                reg_date = datetime.fromisoformat(vehicle['registration_date'])
            else:
                reg_date = vehicle.get('registration_date', datetime.now())
            
            age = (datetime.now() - reg_date).days / 365.25
            fuel_type = vehicle.get('fuel_type', '').upper()
            
            if fuel_type == "DIESEL":
                eligible = age <= DIESEL_AGE_LIMIT
                age_limit = DIESEL_AGE_LIMIT
            elif fuel_type == "PETROL":
                eligible = age <= PETROL_AGE_LIMIT
                age_limit = PETROL_AGE_LIMIT
            else:
                eligible = True
                age_limit = None
            
            vehicle_info = {
                "registration_number": vehicle.get('registration_number'),
                "registration_date": reg_date.isoformat() if reg_date else None,
                "fuel_type": vehicle.get('fuel_type'),
                "owner_name": vehicle.get('owner_name'),
                "vehicle_make": vehicle.get('vehicle_make'),
                "vehicle_model": vehicle.get('vehicle_model'),
                "state": vehicle.get('state'),
                "district": vehicle.get('district'),
                "chassis_number": vehicle.get('chassis_number'),
                "engine_number": vehicle.get('engine_number'),
                "rc_status": vehicle.get('rc_status'),
                "age_years": round(age, 2),
                "fuel_eligibility": {
                    "eligible": eligible,
                    "age_limit": age_limit
                }
            }
            response["vehicles"].append(vehicle_info)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 