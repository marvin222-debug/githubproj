#!/usr/bin/env python3
"""
MongoDB Atlas Database Integration for ANPR System
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
import certifi
from src.models.vehicle import Vehicle

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for age restrictions
DIESEL_AGE_LIMIT = 10
PETROL_AGE_LIMIT = 15

class MongoDBAtlasDatabase:
    """MongoDB Atlas database integration for vehicle data"""
    
    def __init__(self):
        """Initialize MongoDB Atlas connection"""
        try:
            # Get connection details from environment
            self.db_uri = os.getenv('DB_URI', 'mongodb+srv://marvinraichur987_db_user:bgD5RKzToNX7zQDu@anprcluster.rwl9k7j.mongodb.net/?retryWrites=true&w=majority&appName=anprcluster')
            self.db_name = os.getenv('DB_NAME', 'mongodb')
            
            logger.info(f"Connecting to MongoDB Atlas: {self.db_uri[:50]}...")
            
            # Connect to MongoDB Atlas
            self.client = MongoClient(
                self.db_uri,
                serverSelectionTimeoutMS=10000,
                tls=True,
                tlsCAFile=certifi.where()
            )
            
            # Test connection
            self.client.server_info()
            logger.info("✅ MongoDB Atlas connection successful")
            
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db['vehicles']
            
            # Test database access
            count = self.collection.count_documents({})
            logger.info(f"✅ Database accessible with {count} vehicles")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
            raise e
    
    def get_vehicle_info(self, registration_number):
        """
        Get vehicle information from MongoDB Atlas
        
        Args:
            registration_number (str): Vehicle registration number
            
        Returns:
            Vehicle: Vehicle object or None if not found
        """
        try:
            # Normalize the registration number
            registration_number = registration_number.replace(" ", "").upper()
            
            logger.info(f"Looking up vehicle in MongoDB Atlas: {registration_number}")
            
            # Query MongoDB Atlas
            vehicle_data = self.collection.find_one({"registration_number": registration_number})
            
            if not vehicle_data:
                logger.warning(f"Vehicle not found in Atlas: {registration_number}")
                return None
            
            # Convert MongoDB document to Vehicle object
            vehicle = Vehicle(
                registration_number=vehicle_data["registration_number"],
                registration_date=vehicle_data["registration_date"],
                fuel_type=vehicle_data["fuel_type"],
                owner_name=vehicle_data.get("owner_name"),
                vehicle_make=vehicle_data.get("vehicle_make"),
                vehicle_model=vehicle_data.get("vehicle_model"),
                chassis_number=vehicle_data.get("chassis_number", ""),
                engine_number=vehicle_data.get("engine_number", "")
            )
            
            logger.info(f"✅ Vehicle found in Atlas: {vehicle.registration_number} ({vehicle.fuel_type}, Age: {vehicle.age:.1f} years)")
            
            return vehicle
            
        except Exception as e:
            logger.error(f"❌ Error getting vehicle info from Atlas: {e}")
            return None
    
    def search_vehicles(self, **filters):
        """
        Search vehicles with filters
        
        Args:
            **filters: Search filters (fuel_type, state, vehicle_make, etc.)
            
        Returns:
            list: List of vehicle documents
        """
        try:
            # Build MongoDB query
            query = {}
            for key, value in filters.items():
                if value:
                    query[key] = value
            
            logger.info(f"Searching vehicles with filters: {query}")
            
            # Execute query
            vehicles = list(self.collection.find(query))
            
            logger.info(f"Found {len(vehicles)} vehicles matching filters")
            
            return vehicles
            
        except Exception as e:
            logger.error(f"❌ Error searching vehicles: {e}")
            return []
    
    def get_vehicle_details(self, registration_number):
        """
        Get complete vehicle details from MongoDB Atlas
        
        Args:
            registration_number (str): Vehicle registration number
            
        Returns:
            dict: Complete vehicle details or None if not found
        """
        try:
            registration_number = registration_number.replace(" ", "").upper()
            
            vehicle_data = self.collection.find_one({"registration_number": registration_number})
            
            if not vehicle_data:
                return None
            
            # Calculate age and fuel eligibility
            current_date = datetime.now()
            if isinstance(vehicle_data.get('registration_date'), datetime):
                reg_date = vehicle_data['registration_date']
            else:
                reg_date = datetime.fromisoformat(vehicle_data['registration_date'])
            
            age = (current_date - reg_date).days / 365.25
            fuel_type = vehicle_data.get('fuel_type', '').upper()
            
            if fuel_type == "DIESEL":
                eligible = age <= DIESEL_AGE_LIMIT
                age_limit = DIESEL_AGE_LIMIT
            elif fuel_type == "PETROL":
                eligible = age <= PETROL_AGE_LIMIT
                age_limit = PETROL_AGE_LIMIT
            else:
                eligible = True
                age_limit = None
            
            # Add calculated fields
            vehicle_data['age'] = round(age, 2)
            vehicle_data['fuel_eligibility'] = {
                'eligible': eligible,
                'age_limit': age_limit,
                'reason': None if eligible else f"Vehicle exceeds age limit for {fuel_type.lower()} vehicles"
            }
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"❌ Error getting vehicle details: {e}")
            return None
    
    def get_statistics(self):
        """
        Get database statistics
        
        Returns:
            dict: Database statistics
        """
        try:
            total_vehicles = self.collection.count_documents({})
            fuel_types = self.collection.distinct("fuel_type")
            states = self.collection.distinct("state")
            vehicle_makes = self.collection.distinct("vehicle_make")
            
            return {
                'total_vehicles': total_vehicles,
                'fuel_types': fuel_types,
                'states': states,
                'vehicle_makes': vehicle_makes
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}

    def add_vehicle(self, vehicle: Vehicle) -> bool:
        """
        Add or update a vehicle document in MongoDB Atlas

        Args:
            vehicle: Vehicle domain object to persist

        Returns:
            bool: True if operation succeeded
        """
        try:
            if not hasattr(self, 'collection'):
                logger.error("MongoDB collection not initialized")
                return False

            # Prepare document for MongoDB
            doc = {
                "registration_number": vehicle.registration_number.replace(" ", "").upper(),
                "registration_date": vehicle.registration_date,
                "fuel_type": vehicle.fuel_type.upper() if vehicle.fuel_type else None,
                "owner_name": vehicle.owner_name,
                "vehicle_make": vehicle.vehicle_make,
                "vehicle_model": vehicle.vehicle_model,
                "chassis_number": getattr(vehicle, "chassis_number", ""),
                "engine_number": getattr(vehicle, "engine_number", "")
            }

            # Upsert by registration number to avoid duplicates
            res = self.collection.update_one(
                {"registration_number": doc["registration_number"]},
                {"$set": doc},
                upsert=True
            )

            logger.info(
                f"✅ Vehicle upserted in Atlas: {doc['registration_number']} (matched={res.matched_count}, modified={res.modified_count}, upserted_id={res.upserted_id})"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Error adding vehicle to Atlas: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("✅ MongoDB Atlas connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing MongoDB connection: {e}")

# Test the connection
if __name__ == "__main__":
    print("🚀 Testing MongoDB Atlas Database Connection")
    print("=" * 50)
    
    try:
        # Initialize database
        db = MongoDBAtlasDatabase()
        
        # Test vehicle lookup
        test_plate = "KA02AB5678"
        vehicle = db.get_vehicle_info(test_plate)
        
        if vehicle:
            print(f"✅ Test successful: Found {vehicle.registration_number}")
            print(f"   Owner: {vehicle.owner_name}")
            print(f"   Make: {vehicle.vehicle_make} {vehicle.vehicle_model}")
            print(f"   Fuel: {vehicle.fuel_type}")
            print(f"   Age: {vehicle.age:.1f} years")
            print(f"   Eligible: {vehicle.is_eligible_for_fuel(DIESEL_AGE_LIMIT, PETROL_AGE_LIMIT)}")
        else:
            print(f"❌ Test failed: Vehicle {test_plate} not found")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"   Total vehicles: {stats.get('total_vehicles', 0)}")
        print(f"   Fuel types: {stats.get('fuel_types', [])}")
        print(f"   States: {len(stats.get('states', []))}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

