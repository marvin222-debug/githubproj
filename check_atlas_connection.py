import os
import sys
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_mongodb_connection():
    """Check MongoDB Atlas connection status"""
    try:
        # Get connection string from environment
        uri = os.getenv('MONGODB_ATLAS_URI')
        if not uri:
            logger.error("MONGODB_ATLAS_URI not found in .env file")
            return False
            
        logger.info(f"Attempting to connect to MongoDB Atlas: {uri.split('@')[-1]}")
        
        # Try to connect with a short timeout
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Ping the server to test connection
        client.admin.command('ping')
        
        # Get database info
        db_name = os.getenv('DB_NAME', 'anpr_database')
        db = client[db_name]
        
        # Get collection stats
        collections = db.list_collection_names()
        
        logger.info("✅ Successfully connected to MongoDB Atlas")
        logger.info(f"Database: {db_name}")
        logger.info(f"Collections ({len(collections)}): {', '.join(collections) if collections else 'None'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
        
        # Provide specific guidance based on error type
        if "timed out" in str(e):
            logger.error("  - Connection timed out. Check your internet connection and MongoDB Atlas whitelist settings.")
        elif "bad auth" in str(e).lower():
            logger.error("  - Authentication failed. Please check your MongoDB Atlas credentials.")
        elif "ServerSelectionTimeoutError" in str(e):
            logger.error("  - Could not connect to MongoDB Atlas. Check your internet connection and cluster status.")
        
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MongoDB Atlas Connection Test for ANPR Project")
    print("="*60)
    
    # Check if using MongoDB or fallback
    use_mongodb = os.getenv('USE_MONGODB', 'true').lower() == 'true'
    if not use_mongodb:
        print("\nℹ️  MongoDB is currently DISABLED in your configuration (USE_MONGODB=false)")
        print("The application is using the local CSV fallback instead.")
    else:
        print("\n[INFO] Checking MongoDB Atlas connection...")
        is_connected = check_mongodb_connection()
        
        if is_connected:
            print("\n[SUCCESS] MongoDB Atlas connection is ACTIVE and working properly!")
        else:
            print("\n[ERROR] MongoDB Atlas connection FAILED")
            print("\nTroubleshooting steps:")
            print("1. Check your internet connection")
            print("2. Verify your IP is whitelisted in MongoDB Atlas")
            print("3. Check if your cluster is running in MongoDB Atlas")
            print("4. Verify your connection string in .env file")
            print("\nTo use local CSV fallback instead, set USE_MONGODB=false in .env")
    
    print("\n" + "="*60 + "\n")
