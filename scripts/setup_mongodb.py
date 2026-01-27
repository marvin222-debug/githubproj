#!/usr/bin/env python3
"""
MongoDB Setup Script for ANPR System
This script helps set up MongoDB for the ANPR system
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.vehicle_db import VehicleDatabase
from config.config import DB_URI, DB_NAME, DB_COLLECTION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoDBSetup:
    """Class to handle MongoDB setup and configuration"""
    
    def __init__(self):
        self.db_uri = DB_URI
        self.db_name = DB_NAME
        self.collection_name = DB_COLLECTION
        
    def check_mongodb_installation(self):
        """Check if MongoDB is installed and running"""
        try:
            # Try to connect to MongoDB
            db = VehicleDatabase()
            if db.db:
                logger.info("✅ MongoDB is running and accessible")
                db.close()
                return True
            else:
                logger.error("❌ MongoDB connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            return False
    
    def install_mongodb_instructions(self):
        """Provide installation instructions for MongoDB"""
        system = platform.system().lower()
        
        logger.info("📋 MongoDB Installation Instructions:")
        logger.info("=" * 50)
        
        if system == "windows":
            logger.info("🪟 Windows:")
            logger.info("1. Download MongoDB Community Server from:")
            logger.info("   https://www.mongodb.com/try/download/community")
            logger.info("2. Run the installer and follow the setup wizard")
            logger.info("3. Add MongoDB to your PATH environment variable")
            logger.info("4. Start MongoDB service:")
            logger.info("   net start MongoDB")
            logger.info("   OR")
            logger.info("   mongod --dbpath C:\\data\\db")
            
        elif system == "linux":
            logger.info("🐧 Linux (Ubuntu/Debian):")
            logger.info("1. Import MongoDB public key:")
            logger.info("   wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -")
            logger.info("2. Add MongoDB repository:")
            logger.info("   echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list")
            logger.info("3. Update package database:")
            logger.info("   sudo apt-get update")
            logger.info("4. Install MongoDB:")
            logger.info("   sudo apt-get install -y mongodb-org")
            logger.info("5. Start MongoDB service:")
            logger.info("   sudo systemctl start mongod")
            logger.info("   sudo systemctl enable mongod")
            
        elif system == "darwin":
            logger.info("🍎 macOS:")
            logger.info("1. Install using Homebrew:")
            logger.info("   brew tap mongodb/brew")
            logger.info("   brew install mongodb-community")
            logger.info("2. Start MongoDB service:")
            logger.info("   brew services start mongodb/brew/mongodb-community")
            
        else:
            logger.info("❓ Other Operating System:")
            logger.info("Please visit https://docs.mongodb.com/manual/installation/ for installation instructions")
        
        logger.info("=" * 50)
    
    def create_database_structure(self):
        """Create the database structure and indexes"""
        try:
            db = VehicleDatabase()
            if not db.db:
                logger.error("❌ Cannot connect to MongoDB")
                return False
            
            # Create indexes
            collection = db.db[self.collection_name]
            
            # Create indexes for better performance
            indexes = [
                ("registration_number", 1),
                ("state", 1),
                ("fuel_type", 1),
                ("vehicle_make", 1),
                ("registration_date", 1)
            ]
            
            for field, direction in indexes:
                try:
                    collection.create_index([(field, direction)])
                    logger.info(f"✅ Created index on {field}")
                except Exception as e:
                    logger.warning(f"⚠️ Index on {field} may already exist: {e}")
            
            # Create compound indexes
            compound_indexes = [
                [("state", 1), ("fuel_type", 1)],
                [("vehicle_make", 1), ("vehicle_model", 1)],
                [("registration_date", 1), ("fuel_type", 1)]
            ]
            
            for compound_index in compound_indexes:
                try:
                    collection.create_index(compound_index)
                    logger.info(f"✅ Created compound index on {[field for field, _ in compound_index]}")
                except Exception as e:
                    logger.warning(f"⚠️ Compound index may already exist: {e}")
            
            logger.info("✅ Database structure created successfully")
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating database structure: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connection and basic operations"""
        try:
            db = VehicleDatabase()
            if not db.db:
                logger.error("❌ Cannot connect to MongoDB")
                return False
            
            # Test basic operations
            collection = db.db[self.collection_name]
            
            # Count documents
            count = collection.count_documents({})
            logger.info(f"📊 Total documents in database: {count}")
            
            # Test a simple query
            sample_doc = collection.find_one({})
            if sample_doc:
                logger.info(f"📄 Sample document: {sample_doc.get('registration_number', 'N/A')}")
            
            # Test statistics
            stats = db.get_statistics()
            logger.info(f"📈 Database statistics: {stats}")
            
            db.close()
            logger.info("✅ Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def setup_complete(self):
        """Complete setup process"""
        logger.info("🚀 Starting MongoDB setup for ANPR system...")
        logger.info("=" * 60)
        
        # Check MongoDB installation
        if not self.check_mongodb_installation():
            logger.error("❌ MongoDB is not running or not installed")
            self.install_mongodb_instructions()
            return False
        
        # Create database structure
        if not self.create_database_structure():
            logger.error("❌ Failed to create database structure")
            return False
        
        # Test database connection
        if not self.test_database_connection():
            logger.error("❌ Database connection test failed")
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 MongoDB setup completed successfully!")
        logger.info("📝 Next steps:")
        logger.info("1. Run the import script to load vehicle data:")
        logger.info("   python scripts/import_csv_to_mongodb.py")
        logger.info("2. Start your ANPR application")
        logger.info("3. The system will now use MongoDB as the primary database")
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup MongoDB for ANPR system')
    parser.add_argument('--check-only', action='store_true', help='Only check MongoDB installation')
    parser.add_argument('--create-structure', action='store_true', help='Only create database structure')
    parser.add_argument('--test-connection', action='store_true', help='Only test database connection')
    
    args = parser.parse_args()
    
    setup = MongoDBSetup()
    
    try:
        if args.check_only:
            setup.check_mongodb_installation()
        elif args.create_structure:
            setup.create_database_structure()
        elif args.test_connection:
            setup.test_database_connection()
        else:
            setup.setup_complete()
            
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
