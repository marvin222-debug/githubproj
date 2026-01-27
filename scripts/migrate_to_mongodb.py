#!/usr/bin/env python3
"""
Migration Script: CSV to MongoDB
This script migrates vehicle data from CSV to MongoDB
"""

import os
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.vehicle_db import VehicleDatabase
from database.csv_vehicle_db import CSVVehicleDatabase
from config.config import DB_URI, DB_NAME, CSV_FILE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataMigrator:
    """Class to handle data migration from CSV to MongoDB"""
    
    def __init__(self):
        self.csv_db = CSVVehicleDatabase(CSV_FILE_PATH)
        self.mongo_db = VehicleDatabase()
        
    def check_prerequisites(self):
        """Check if prerequisites are met for migration"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check CSV database
        if not self.csv_db.vehicles_data:
            logger.error("❌ CSV database is empty or not accessible")
            return False
        
        # Check MongoDB connection
        if not self.mongo_db.db:
            logger.error("❌ MongoDB connection failed")
            return False
        
        logger.info("✅ Prerequisites check passed")
        return True
    
    def backup_existing_data(self):
        """Backup existing MongoDB data before migration"""
        try:
            if not self.mongo_db.db:
                logger.warning("⚠️ MongoDB not available, skipping backup")
                return True
            
            # Count existing documents
            existing_count = self.mongo_db.db[DB_NAME].count_documents({})
            
            if existing_count > 0:
                # Create backup collection
                backup_collection = f"{DB_NAME}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Copy existing data to backup
                existing_data = list(self.mongo_db.db[DB_NAME].find({}))
                if existing_data:
                    self.mongo_db.db[backup_collection].insert_many(existing_data)
                    logger.info(f"✅ Backed up {len(existing_data)} documents to {backup_collection}")
                
                return True
            else:
                logger.info("ℹ️ No existing data to backup")
                return True
                
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def migrate_data(self):
        """Migrate data from CSV to MongoDB"""
        try:
            logger.info("🚀 Starting data migration...")
            
            # Get all vehicles from CSV
            csv_vehicles = self.csv_db.vehicles_data
            total_vehicles = len(csv_vehicles)
            
            if total_vehicles == 0:
                logger.warning("⚠️ No vehicles found in CSV database")
                return False
            
            logger.info(f"📊 Found {total_vehicles} vehicles in CSV database")
            
            # Clear existing MongoDB data
            self.mongo_db.db[DB_NAME].drop()
            logger.info("🗑️ Cleared existing MongoDB data")
            
            # Migrate vehicles in batches
            batch_size = 100
            migrated_count = 0
            
            for i, (reg_num, vehicle_data) in enumerate(csv_vehicles.items()):
                try:
                    # Prepare document for MongoDB
                    mongo_doc = self._prepare_mongo_document(vehicle_data)
                    
                    if mongo_doc:
                        # Insert into MongoDB
                        self.mongo_db.db[DB_NAME].insert_one(mongo_doc)
                        migrated_count += 1
                        
                        # Log progress
                        if (i + 1) % batch_size == 0:
                            logger.info(f"📈 Migrated {i + 1}/{total_vehicles} vehicles...")
                
                except Exception as e:
                    logger.error(f"❌ Failed to migrate vehicle {reg_num}: {e}")
                    continue
            
            logger.info(f"✅ Migration completed: {migrated_count}/{total_vehicles} vehicles migrated")
            return migrated_count > 0
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def _prepare_mongo_document(self, vehicle_data):
        """Prepare a vehicle document for MongoDB"""
        try:
            # Convert the vehicle data to MongoDB format
            mongo_doc = {
                "registration_number": vehicle_data.get('registration_number'),
                "registration_date": vehicle_data.get('registration_date'),
                "fuel_type": vehicle_data.get('fuel_type'),
                "owner_name": vehicle_data.get('owner_name'),
                "vehicle_make": vehicle_data.get('vehicle_make'),
                "vehicle_model": vehicle_data.get('vehicle_model'),
                "chassis_number": vehicle_data.get('chassis_number'),
                "engine_number": vehicle_data.get('engine_number'),
                "state": vehicle_data.get('state'),
                "district": vehicle_data.get('district'),
                "rto_office": vehicle_data.get('rto_office'),
                "vehicle_class": vehicle_data.get('vehicle_class'),
                "vehicle_category": vehicle_data.get('vehicle_category'),
                "manufacturing_year": vehicle_data.get('manufacturing_year'),
                "engine_capacity": vehicle_data.get('engine_capacity'),
                "seating_capacity": vehicle_data.get('seating_capacity'),
                "gross_vehicle_weight": vehicle_data.get('gross_vehicle_weight'),
                "unladen_weight": vehicle_data.get('unladen_weight'),
                "vehicle_color": vehicle_data.get('vehicle_color'),
                "norms": vehicle_data.get('norms'),
                "fitness_upto": vehicle_data.get('fitness_upto'),
                "insurance_upto": vehicle_data.get('insurance_upto'),
                "permit_upto": vehicle_data.get('permit_upto'),
                "tax_upto": vehicle_data.get('tax_upto'),
                "puc_upto": vehicle_data.get('puc_upto'),
                "rc_status": vehicle_data.get('rc_status'),
                "vehicle_status": vehicle_data.get('vehicle_status'),
                "migrated_at": datetime.now(),
                "last_updated": datetime.now()
            }
            
            return mongo_doc
            
        except Exception as e:
            logger.error(f"❌ Error preparing document: {e}")
            return None
    
    def verify_migration(self):
        """Verify that migration was successful"""
        try:
            logger.info("🔍 Verifying migration...")
            
            # Count documents in MongoDB
            mongo_count = self.mongo_db.db[DB_NAME].count_documents({})
            csv_count = len(self.csv_db.vehicles_data)
            
            logger.info(f"📊 CSV records: {csv_count}")
            logger.info(f"📊 MongoDB records: {mongo_count}")
            
            if mongo_count == csv_count:
                logger.info("✅ Migration verification successful")
                return True
            else:
                logger.error(f"❌ Migration verification failed: count mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting CSV to MongoDB migration...")
        logger.info("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Backup existing data
        if not self.backup_existing_data():
            logger.warning("⚠️ Backup failed, but continuing with migration...")
        
        # Migrate data
        if not self.migrate_data():
            logger.error("❌ Migration failed")
            return False
        
        # Verify migration
        if not self.verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 Migration completed successfully!")
        logger.info("📝 Next steps:")
        logger.info("1. Update your configuration to use MongoDB as primary database")
        logger.info("2. Test your ANPR application")
        logger.info("3. The system will now use MongoDB for all vehicle lookups")
        
        return True
    
    def close(self):
        """Close database connections"""
        if self.csv_db:
            self.csv_db.close()
        if self.mongo_db:
            self.mongo_db.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate vehicle data from CSV to MongoDB')
    parser.add_argument('--check-only', action='store_true', help='Only check prerequisites')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing migration')
    parser.add_argument('--backup-only', action='store_true', help='Only backup existing data')
    
    args = parser.parse_args()
    
    migrator = DataMigrator()
    
    try:
        if args.check_only:
            migrator.check_prerequisites()
        elif args.verify_only:
            migrator.verify_migration()
        elif args.backup_only:
            migrator.backup_existing_data()
        else:
            migrator.run_migration()
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        migrator.close()

if __name__ == "__main__":
    main()

