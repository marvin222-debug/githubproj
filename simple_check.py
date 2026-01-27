import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get connection details
db_uri = os.getenv('MONGODB_ATLAS_URI')
db_name = os.getenv('DB_NAME', 'anpr_database')

# Plate to check
plate_number = 'KA63MA6613'

try:
    print(f"Connecting to MongoDB Atlas...")
    client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    
    # Try exact match first
    vehicle = db.vehicles.find_one({"registration_number": plate_number})
    
    if not vehicle:
        # Try case-insensitive and ignore spaces
        vehicle = db.vehicles.find_one({
            "registration_number": {"$regex": f"^{plate_number.replace(' ', '\\s*')}$", "$options": "i"}
        })
    
    if vehicle:
        print("Vehicle found:")
        print(f"Registration: {vehicle.get('registration_number')}")
        print(f"Owner: {vehicle.get('owner_name')}")
        print(f"Make/Model: {vehicle.get('vehicle_make')} {vehicle.get('vehicle_model')}")
        print(f"Fuel Type: {vehicle.get('fuel_type')}")
    else:
        print(f"Vehicle with plate '{plate_number}' not found.")
        
        # List available plates for debugging
        print("\nSample plates in database:")
        for doc in db.vehicles.find({}, {"registration_number": 1, "_id": 0}).limit(5):
            print(f"- {doc.get('registration_number')}")
            
except Exception as e:
    print(f"Error: {e}")
    
    # Test basic connectivity
    try:
        client.admin.command('ping')
        print("MongoDB connection is working.")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        
finally:
    if 'client' in locals():
        client.close()
