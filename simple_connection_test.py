import os
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    try:
        # Get connection string from environment
        uri = os.getenv('DB_URI')
        if not uri:
            print("ERROR: DB_URI not found in .env file")
            return False
            
        print(f"Attempting to connect to: {uri.split('@')[-1]}")
        
        # Try to connect with a short timeout
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Ping the server to test connection
        client.admin.command('ping')
        print("SUCCESS: Successfully connected to MongoDB Atlas")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB Atlas: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("\n=== Testing MongoDB Atlas Connection ===")
    success = test_connection()
    print("==================================\n")
    
    if not success:
        print("Troubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify your IP is whitelisted in MongoDB Atlas")
        print("3. Check if your cluster is running in MongoDB Atlas")
        print("4. Verify your connection string in .env file")
        print("5. Try using the connection string from MongoDB Atlas dashboard")
        print("\nTo use local CSV fallback instead, set USE_MONGODB=false in .env")
