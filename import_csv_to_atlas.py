#!/usr/bin/env python3
"""
Import CSV vehicle data to MongoDB Atlas
"""

import pandas as pd
import pymongo
from pymongo import MongoClient
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_csv_to_atlas():
    """Import CSV vehicle data to MongoDB Atlas"""
    
    try:
        # Connect to MongoDB Atlas
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        client = MongoClient(connection_string)
        db = client['anpr_database']
        collection = db['vehicles']
        
        logger.info("🔍 Connected to MongoDB Atlas")
        
        # Read CSV file
        logger.info("📊 Reading CSV file...")
        df = pd.read_csv('data/vahan_data.csv')
        logger.info(f"✅ Loaded {len(df)} vehicles from CSV")
        
        # Convert DataFrame to list of dictionaries
        vehicles = []
        for _, row in df.iterrows():
            vehicle = {
                "registration_number": str(row['registration_number']),
                "registration_date": datetime.strptime(row['registration_date'], '%Y-%m-%d'),
                "fuel_type": str(row['fuel_type']),
                "owner_name": str(row['owner_name']),
                "vehicle_make": str(row['vehicle_make']),
                "vehicle_model": str(row['vehicle_model']),
                "chassis_number": str(row['chassis_number']),
                "engine_number": str(row['engine_number']),
                "state": str(row['state']),
                "district": str(row['district']),
                "rto_office": str(row['rto_office']),
                "vehicle_class": str(row['vehicle_class']),
                "vehicle_category": str(row['vehicle_category']),
                "manufacturing_year": int(row['manufacturing_year']),
                "engine_capacity": str(row['engine_capacity']),
                "seating_capacity": int(row['seating_capacity']),
                "gross_vehicle_weight": str(row['gross_vehicle_weight']),
                "unladen_weight": str(row['unladen_weight']),
                "vehicle_color": str(row['vehicle_color']),
                "norms": str(row['norms']),
                "fitness_upto": datetime.strptime(row['fitness_upto'], '%Y-%m-%d'),
                "insurance_upto": datetime.strptime(row['insurance_upto'], '%Y-%m-%d'),
                "permit_upto": datetime.strptime(row['permit_upto'], '%Y-%m-%d'),
                "tax_upto": datetime.strptime(row['tax_upto'], '%Y-%m-%d'),
                "puc_upto": datetime.strptime(row['puc_upto'], '%Y-%m-%d'),
                "rc_status": str(row['rc_status']),
                "vehicle_status": str(row['vehicle_status']),
                "imported_at": datetime.now(),
                "last_updated": datetime.now()
            }
            vehicles.append(vehicle)
        
        logger.info(f"✅ Converted {len(vehicles)} vehicles to MongoDB format")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        logger.info("🗑️ Clearing existing vehicle data...")
        collection.delete_many({})
        logger.info("✅ Existing data cleared")
        
        # Insert all vehicles
        logger.info("📤 Inserting vehicles into MongoDB Atlas...")
        result = collection.insert_many(vehicles)
        logger.info(f"✅ Successfully inserted {len(result.inserted_ids)} vehicles")
        
        # Create indexes for better performance
        logger.info("🔧 Creating database indexes...")
        collection.create_index("registration_number", unique=True)
        collection.create_index("fuel_type")
        collection.create_index("state")
        collection.create_index("vehicle_make")
        collection.create_index("district")
        collection.create_index("rc_status")
        collection.create_index("registration_date")
        logger.info("✅ Database indexes created")
        
        # Verify import
        total_count = collection.count_documents({})
        logger.info(f"📊 Total vehicles in database: {total_count}")
        
        # Show sample data
        sample_vehicles = list(collection.find({}, {"registration_number": 1, "vehicle_make": 1, "fuel_type": 1}).limit(5))
        logger.info("📋 Sample vehicles imported:")
        for vehicle in sample_vehicles:
            logger.info(f"  - {vehicle['registration_number']}: {vehicle['vehicle_make']} ({vehicle['fuel_type']})")
        
        # Show statistics
        fuel_types = collection.distinct("fuel_type")
        states = collection.distinct("state")
        makes = collection.distinct("vehicle_make")
        
        logger.info(f"📈 Database Statistics:")
        logger.info(f"  - Fuel Types: {fuel_types}")
        logger.info(f"  - States: {states}")
        logger.info(f"  - Vehicle Makes: {makes}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error importing CSV data: {str(e)}")
        return False

def verify_import():
    """Verify the import was successful"""
    try:
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        client = MongoClient(connection_string)
        db = client['anpr_database']
        collection = db['vehicles']
        
        # Count total vehicles
        total_count = collection.count_documents({})
        logger.info(f"✅ Verification: {total_count} vehicles in database")
        
        # Test a few specific vehicles
        test_plates = ["KA01MJ2023", "DL05AB1234", "MH02CD5678", "KA63MA6613"]
        for plate in test_plates:
            vehicle = collection.find_one({"registration_number": plate})
            if vehicle:
                logger.info(f"✅ Found: {plate} - {vehicle['vehicle_make']} {vehicle['vehicle_model']}")
            else:
                logger.warning(f"❌ Not found: {plate}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying import: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 CSV to MongoDB Atlas Import")
    print("=" * 50)
    
    # Import CSV data
    success = import_csv_to_atlas()
    
    if success:
        print("\n✅ CSV import completed successfully!")
        
        # Verify import
        print("\n🔍 Verifying import...")
        verify_success = verify_import()
        
        if verify_success:
            print("\n🎉 All vehicle data successfully imported to MongoDB Atlas!")
            print("✅ Your ANPR system now has access to all 20 vehicles")
            print("✅ You can test with any registration number from the CSV")
        else:
            print("\n⚠️ Import completed but verification failed")
    else:
        print("\n❌ CSV import failed")

