import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Get connection string
connection_string = os.getenv('MONGODB_ATLAS_URI')
db_name = os.getenv('DB_NAME', 'anpr_database')

print(f"Connecting to Atlas to retrieve all vehicle plates...")

try:
    # Connect to MongoDB
    client = MongoClient(connection_string, tlsCAFile=certifi.where())
    db = client[db_name]
    collection = db['vehicles']

    print(f"Successfully connected to database '{db_name}' and collection 'vehicles'.")

    # Find all vehicles and project only the registration number
    all_vehicles = collection.find({}, {"registration_number": 1, "_id": 0})
    
    plates = [vehicle.get('registration_number') for vehicle in all_vehicles if vehicle.get('registration_number')]

    if plates:
        print("\n--- All Vehicle Registration Numbers in Atlas ---")
        for i, plate in enumerate(plates, 1):
            print(f"{i}. {plate}")
        print(f"\nTotal vehicles found: {len(plates)}")
        print("-------------------------------------------------")
    else:
        print("\n--- No Vehicles Found ---")
        print("The 'vehicles' collection is empty or does not contain any documents with a 'registration_number' field.")

except Exception as e:
    print(f"\n--- AN ERROR OCCURRED ---")
    print(f"Error: {e}")

finally:
    if 'client' in locals() and client:
        client.close()
        print("\nConnection closed.")
