#!/usr/bin/env python3
"""
Quick MongoDB Atlas connection test
"""

def test_atlas_with_connection_string(connection_string):
    """Test MongoDB Atlas with provided connection string"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        print("🔍 Testing MongoDB Atlas Connection...")
        print(f"Connection String: {connection_string[:50]}...")
        
        # Test connection
        client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
        
        # Test server connection
        server_info = client.server_info()
        print("✅ MongoDB Atlas connection successful!")
        print(f"📊 Server version: {server_info['version']}")
        
        # Test database access
        db = client['anpr_database']
        collections = db.list_collection_names()
        print(f"✅ Database 'anpr_database' accessible!")
        print(f"📁 Available collections: {collections}")
        
        # Test basic operations
        test_collection = db['connection_test']
        test_doc = {"test": "atlas_connection", "timestamp": "2024-01-01"}
        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB Atlas connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Quick MongoDB Atlas Connection Test")
    print("=" * 50)
    
    # You can replace this with your actual connection string
    connection_string = "mongodb+srv://username:password@anpr-cluster.xxxxx.mongodb.net/"
    
    print("Please provide your actual Atlas connection string to test.")
    print("You can find it in MongoDB Atlas dashboard:")
    print("1. Go to your cluster")
    print("2. Click 'Connect'")
    print("3. Choose 'Connect your application'")
    print("4. Copy the connection string")
    print("\nThen replace the connection_string variable in this script.")

