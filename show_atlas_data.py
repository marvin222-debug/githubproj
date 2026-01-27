#!/usr/bin/env python3
"""
Display all data in MongoDB Atlas database
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import json

def show_all_atlas_data():
    """Display comprehensive data from MongoDB Atlas"""
    try:
        # Connect to MongoDB Atlas
        connection_string = "mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster"
        client = MongoClient(connection_string)
        db = client['anpr_database']
        collection = db['vehicles']
        
        print("🚀 MongoDB Atlas Database - Complete Data Report")
        print("=" * 80)
        
        # Basic statistics
        total_count = collection.count_documents({})
        print(f"📊 Total Vehicles in Database: {total_count}")
        print(f"🗄️ Database: anpr_database")
        print(f"📁 Collection: vehicles")
        print(f"🌐 Cluster: anprcluster")
        
        # Get all vehicles
        all_vehicles = list(collection.find({}))
        
        print(f"\n📋 ALL VEHICLES IN YOUR ATLAS DATABASE:")
        print("=" * 80)
        
        for i, vehicle in enumerate(all_vehicles, 1):
            print(f"\n🚗 Vehicle #{i}:")
            print(f"   Registration: {vehicle['registration_number']}")
            print(f"   Owner: {vehicle['owner_name']}")
            print(f"   Make & Model: {vehicle['vehicle_make']} {vehicle['vehicle_model']}")
            print(f"   Fuel Type: {vehicle['fuel_type']}")
            print(f"   Registration Date: {vehicle['registration_date'].strftime('%Y-%m-%d')}")
            print(f"   State: {vehicle['state']}")
            print(f"   District: {vehicle['district']}")
            print(f"   Color: {vehicle['vehicle_color']}")
            print(f"   Manufacturing Year: {vehicle['manufacturing_year']}")
            print(f"   Engine Capacity: {vehicle['engine_capacity']}cc")
            print(f"   Seating Capacity: {vehicle['seating_capacity']}")
            print(f"   RC Status: {vehicle['rc_status']}")
            print(f"   Vehicle Status: {vehicle['vehicle_status']}")
            print(f"   Chassis: {vehicle['chassis_number']}")
            print(f"   Engine: {vehicle['engine_number']}")
            print(f"   RTO Office: {vehicle['rto_office']}")
            print(f"   Vehicle Class: {vehicle['vehicle_class']}")
            print(f"   Category: {vehicle['vehicle_category']}")
            print(f"   Norms: {vehicle['norms']}")
            print(f"   Fitness Upto: {vehicle['fitness_upto'].strftime('%Y-%m-%d')}")
            print(f"   Insurance Upto: {vehicle['insurance_upto'].strftime('%Y-%m-%d')}")
            print(f"   Permit Upto: {vehicle['permit_upto'].strftime('%Y-%m-%d')}")
            print(f"   Tax Upto: {vehicle['tax_upto'].strftime('%Y-%m-%d')}")
            print(f"   PUC Upto: {vehicle['puc_upto'].strftime('%Y-%m-%d')}")
            print(f"   Imported At: {vehicle['imported_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
        
        # Summary statistics
        print(f"\n📈 DATABASE SUMMARY STATISTICS:")
        print("=" * 50)
        
        # Fuel type distribution
        fuel_types = collection.distinct("fuel_type")
        print(f"⛽ Fuel Types ({len(fuel_types)}): {', '.join(fuel_types)}")
        for fuel in fuel_types:
            count = collection.count_documents({"fuel_type": fuel})
            print(f"   - {fuel}: {count} vehicles")
        
        # State distribution
        states = collection.distinct("state")
        print(f"\n🗺️ States ({len(states)}): {', '.join(states)}")
        for state in states:
            count = collection.count_documents({"state": state})
            print(f"   - {state}: {count} vehicles")
        
        # Vehicle make distribution
        makes = collection.distinct("vehicle_make")
        print(f"\n🚙 Vehicle Makes ({len(makes)}): {', '.join(makes)}")
        for make in makes:
            count = collection.count_documents({"vehicle_make": make})
            print(f"   - {make}: {count} vehicles")
        
        # Age analysis
        print(f"\n📅 Age Analysis:")
        current_year = datetime.now().year
        for vehicle in all_vehicles:
            age = current_year - vehicle['manufacturing_year']
            print(f"   - {vehicle['registration_number']}: {age} years old")
        
        # Status analysis
        active_rc = collection.count_documents({"rc_status": "Active"})
        active_vehicle = collection.count_documents({"vehicle_status": "Active"})
        print(f"\n✅ Status Analysis:")
        print(f"   - Active RC: {active_rc}/{total_count}")
        print(f"   - Active Vehicle: {active_vehicle}/{total_count}")
        
        # Recent registrations
        print(f"\n🆕 Recent Registrations (2020+):")
        recent_vehicles = collection.find({"manufacturing_year": {"$gte": 2020}})
        for vehicle in recent_vehicles:
            print(f"   - {vehicle['registration_number']}: {vehicle['vehicle_make']} {vehicle['vehicle_model']} ({vehicle['manufacturing_year']})")
        
        # Old vehicles
        print(f"\n🕰️ Old Vehicles (2010 and before):")
        old_vehicles = collection.find({"manufacturing_year": {"$lte": 2010}})
        for vehicle in old_vehicles:
            age = current_year - vehicle['manufacturing_year']
            print(f"   - {vehicle['registration_number']}: {vehicle['vehicle_make']} {vehicle['vehicle_model']} ({age} years old)")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error displaying data: {str(e)}")
        return False

if __name__ == "__main__":
    success = show_all_atlas_data()
    
    if success:
        print(f"\n🎉 Complete data report generated!")
        print(f"📱 You can also view this data in MongoDB Atlas web interface")
        print(f"🌐 Go to: https://cloud.mongodb.com/")
        print(f"📁 Navigate to: anprcluster → anpr_database → vehicles")
    else:
        print(f"\n❌ Failed to generate data report")

