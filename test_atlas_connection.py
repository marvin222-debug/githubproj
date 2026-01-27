#!/usr/bin/env python3
"""
Test MongoDB Atlas connection for ANPR project
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_atlas_connection():
    """Test MongoDB Atlas connection"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        # Get connection details
        db_uri = os.getenv('DB_URI', 'mongodb+srv://username:password@anpr-cluster.xxxxx.mongodb.net/')
        db_name = os.getenv('DB_NAME', 'anpr_database')
        
        print("🔍 Testing MongoDB Atlas Connection...")
        print(f"Database URI: {db_uri}")
        print(f"Database Name: {db_name}")
        
        # Test connection
        client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)
        
        # Test server connection
        client.server_info()
        print("✅ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"✅ Database '{db_name}' accessible!")
        print(f"📁 Available collections: {collections}")
        
        # Test basic operations
        test_collection = db['test_connection']
        test_doc = {"test": "connection", "timestamp": "2024-01-01"}
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
        print("1. Check your connection string in .env file")
        print("2. Verify your Atlas cluster is running")
        print("3. Check your database user credentials")
        print("4. Ensure your IP is whitelisted in Atlas")
        return False

if __name__ == "__main__":
    print("🚀 ANPR MongoDB Atlas Connection Test")
    print("=" * 50)
    
    success = test_atlas_connection()
    
    if success:
        print("\n🎉 MongoDB Atlas is ready for your ANPR project!")
    else:
        print("\n❌ Please fix the connection issues and try again.")

