import os
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Get connection details from environment
    db_uri = os.getenv('DB_URI')
    db_name = os.getenv('DB_NAME', 'anpr_database')
    
    if not db_uri:
        print("Error: DB_URI not found in .env file")
        exit(1)
    
    print(f"Attempting to connect to MongoDB Atlas...")
    print(f"URI: {db_uri.split('@')[-1]}")
    
    # Try to connect with a timeout
    client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)
    
    # Test the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
    
    # List databases
    print("\nAvailable databases:")
    for db in client.list_database_names():
        print(f"- {db}")
    
    # Check if our database exists
    if db_name in client.list_database_names():
        print(f"\nDatabase '{db_name}' exists!")
        db = client[db_name]
        
        # List collections
        print(f"\nCollections in '{db_name}':")
        for collection in db.list_collection_names():
            print(f"- {collection}")
    else:
        print(f"\nWarning: Database '{db_name}' does not exist")
    
except pymongo.errors.ServerSelectionTimeoutError:
    print("Error: Could not connect to MongoDB Atlas. Please check:")
    print("1. Your internet connection")
    print("2. If you're using a VPN, ensure it's connected")
    print("3. Your IP is whitelisted in MongoDB Atlas Network Access")
    print("4. The database server is running and accessible")
    
except pymongo.errors.ConfigurationError as e:
    print(f"Error in MongoDB connection configuration: {str(e)}")
    print("Please check your DB_URI in the .env file.")
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    
finally:
    if 'client' in locals():
        client.close()
        print("\nConnection closed.")
