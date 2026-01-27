import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Get connection string
connection_string = os.getenv('MONGODB_ATLAS_URI')
db_name = os.getenv('DB_NAME', 'anpr_database')

# Plate to search
plate_to_find = "DL07KL9988"

print(f"Connecting to Atlas...")

try:
    # Connect to MongoDB
    client = MongoClient(connection_string, tlsCAFile=certifi.where())
    db = client[db_name]
    collection = db['vehicles']

    print(f"Successfully connected to database '{db_name}' and collection 'vehicles'.")

    # Find the vehicle
    print(f"Searching for registration_number: '{plate_to_find}'")
    vehicle = collection.find_one({"registration_number": plate_to_find})

    if vehicle:
        print("\n--- VEHICLE FOUND ---")
        for key, value in vehicle.items():
            print(f"{key}: {value}")
        print("---------------------")
    else:
        print("\n--- VEHICLE NOT FOUND ---")
        print(f"No vehicle with registration number '{plate_to_find}' was found in the 'vehicles' collection.")

except Exception as e:
    print(f"\n--- AN ERROR OCCURRED ---")
    print(f"Error: {e}")

finally:
    if 'client' in locals() and client:
        client.close()
        print("\nConnection closed.")
