#!/usr/bin/env python3
"""
Script to import vehicle data from CSV file to MongoDB
Run this script to populate MongoDB with vehicle data from vahan_data.csv
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoDBImporter:
    """Class to handle importing CSV data to MongoDB"""
    
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="anpr_database"):
        """
        Initialize MongoDB importer
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB: {self.mongo_uri}")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def import_csv_data(self, csv_file_path="data/vahan_data.csv"):
        """
        Import vehicle data from CSV file to MongoDB
        
        Args:
            csv_file_path: Path to the CSV file
        """
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            return False
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded {len(df)} records from CSV file")
            
            # Clear existing data
            self.db.vehicles.drop()
            logger.info("Cleared existing vehicle data")
            
            # Create index for faster lookups
            self.db.vehicles.create_index("registration_number", unique=True)
            self.db.vehicles.create_index("state")
            self.db.vehicles.create_index("fuel_type")
            self.db.vehicles.create_index("vehicle_make")
            logger.info("Created database indexes")
            
            # Convert DataFrame to list of dictionaries
            vehicles_data = []
            for _, row in df.iterrows():
                vehicle_doc = self._prepare_vehicle_document(row)
                if vehicle_doc:
                    vehicles_data.append(vehicle_doc)
            
            # Insert data in batches
            batch_size = 100
            for i in range(0, len(vehicles_data), batch_size):
                batch = vehicles_data[i:i + batch_size]
                result = self.db.vehicles.insert_many(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(result.inserted_ids)} records")
            
            logger.info(f"Successfully imported {len(vehicles_data)} vehicles to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def _prepare_vehicle_document(self, row):
        """
        Prepare a single vehicle document for MongoDB
        
        Args:
            row: Pandas Series row from CSV
            
        Returns:
            dict: Prepared vehicle document
        """
        try:
            # Parse registration date
            reg_date = None
            if pd.notna(row.get('registration_date')):
                reg_date = pd.to_datetime(row['registration_date']).to_pydatetime()
            
            # Parse other date fields
            fitness_upto = None
            if pd.notna(row.get('fitness_upto')):
                fitness_upto = pd.to_datetime(row['fitness_upto']).to_pydatetime()
            
            insurance_upto = None
            if pd.notna(row.get('insurance_upto')):
                insurance_upto = pd.to_datetime(row['insurance_upto']).to_pydatetime()
            
            permit_upto = None
            if pd.notna(row.get('permit_upto')):
                permit_upto = pd.to_datetime(row['permit_upto']).to_pydatetime()
            
            tax_upto = None
            if pd.notna(row.get('tax_upto')):
                tax_upto = pd.to_datetime(row['tax_upto']).to_pydatetime()
            
            puc_upto = None
            if pd.notna(row.get('puc_upto')):
                puc_upto = pd.to_datetime(row['puc_upto']).to_pydatetime()
            
            # Create vehicle document
            vehicle_doc = {
                "registration_number": str(row.get('registration_number', '')).strip().upper(),
                "registration_date": reg_date,
                "fuel_type": str(row.get('fuel_type', 'PETROL')).strip().upper(),
                "owner_name": str(row.get('owner_name', '')).strip() if pd.notna(row.get('owner_name')) else None,
                "vehicle_make": str(row.get('vehicle_make', '')).strip() if pd.notna(row.get('vehicle_make')) else None,
                "vehicle_model": str(row.get('vehicle_model', '')).strip() if pd.notna(row.get('vehicle_model')) else None,
                "chassis_number": str(row.get('chassis_number', '')).strip() if pd.notna(row.get('chassis_number')) else None,
                "engine_number": str(row.get('engine_number', '')).strip() if pd.notna(row.get('engine_number')) else None,
                "state": str(row.get('state', '')).strip() if pd.notna(row.get('state')) else None,
                "district": str(row.get('district', '')).strip() if pd.notna(row.get('district')) else None,
                "rto_office": str(row.get('rto_office', '')).strip() if pd.notna(row.get('rto_office')) else None,
                "vehicle_class": str(row.get('vehicle_class', '')).strip() if pd.notna(row.get('vehicle_class')) else None,
                "vehicle_category": str(row.get('vehicle_category', '')).strip() if pd.notna(row.get('vehicle_category')) else None,
                "manufacturing_year": int(row.get('manufacturing_year', 0)) if pd.notna(row.get('manufacturing_year')) else None,
                "engine_capacity": str(row.get('engine_capacity', '')).strip() if pd.notna(row.get('engine_capacity')) else None,
                "seating_capacity": int(row.get('seating_capacity', 0)) if pd.notna(row.get('seating_capacity')) else None,
                "gross_vehicle_weight": str(row.get('gross_vehicle_weight', '')).strip() if pd.notna(row.get('gross_vehicle_weight')) else None,
                "unladen_weight": str(row.get('unladen_weight', '')).strip() if pd.notna(row.get('unladen_weight')) else None,
                "vehicle_color": str(row.get('vehicle_color', '')).strip() if pd.notna(row.get('vehicle_color')) else None,
                "norms": str(row.get('norms', '')).strip() if pd.notna(row.get('norms')) else None,
                "fitness_upto": fitness_upto,
                "insurance_upto": insurance_upto,
                "permit_upto": permit_upto,
                "tax_upto": tax_upto,
                "puc_upto": puc_upto,
                "rc_status": str(row.get('rc_status', '')).strip() if pd.notna(row.get('rc_status')) else None,
                "vehicle_status": str(row.get('vehicle_status', '')).strip() if pd.notna(row.get('vehicle_status')) else None,
                "imported_at": datetime.now(),
                "last_updated": datetime.now()
            }
            
            return vehicle_doc
            
        except Exception as e:
            logger.error(f"Error preparing vehicle document: {e}")
            return None
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            total_vehicles = self.db.vehicles.count_documents({})
            
            # Count by fuel type
            fuel_types = list(self.db.vehicles.aggregate([
                {"$group": {"_id": "$fuel_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            
            # Count by state
            states = list(self.db.vehicles.aggregate([
                {"$group": {"_id": "$state", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            
            # Count by vehicle make
            makes = list(self.db.vehicles.aggregate([
                {"$group": {"_id": "$vehicle_make", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            
            return {
                "total_vehicles": total_vehicles,
                "fuel_types": fuel_types,
                "states": states,
                "vehicle_makes": makes
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

def main():
    """Main function to run the import process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import vehicle data from CSV to MongoDB')
    parser.add_argument('--csv-file', default='data/vahan_data.csv', help='Path to CSV file')
    parser.add_argument('--mongo-uri', default='mongodb://localhost:27017/', help='MongoDB connection URI')
    parser.add_argument('--db-name', default='anpr_database', help='Database name')
    parser.add_argument('--show-stats', action='store_true', help='Show database statistics after import')
    
    args = parser.parse_args()
    
    # Create importer
    importer = MongoDBImporter(args.mongo_uri, args.db_name)
    
    try:
        # Connect to MongoDB
        if not importer.connect():
            sys.exit(1)
        
        # Import data
        if importer.import_csv_data(args.csv_file):
            logger.info("✅ Data import completed successfully!")
            
            if args.show_stats:
                stats = importer.get_statistics()
                logger.info(f"📊 Database Statistics:")
                logger.info(f"   Total vehicles: {stats.get('total_vehicles', 0)}")
                logger.info(f"   Fuel types: {stats.get('fuel_types', [])}")
                logger.info(f"   States: {stats.get('states', [])}")
                logger.info(f"   Vehicle makes: {stats.get('vehicle_makes', [])}")
        else:
            logger.error("❌ Data import failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        importer.close()

if __name__ == "__main__":
    main()

