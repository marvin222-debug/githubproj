#!/usr/bin/env python3
"""
Simple MongoDB Atlas Connection Test
"""
import sys
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Load environment variables
load_dotenv()

print("=" * 50)
print("MongoDB Atlas Connection Test")
print("=" * 50)

# Get URI from environment
uri = os.getenv('MONGODB_ATLAS_URI')
print(f"\n1. MongoDB URI configured: {'Yes' if uri else 'No'}")

if not uri:
    print("ERROR: MONGODB_ATLAS_URI not found in environment")
    sys.exit(1)

# Mask password in display
masked_uri = uri.split('@')[0].split(':')[0] + ':****@' + uri.split('@')[1] if '@' in uri else uri
print(f"   URI: {masked_uri}")

# Try to connect
try:
    print("\n2. Attempting to connect to MongoDB Atlas...")
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where()
    )
    
    # Test connection
    client.admin.command('ping')
    print("   Connection: SUCCESS")
    
    # Get database
    db = client['anpr_database']
    collection = db['vehicles']
    
    # Count vehicles
    count = collection.count_documents({})
    print(f"\n3. Database: anpr_database")
    print(f"   Collection: vehicles")
    print(f"   Total vehicles: {count}")
    
    # Get sample vehicle
    if count > 0:
        sample = collection.find_one()
        print(f"\n4. Sample vehicle:")
        print(f"   Registration: {sample.get('registration_number', 'N/A')}")
        print(f"   Owner: {sample.get('owner_name', 'N/A')}")
        print(f"   Fuel Type: {sample.get('fuel_type', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("MongoDB Atlas Connection: SUCCESSFUL")
    print("=" * 50)
    
    client.close()
    
except Exception as e:
    print(f"   Connection: FAILED")
    print(f"   Error: {str(e)}")
    print("\n" + "=" * 50)
    print("MongoDB Atlas Connection: FAILED")
    print("=" * 50)
    sys.exit(1)
