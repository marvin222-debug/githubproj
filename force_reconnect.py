import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def force_reconnect():
    """Force a reconnection to MongoDB Atlas"""
    try:
        # Get connection details from environment
        db_uri = os.getenv('MONGODB_ATLAS_URI')
        db_name = os.getenv('DB_NAME', 'anpr_database')
        
        if not db_uri:
            logger.error("MONGODB_ATLAS_URI not found in .env file")
            return False
            
        logger.info(f"Attempting to connect to MongoDB Atlas: {db_uri.split('@')[-1]}")
        
        # Create a new connection
        client = MongoClient(
            db_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000
        )
        
        # Test the connection
        client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB Atlas")
        
        # Get database and collection
        db = client[db_name]
        collections = db.list_collection_names()
        
        logger.info(f"Database: {db_name}")
        logger.info(f"Collections: {', '.join(collections) if collections else 'None'}")
        
        # Test a sample query
        vehicles = db.vehicles.find().limit(1)
        vehicle_count = db.vehicles.count_documents({})
        
        logger.info(f"Total vehicles in database: {vehicle_count}")
        
        if vehicle_count > 0:
            logger.info("Sample vehicle:")
            for vehicle in vehicles:
                logger.info(vehicle)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MongoDB Atlas Connection Test & Reconnection")
    print("="*60)
    
    if force_reconnect():
        print("\n✅ Connection successful! The database should now be accessible in the web application.")
    else:
        print("\n❌ Failed to connect to MongoDB Atlas. Please check your internet connection and try again.")
    
    print("\nNote: You may need to restart the ANPR system for the changes to take effect.")
