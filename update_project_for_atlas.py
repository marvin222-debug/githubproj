#!/usr/bin/env python3
"""
Update ANPR project to use MongoDB Atlas
"""

import os
import shutil

def update_project_configuration():
    """Update project configuration to use MongoDB Atlas"""
    
    print("🔧 Updating ANPR project for MongoDB Atlas...")
    
    # Create a proper .env file
    env_content = """# MongoDB Atlas Configuration
DB_URI=mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster
DB_NAME=anpr_database

# Database Type Configuration
USE_MONGODB=true
USE_CSV_FALLBACK=true
CSV_FILE_PATH=data/vahan_data.csv

# Other configurations
API_PORT=5000
API_HOST=0.0.0.0
DIESEL_AGE_LIMIT=10
PETROL_AGE_LIMIT=15
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
VAHAN_API_URL=https://vahan.example.gov.in/api/vehicle
VAHAN_API_KEY=dummy_key
CAMERA_SOURCE=0
IMAGE_WIDTH=640
IMAGE_HEIGHT=480
MIN_CONFIDENCE=0.5
"""
    
    # Write .env file
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env file created with Atlas configuration")
    
    # Test the configuration
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        db_uri = os.getenv('DB_URI')
        db_name = os.getenv('DB_NAME')
        
        if db_uri and 'mongodb+srv://' in db_uri:
            print("✅ Environment variables loaded correctly")
            print(f"✅ Database URI: {db_uri[:50]}...")
            print(f"✅ Database Name: {db_name}")
            return True
        else:
            print("❌ Environment variables not loaded correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error loading environment: {e}")
        return False

def import_sample_data():
    """Import sample vehicle data to MongoDB Atlas"""
    try:
        import pymongo
        from pymongo import MongoClient
        from datetime import datetime
        
        print("\n📊 Importing sample vehicle data to MongoDB Atlas...")
        
        # Connect to Atlas
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        client = MongoClient(connection_string)
        db = client['anpr_database']
        collection = db['vehicles']
        
        # Sample vehicle data
        sample_vehicles = [
            {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "chassis_number": "MALA851CMKM123456",
                "engine_number": "1ZZ1234567",
                "state": "Karnataka",
                "district": "Bangalore Urban"
            },
            {
                "registration_number": "DL05AB1234",
                "registration_date": datetime(2010, 6, 10),
                "fuel_type": "DIESEL",
                "owner_name": "Jane Smith",
                "vehicle_make": "Honda",
                "vehicle_model": "City",
                "chassis_number": "MALA851CMKM123457",
                "engine_number": "1ZZ1234568",
                "state": "Delhi",
                "district": "Central Delhi"
            },
            {
                "registration_number": "MH02CD5678",
                "registration_date": datetime(2008, 3, 22),
                "fuel_type": "PETROL",
                "owner_name": "Raj Kumar",
                "vehicle_make": "Maruti",
                "vehicle_model": "Swift",
                "chassis_number": "MALA851CMKM123458",
                "engine_number": "1ZZ1234569",
                "state": "Maharashtra",
                "district": "Mumbai"
            },
            {
                "registration_number": "KA63MA6613",
                "registration_date": datetime(2020, 5, 15),
                "fuel_type": "PETROL",
                "owner_name": "Test User",
                "vehicle_make": "Hyundai",
                "vehicle_model": "i20",
                "chassis_number": "MALA851CMKM123459",
                "engine_number": "1ZZ1234570",
                "state": "Karnataka",
                "district": "Bangalore Urban"
            }
        ]
        
        # Insert sample data
        result = collection.insert_many(sample_vehicles)
        print(f"✅ Inserted {len(result.inserted_ids)} sample vehicles")
        
        # Create indexes for better performance
        collection.create_index("registration_number", unique=True)
        collection.create_index("fuel_type")
        collection.create_index("state")
        collection.create_index("vehicle_make")
        print("✅ Created database indexes")
        
        # Verify data
        count = collection.count_documents({})
        print(f"✅ Total vehicles in database: {count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ANPR Project MongoDB Atlas Configuration")
    print("=" * 60)
    
    # Update configuration
    config_success = update_project_configuration()
    
    if config_success:
        # Import sample data
        data_success = import_sample_data()
        
        if data_success:
            print("\n🎉 ANPR project is now configured with MongoDB Atlas!")
            print("✅ Configuration updated")
            print("✅ Sample data imported")
            print("✅ Ready to use MongoDB instead of mock data")
        else:
            print("\n⚠️ Configuration updated but data import failed")
    else:
        print("\n❌ Configuration update failed")

