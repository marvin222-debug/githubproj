#!/usr/bin/env python3
"""
Final system test for ANPR with MongoDB Atlas
"""

import sys
import os
sys.path.append('.')

def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    try:
        from src.database.mongodb_atlas_db import MongoDBAtlasDatabase
        
        print("🔍 Testing MongoDB Atlas Connection...")
        db = MongoDBAtlasDatabase()
        
        # Test vehicle lookup
        test_plate = "KA02AB5678"
        vehicle = db.get_vehicle_info(test_plate)
        
        if vehicle:
            print(f"✅ SUCCESS: Found vehicle {vehicle.registration_number}")
            print(f"   Owner: {vehicle.owner_name}")
            print(f"   Make: {vehicle.vehicle_make} {vehicle.vehicle_model}")
            print(f"   Fuel: {vehicle.fuel_type}")
            print(f"   Age: {vehicle.age:.1f} years")
            print(f"   Eligible: {vehicle.is_eligible_for_fuel(10, 15)}")
            db.close()
            return True
        else:
            print(f"❌ FAILED: Vehicle {test_plate} not found")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_web_api():
    """Test web API"""
    try:
        import requests
        
        print("\n🌐 Testing Web API...")
        response = requests.get('http://localhost:5000/api/check-plate?plate=KA02AB5678', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ SUCCESS: API working correctly")
                print(f"   Vehicle: {data.get('registration_number')}")
                print(f"   Make: {data.get('vehicle_details', {}).get('make')}")
                print(f"   Fuel: {data.get('vehicle_details', {}).get('fuel_type')}")
                print(f"   Eligible: {data.get('fuel_eligibility', {}).get('eligible')}")
                return True
            else:
                print(f"❌ API Error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app not running")
        return False
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

def main():
    print("🚀 ANPR System Final Test")
    print("=" * 50)
    
    # Test MongoDB connection
    db_success = test_mongodb_connection()
    
    # Test Web API
    api_success = test_web_api()
    
    print("\n📊 Test Results:")
    print(f"   MongoDB Atlas: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"   Web API: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if db_success and api_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your ANPR system is working correctly with MongoDB Atlas")
        print("✅ You can now test vehicle lookup in the web interface")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    return db_success and api_success

if __name__ == "__main__":
    main()
