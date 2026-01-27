import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def check_plate(plate_number):
    """Check if a plate exists in the database and return its details."""
    try:
        # Get connection details from environment
        db_uri = os.getenv('MONGODB_ATLAS_URI')
        db_name = os.getenv('DB_NAME', 'anpr_database')
        
        if not db_uri:
            print("Error: MONGODB_ATLAS_URI not found in .env file")
            return
            
        print(f"Connecting to MongoDB Atlas...")
        
        # Connect to MongoDB Atlas
        client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # Search for the plate (case-insensitive and ignoring spaces)
        query = {"registration_number": {"$regex": plate_number.replace(" ", ".*"), "$options": "i"}}
        vehicle = db.vehicles.find_one(query)
        
        if vehicle:
            print("✅ Vehicle found in database:")
            print(f"Registration: {vehicle.get('registration_number')}")
            print(f"Owner: {vehicle.get('owner_name')}")
            print(f"Make/Model: {vehicle.get('vehicle_make')} {vehicle.get('vehicle_model')}")
            print(f"Fuel Type: {vehicle.get('fuel_type')}")
            print(f"Registration Date: {vehicle.get('registration_date')}")
        else:
            print(f"❌ Vehicle with plate '{plate_number}' not found in the database.")
            print("\nAvailable plates in the database:")
            # List all plates for reference
            for doc in db.vehicles.find({}, {"registration_number": 1, "_id": 0}).limit(10):
                print(f"- {doc.get('registration_number')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    plate = input("Enter the number plate to check (e.g., KA63MA6613): ").strip().upper()
    check_plate(plate)
