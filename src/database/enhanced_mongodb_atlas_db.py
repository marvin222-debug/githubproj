#!/usr/bin/env python3
"""
Enhanced MongoDB Atlas Database with Persistent Connection
Improved version with better connection management and auto-reconnection
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from src.models.vehicle import Vehicle
from src.database.persistent_atlas_connection import get_persistent_connection

logger = logging.getLogger(__name__)

class EnhancedMongoDBAtlasDatabase:
    """
    Enhanced MongoDB Atlas database with persistent connection management
    """
    
    def __init__(self):
        """Initialize enhanced Atlas database"""
        self.connection = get_persistent_connection()
        
        # Initialize connection
        if not self.connection.connect():
            logger.error("❌ Failed to establish initial Atlas connection")
            raise ConnectionError("Could not connect to MongoDB Atlas")
        
        logger.info("✅ Enhanced MongoDB Atlas Database initialized")
    
    def get_vehicle_info(self, registration_number: str) -> Optional[Vehicle]:
        """
        Get vehicle information from Atlas with automatic reconnection
        """
        try:
            # Get raw document from persistent connection
            vehicle_doc = self.connection.get_vehicle_info(registration_number)
            
            if not vehicle_doc:
                return None
            
            # Handle registration_date conversion (string to datetime)
            reg_date_str = vehicle_doc.get('registration_date')
            reg_date = None
            if isinstance(reg_date_str, str):
                try:
                    from dateutil import parser
                    reg_date = parser.parse(reg_date_str)
                except Exception as e:
                    logger.error(f"❌ Failed to parse registration date string: '{reg_date_str}'. Error: {e}")
                    # Fallback to trying a specific format if parsing fails
                    try:
                        reg_date = datetime.strptime(reg_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logger.error(f"❌ Could not parse date with specific format either.")
                        # As a last resort, you could return None or handle the error appropriately
                        return None # Or raise an error
            elif isinstance(reg_date_str, datetime):
                reg_date = reg_date_str # Already a datetime object
            
            # Convert to Vehicle object
            vehicle = Vehicle(
                registration_number=vehicle_doc.get('registration_number'),
                registration_date=reg_date,
                fuel_type=vehicle_doc.get('fuel_type'),
                owner_name=vehicle_doc.get('owner_name'),
                vehicle_make=vehicle_doc.get('vehicle_make'),
                vehicle_model=vehicle_doc.get('vehicle_model'),
                state=vehicle_doc.get('state'),
                district=vehicle_doc.get('district'),
                chassis_number=vehicle_doc.get('chassis_number', ''),
                engine_number=vehicle_doc.get('engine_number', '')
            )
            
            logger.info(f"✅ Vehicle retrieved: {vehicle.registration_number}")
            return vehicle
            
        except Exception as e:
            logger.error(f"❌ Error retrieving vehicle: {e}")
            logger.exception("Full error details:")
            return None
    
    def add_vehicle(self, vehicle: Vehicle) -> bool:
        """
        Add vehicle to Atlas database with automatic reconnection
        """
        try:
            vehicle_data = {
                'registration_number': vehicle.registration_number,
                'registration_date': vehicle.registration_date,
                'fuel_type': vehicle.fuel_type,
                'owner_name': vehicle.owner_name,
                'vehicle_make': vehicle.vehicle_make,
                'vehicle_model': vehicle.vehicle_model,
                'state': getattr(vehicle, 'state', ''),
                'district': getattr(vehicle, 'district', ''),
                'chassis_number': getattr(vehicle, 'chassis_number', ''),
                'engine_number': getattr(vehicle, 'engine_number', ''),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            return self.connection.add_vehicle(vehicle_data)
            
        except Exception as e:
            logger.error(f"❌ Error adding vehicle: {e}")
            return False
    
    def search_vehicles(self, **filters) -> List[Dict]:
        """
        Search vehicles with filters and automatic reconnection
        """
        try:
            if not self.connection.is_connected:
                if not self.connection.connect():
                    return []
            
            # Build MongoDB query
            query = {}
            for key, value in filters.items():
                if key == "fuel_type":
                    query["fuel_type"] = value.upper()
                elif key == "state":
                    query["state"] = value
                elif key == "vehicle_make":
                    query["vehicle_make"] = {"$regex": value, "$options": "i"}
            
            # Execute query
            cursor = self.connection.collection.find(query).limit(100)
            results = list(cursor)
            
            logger.info(f"✅ Search completed: {len(results)} vehicles found")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def get_connection_status(self) -> Dict:
        """
        Get detailed connection status
        """
        return self.connection.get_connection_status()
    
    def force_reconnect(self) -> bool:
        """
        Force reconnection to Atlas
        """
        return self.connection.force_reconnect()
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics
        """
        try:
            if not self.connection.is_connected:
                return {"error": "Not connected"}
            
            # Get collection stats
            stats = self.connection.database.command("collStats", "vehicles")
            vehicle_count = self.connection.collection.count_documents({})
            
            return {
                "total_vehicles": vehicle_count,
                "collection_size": stats.get("size", 0),
                "storage_size": stats.get("storageSize", 0),
                "index_count": stats.get("nindexes", 0),
                "connection_status": self.get_connection_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Stats error: {e}")
            return {"error": str(e)}

    def list_plate_numbers(self, limit: int = 1000) -> List[str]:
        """
        Return a list of registration_number values from Atlas.
        """
        try:
            if not self.connection.is_connected:
                if not self.connection.connect():
                    return []

            cursor = self.connection.collection.find(
                {}, {"_id": 0, "registration_number": 1}
            ).limit(limit)
            plates = []
            for doc in cursor:
                reg = (doc.get("registration_number") or "").replace(" ", "").upper()
                if reg:
                    plates.append(reg)
            return plates
        except Exception as e:
            logger.error(f"❌ Error listing plate numbers: {e}")
            return []
    
    def close(self):
        """
        Close database connection
        """
        self.connection.close()
        logger.info("✅ Enhanced Atlas database closed")
