import logging
import sys
import os
import time
import cv2
import argparse
from datetime import datetime

from src.capture.camera import Camera
from src.processing.plate_detector import PlateDetector
from src.processing.enhanced_plate_detector import EnhancedPlateDetector
# from src.processing.yolo_plate_detector import YOLOPlateDetector  # Disabled until PyTorch is installed
from src.database.vehicle_db import VehicleDatabase
from src.config.config import (
    DB_URI, DB_NAME, VAHAN_API_URL, VAHAN_API_KEY, TESSERACT_PATH,
    DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT, MIN_CONFIDENCE,
    CAMERA_SOURCE, IMAGE_WIDTH, IMAGE_HEIGHT
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('anpr_system.log')
    ]
)
logger = logging.getLogger(__name__)

def run_continuous_mode(camera, plate_detector, vehicle_db, live_preview=True, interval=2):
    """
    Run the ANPR system in continuous mode, capturing frames at regular intervals
    
    Args:
        camera: Camera object for capturing images
        plate_detector: PlateDetector object for license plate recognition
        vehicle_db: VehicleDatabase object for vehicle information lookup
        live_preview: Whether to show live camera preview
        interval: Interval between captures in seconds
    """
    logger.info("Starting continuous ANPR mode")
    
    last_process_time = 0
    last_plate = None
    
    try:
        while True:
            # Capture frame
            result = camera.capture_frame()
            if not result:
                logger.error("Failed to capture frame")
                time.sleep(1)
                continue
                
            _, frame = result
            
            # Show live preview
            if live_preview:
                # Draw a help text
                cv2.putText(
                    frame, 
                    "Press 'q' to quit, 's' to save current frame", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 0), 
                    2
                )
                
                # Display timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    frame, 
                    timestamp, 
                    (10, IMAGE_HEIGHT - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 255, 255), 
                    1
                )
                
                cv2.imshow("ANPR System", frame)
                
                # Check for key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("User requested exit")
                    break
                elif key == ord('s'):
                    # Save current frame
                    saved_path = camera.save_image(frame)
                    if saved_path:
                        logger.info(f"Manually saved frame to {saved_path}")
            
            # Process frame at regular intervals
            current_time = time.time()
            if current_time - last_process_time >= interval:
                last_process_time = current_time
                
                # Detect license plate
                plate_result = plate_detector.detect_and_read_plate(frame)
                
                if plate_result:
                    plate_text = plate_result["text"]
                    
                    # Skip if it's the same plate as last time (vehicle hasn't moved)
                    if plate_text == last_plate:
                        continue
                        
                    last_plate = plate_text
                    logger.info(f"Detected license plate: {plate_text}")
                    
                    # Save the frame with the detected plate
                    saved_path = camera.save_image(frame)
                    
                    # Get vehicle info
                    vehicle = vehicle_db.get_vehicle_info(plate_text)
                    
                    if vehicle:
                        # Check fuel eligibility
                        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
                        
                        vehicle_age = round(vehicle.age, 1)
                        age_limit = DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
                        
                        logger.info(f"Vehicle details: {vehicle.registration_number}, "
                                  f"Age: {vehicle_age} years, Fuel: {vehicle.fuel_type}")
                        
                        if eligible:
                            logger.info(f"FUEL ALLOWED: Vehicle is within age limit ({vehicle_age}/{age_limit} years)")
                            status_text = "ALLOWED"
                            color = (0, 255, 0)  # Green
                        else:
                            logger.info(f"FUEL DENIED: Vehicle exceeds age limit ({vehicle_age}/{age_limit} years)")
                            status_text = "DENIED"
                            color = (0, 0, 255)  # Red
                        
                        # Draw status on the frame if live preview is enabled
                        if live_preview:
                            # Draw plate text
                            cv2.putText(
                                frame, 
                                f"Plate: {plate_text}", 
                                (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.7, 
                                (255, 255, 0), 
                                2
                            )
                            
                            # Draw vehicle info
                            cv2.putText(
                                frame, 
                                f"Age: {vehicle_age} years, Fuel: {vehicle.fuel_type}", 
                                (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.7, 
                                (255, 255, 0), 
                                2
                            )
                            
                            # Draw status
                            cv2.putText(
                                frame, 
                                f"FUEL {status_text}", 
                                (10, 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.8, 
                                color, 
                                2
                            )
                            
                            # Update display
                            cv2.imshow("ANPR System", frame)
                    else:
                        logger.warning(f"Vehicle information not found for: {plate_text}")
                
            # Small delay to prevent high CPU usage
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting...")
    finally:
        # Clean up
        camera.close()
        if live_preview:
            cv2.destroyAllWindows()
        logger.info("ANPR system stopped")
        
def process_image_file(image_path, plate_detector, vehicle_db):
    """
    Process a single image file
    
    Args:
        image_path: Path to the image file
        plate_detector: PlateDetector object
        vehicle_db: VehicleDatabase object
    """
    logger.info(f"Processing image file: {image_path}")
    
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to read image: {image_path}")
        return
    
    # Detect and read license plate
    plate_result = plate_detector.detect_and_read_plate(image)
    
    if not plate_result:
        logger.warning("No license plate detected in the image")
        return
        
    # Get registration number
    registration_number = plate_result["text"]
    logger.info(f"Detected license plate: {registration_number}")
    
    # Get vehicle info
    vehicle = vehicle_db.get_vehicle_info(registration_number)
    
    if vehicle:
        # Check fuel eligibility
        eligible = vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)
        
        vehicle_age = round(vehicle.age, 1)
        age_limit = DIESEL_AGE_LIMIT if vehicle.fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
        
        logger.info(f"Vehicle details: {vehicle.registration_number}, "
                  f"Age: {vehicle_age} years, Fuel: {vehicle.fuel_type}")
        
        if eligible:
            logger.info(f"FUEL ALLOWED: Vehicle is within age limit ({vehicle_age}/{age_limit} years)")
        else:
            logger.info(f"FUEL DENIED: Vehicle exceeds age limit ({vehicle_age}/{age_limit} years)")
    else:
        logger.warning(f"Vehicle information not found for: {registration_number}")
        
def main():
    """
    Main entry point for the ANPR system
    """
    parser = argparse.ArgumentParser(description="Automatic Number Plate Recognition (ANPR) System")
    parser.add_argument("--image", "-i", help="Path to an image file to process")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run in continuous mode using camera")
    parser.add_argument("--no-preview", action="store_true", help="Disable live preview in continuous mode")
    parser.add_argument("--interval", type=float, default=2.0, help="Processing interval in seconds (continuous mode)")
    args = parser.parse_args()
    
    logger.info("Starting ANPR System")
    
    # Initialize components
    try:
        plate_detector = EnhancedPlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
        logger.info("Using enhanced plate detector with EasyOCR")
    except Exception as e:
        logger.warning(f"Enhanced detector failed, falling back to traditional: {e}")
        plate_detector = PlateDetector(tesseract_path=TESSERACT_PATH, min_confidence=MIN_CONFIDENCE)
    vehicle_db = VehicleDatabase(DB_URI, DB_NAME, VAHAN_API_URL, VAHAN_API_KEY)
    
    try:
        if args.image:
            # Process a single image file
            process_image_file(args.image, plate_detector, vehicle_db)
        elif args.continuous:
            # Run in continuous mode using camera
            camera = Camera(camera_source=CAMERA_SOURCE, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
            run_continuous_mode(
                camera, 
                plate_detector, 
                vehicle_db, 
                live_preview=(not args.no_preview),
                interval=args.interval
            )
        else:
            # If no mode specified, show help
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        if vehicle_db:
            vehicle_db.close()
            
if __name__ == "__main__":
    main() 