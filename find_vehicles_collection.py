import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def find_vehicles_collection():
    try:
        # Get connection string from environment
        uri = os.getenv('DB_URI')
        db_name = os.getenv('DB_NAME', 'anpr_database')
        
        if not uri:
            print("ERROR: DB_URI not found in .env file")
            return []
            
        # Connect to MongoDB Atlas
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Get the database
        db = client[db_name]
        
        # List all collections in the database
        collections = db.list_collection_names()
        print(f"\nFound {len(collections)} collections in database '{db_name}':")
        
        # Check each collection for vehicle data
        for collection_name in collections:
            collection = db[collection_name]
            # Try to find documents with registration_number field
            count = collection.count_documents({"registration_number": {"$exists": True}})
            if count > 0:
                print(f"\nFound {count} documents with vehicle data in collection: {collection_name}")
                # Get one sample document to show structure
                sample = collection.find_one({"registration_number": {"$exists": True}})
                print("Sample document structure:")
                for key in sample:
                    print(f"- {key}: {sample[key]}")
                
                # Get all registration numbers
                print("\nRegistration numbers in this collection:")
                for doc in collection.find({}, {"registration_number": 1, "_id": 0}):
                    print(f"- {doc['registration_number']}")
                
                return collection_name
        
        print("\nNo collections with vehicle data found.")
        return None
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("\n=== Searching for Vehicle Data in MongoDB Atlas ===")
    collection_name = find_vehicles_collection()
    
    if collection_name:
        print(f"\n✅ Found vehicle data in collection: {collection_name}")
    else:
        print("\n❌ No vehicle data found in any collection.")
    
    print("\n" + "="*50)
