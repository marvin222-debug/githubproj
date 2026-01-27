import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_number_plates():
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
        
        # Get the database and collection
        db = client[db_name]
        collection = db['vehicles']  # Assuming the collection is named 'vehicles'
        
        # Find all documents and extract number plates
        vehicles = collection.find({}, {'number_plate': 1, '_id': 0})
        
        # Extract number plates
        number_plates = [v.get('number_plate') for v in vehicles if v.get('number_plate')]
        
        return number_plates
        
    except Exception as e:
        print(f"ERROR: Failed to fetch number plates: {str(e)}")
        return []
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("\n=== Fetching Number Plates from MongoDB Atlas ===")
    plates = get_number_plates()
    
    if plates:
        print("\nNumber Plates in the database:")
        for i, plate in enumerate(plates, 1):
            print(f"{i}. {plate}")
    else:
        print("\nNo number plates found in the database.")
    
    print("\n" + "="*50)
