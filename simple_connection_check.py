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
        print("❌ Error: DB_URI not found in .env file")
        exit(1)
    
    print(f"🔗 Attempting to connect to MongoDB Atlas: {db_uri.split('@')[-1]}")
    
    # Try to connect
    client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)  # 5 second timeout
    
    # The ping command is cheap and does not require auth
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas!")
    
    # List databases
    print("\n📂 Available databases:")
    for db in client.list_database_names():
        print(f"- {db}")
    
    # Try to access the configured database
    if db_name in client.list_database_names():
        print(f"\n✅ Database '{db_name}' exists!")
        db = client[db_name]
        
        # List collections in the database
        print(f"\n📋 Collections in '{db_name}':")
        for collection in db.list_collection_names():
            print(f"- {collection}")
    else:
        print(f"\n⚠️  Warning: Database '{db_name}' does not exist")
    
except pymongo.errors.ServerSelectionTimeoutError:
    print("❌ Error: Could not connect to MongoDB Atlas. Please check your internet connection and database URI.")
    print("If you're using a VPN, please ensure it's connected.")
    print("Also, verify that your IP is whitelisted in MongoDB Atlas Network Access.")
    
except pymongo.errors.ConfigurationError as e:
    print(f"❌ Error in MongoDB connection configuration: {str(e)}")
    print("Please check your DB_URI in the .env file.")
    
except Exception as e:
    print(f"❌ An unexpected error occurred: {str(e)}")
    
finally:
    if 'client' in locals():
        client.close()
        print("\n🔌 Connection closed.")
