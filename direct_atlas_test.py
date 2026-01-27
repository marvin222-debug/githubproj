#!/usr/bin/env python3
"""
Direct MongoDB Atlas connection test
"""

def test_direct_atlas_connection():
    """Test MongoDB Atlas connection directly with connection string"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        # Your actual connection string
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        db_name = "anpr_database"
        
        print("🔍 Testing MongoDB Atlas Connection...")
        print(f"Database URI: {connection_string[:50]}...")
        print(f"Database Name: {db_name}")
        
        # Test connection
        client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
        
        # Test server connection
        server_info = client.server_info()
        print("✅ MongoDB Atlas connection successful!")
        print(f"📊 Server version: {server_info['version']}")
        
        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"✅ Database '{db_name}' accessible!")
        print(f"📁 Available collections: {collections}")
        
        # Test basic operations
        test_collection = db['connection_test']
        test_doc = {"test": "atlas_connection", "timestamp": "2024-01-01", "project": "ANPR"}
        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB Atlas connection failed: {str(e)}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your Atlas cluster is running")
        print("2. Verify your database user credentials")
        print("3. Ensure your IP is whitelisted in Atlas")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    print("🚀 Direct MongoDB Atlas Connection Test")
    print("=" * 50)
    
    success = test_direct_atlas_connection()
    
    if success:
        print("\n🎉 MongoDB Atlas is ready for your ANPR project!")
        print("✅ You can now use MongoDB instead of mock data")
    else:
        print("\n❌ Please fix the connection issues and try again.")

