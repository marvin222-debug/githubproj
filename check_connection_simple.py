from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

load_dotenv()

def check_atlas_connection():
    try:
        # Get connection string from environment
        uri = os.getenv('MONGODB_ATLAS_URI')
        if not uri:
            return "[ERROR] MONGODB_ATLAS_URI not found in .env file"
            
        print("[INFO] Attempting to connect to MongoDB Atlas...")
        print(f"[INFO] Connection string: {uri.split('@')[-1]}")
        
        # Try to connect with a short timeout
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Check if the server is available
        client.admin.command('ping')
        print("[SUCCESS] Connected to MongoDB Atlas")
        
        # Get database info
        db_name = os.getenv('DB_NAME', 'anpr_database')
        db = client[db_name]
        print(f"[INFO] Database: {db_name}")
        
        # List collections
        try:
            collections = db.list_collection_names()
            print(f"[INFO] Collections ({len(collections)}):")
            for col in collections:
                print(f"  - {col}")
        except Exception as e:
            print(f"[WARNING] Could not list collections: {str(e)}")
        
        return "[SUCCESS] Connection test completed"
        
    except Exception as e:
        error_msg = str(e)
        if "timed out" in error_msg:
            return "[ERROR] Connection timed out. Check your internet connection and MongoDB Atlas whitelist settings."
        elif "bad auth" in error_msg.lower():
            return "[ERROR] Authentication failed. Please check your MongoDB Atlas credentials."
        elif "ServerSelectionTimeoutError" in error_msg:
            return "[ERROR] Could not connect to MongoDB Atlas. Check your internet connection and cluster status."
        else:
            return f"[ERROR] Connection failed: {error_msg}"
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing MongoDB Atlas Connection")
    print("="*50)
    result = check_atlas_connection()
    print("\n" + "="*50)
    print(result)
    print("="*50 + "\n")
