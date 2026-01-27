#!/usr/bin/env python3
"""
Verify MongoDB Atlas data import
"""

import pymongo
from pymongo import MongoClient

def verify_atlas_data():
    """Verify the data import to MongoDB Atlas"""
    try:
        # Connect to MongoDB Atlas
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        client = MongoClient(connection_string)
        db = client['anpr_database']
        collection = db['vehicles']
        
        print("🔍 Verifying MongoDB Atlas data...")
        
        # Count total vehicles
        total_count = collection.count_documents({})
        print(f"✅ Total vehicles in database: {total_count}")
        
        # Show sample vehicles
        print("\n📋 Sample vehicles:")
        sample_vehicles = list(collection.find({}, {"registration_number": 1, "vehicle_make": 1, "fuel_type": 1}).limit(10))
        for i, vehicle in enumerate(sample_vehicles, 1):
            print(f"  {i}. {vehicle['registration_number']}: {vehicle['vehicle_make']} ({vehicle['fuel_type']})")
        
        # Show statistics
        fuel_types = collection.distinct("fuel_type")
        states = collection.distinct("state")
        makes = collection.distinct("vehicle_make")
        
        print(f"\n📊 Database Statistics:")
        print(f"  - Fuel Types: {fuel_types}")
        print(f"  - States: {states}")
        print(f"  - Vehicle Makes: {makes}")
        
        # Test specific vehicles
        print(f"\n🔍 Testing specific vehicles:")
        test_plates = ["KA01MJ2023", "DL05AB1234", "MH02CD5678", "KA63MA6613"]
        for plate in test_plates:
            vehicle = collection.find_one({"registration_number": plate})
            if vehicle:
                print(f"  ✅ {plate}: {vehicle['vehicle_make']} {vehicle['vehicle_model']} ({vehicle['fuel_type']})")
            else:
                print(f"  ❌ {plate}: Not found")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 MongoDB Atlas Data Verification")
    print("=" * 50)
    
    success = verify_atlas_data()
    
    if success:
        print("\n🎉 Data verification completed successfully!")
    else:
        print("\n❌ Data verification failed")

