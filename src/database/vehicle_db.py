import requests
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.models.vehicle import Vehicle
from src.database.csv_vehicle_db import CSVVehicleDatabase
from config.config import DB_URI, DB_NAME, DB_COLLECTION, USE_MONGODB, USE_CSV_FALLBACK, CSV_FILE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VehicleDatabase:
    """
    Database connector for vehicle information
    """
    def __init__(self, db_uri: str = None, db_name: str = None, vahan_api_url: str = None, vahan_api_key: str = None, csv_file_path: str = None):
        """
        Initialize the database connector
        
        Args:
            db_uri: MongoDB connection URI (optional, uses config default)
            db_name: Database name (optional, uses config default)
            vahan_api_url: URL for the Vahan API
            vahan_api_key: API key for the Vahan API
            csv_file_path: Path to CSV file containing vehicle data (optional, uses config default)
        """
        self.db_uri = db_uri or DB_URI
        self.db_name = db_name or DB_NAME
        self.vahan_api_url = vahan_api_url
        self.vahan_api_key = vahan_api_key
        self.csv_file_path = csv_file_path or CSV_FILE_PATH
        self.client = None
        self.db = None
        
        # Initialize CSV database as fallback
        if USE_CSV_FALLBACK:
            self.csv_db = CSVVehicleDatabase(self.csv_file_path)
        else:
            self.csv_db = None
        
        # Connect to MongoDB if enabled
        if USE_MONGODB:
            self._connect()
        
    def _connect(self) -> bool:
        """
        Connect to the MongoDB database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.db_uri)
            self.db = self.client[self.db_name]
            # Create indexes for faster lookups
            self.db[DB_COLLECTION].create_index("registration_number", unique=True)
            self.db[DB_COLLECTION].create_index("state")
            self.db[DB_COLLECTION].create_index("fuel_type")
            self.db[DB_COLLECTION].create_index("vehicle_make")
            logger.info(f"Connected to database: {self.db_name}")
            return True
        except PyMongoError as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
            
    def get_vehicle_details(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed vehicle information including all fields
        
        Args:
            registration_number: Vehicle registration number
            
        Returns:
            Dict with detailed vehicle information or None if not found
        """
        # Normalize the registration number
        registration_number = registration_number.replace(" ", "").upper()
        
        try:
            # First try MongoDB if available
            if self.db:
                vehicle_doc = self.db[DB_COLLECTION].find_one({"registration_number": registration_number})
                
                if vehicle_doc:
                    # Calculate age
                    age = 0
                    if vehicle_doc.get('registration_date'):
                        today = datetime.now()
                        delta = today - vehicle_doc['registration_date']
                        age = delta.days / 365.25
                    
                    # Check fuel eligibility
                    fuel_type = vehicle_doc.get('fuel_type', '').upper()
                    if fuel_type == "DIESEL":
                        eligible = age <= 10
                        age_limit = 10
                    elif fuel_type == "PETROL":
                        eligible = age <= 15
                        age_limit = 15
                    else:
                        eligible = True
                        age_limit = None
                    
                    # Convert ObjectId to string for JSON serialization
                    vehicle_doc['_id'] = str(vehicle_doc['_id'])
                    
                    return {
                        **vehicle_doc,
                        'age': age,
                        'fuel_eligibility': {
                            'eligible': eligible,
                            'age_limit': age_limit
                        }
                    }
            
            # Fallback to CSV database
            if self.csv_db:
                return self.csv_db.get_vehicle_details(registration_number)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting vehicle details: {str(e)}")
            return None
    
    def search_vehicles(self, **filters) -> List[Dict[str, Any]]:
        """
        Search vehicles based on various filters
        
        Args:
            **filters: Filter criteria (e.g., fuel_type='DIESEL', state='Karnataka')
            
        Returns:
            List of matching vehicle records
        """
        try:
            # First try MongoDB if available
            if self.db:
                # Build MongoDB query
                query = {}
                for key, value in filters.items():
                    if isinstance(value, str):
                        query[key] = {"$regex": value, "$options": "i"}  # Case-insensitive search
                    else:
                        query[key] = value
                
                vehicles = list(self.db[DB_COLLECTION].find(query))
                
                # Convert ObjectId to string for JSON serialization
                for vehicle in vehicles:
                    vehicle['_id'] = str(vehicle['_id'])
                
                logger.info(f"Found {len(vehicles)} vehicles in MongoDB matching filters: {filters}")
                return vehicles
            
            # Fallback to CSV database
            if self.csv_db:
                return self.csv_db.search_vehicles(**filters)
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dict with database statistics
        """
        try:
            # First try MongoDB if available
            if self.db:
                total_vehicles = self.db[DB_COLLECTION].count_documents({})
                
                # Count by fuel type
                fuel_types = list(self.db[DB_COLLECTION].aggregate([
                    {"$group": {"_id": "$fuel_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                # Count by state
                states = list(self.db[DB_COLLECTION].aggregate([
                    {"$group": {"_id": "$state", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                # Count by vehicle make
                makes = list(self.db[DB_COLLECTION].aggregate([
                    {"$group": {"_id": "$vehicle_make", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                return {
                    "total_vehicles": total_vehicles,
                    "fuel_types": fuel_types,
                    "states": states,
                    "vehicle_makes": makes,
                    "database_type": "MongoDB"
                }
            
            # Fallback to CSV database
            if self.csv_db:
                stats = self.csv_db.get_statistics()
                stats["database_type"] = "CSV"
                return stats
            
            return {"database_type": "None", "total_vehicles": 0}
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {"database_type": "Error", "total_vehicles": 0}
    
    def reload_csv_data(self) -> bool:
        """
        Reload data from CSV file
        
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        return self.csv_db.reload_data()
    
    def close(self):
        """
        Close the database connection
        """
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
        if self.csv_db:
            self.csv_db.close()
            
    def _fetch_from_vahan_api(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch vehicle information from Vahan API
        
        Args:
            registration_number: Vehicle registration number
            
        Returns:
            Dict with vehicle information or None if not found
        """
        if not self.vahan_api_url or not self.vahan_api_key:
            logger.warning("Vahan API URL or key not configured")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.vahan_api_key}",
                "Content-Type": "application/json"
            }
            params = {"registrationNumber": registration_number}
            
            response = requests.get(self.vahan_api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data and "vehicleDetails" in data:
                    return data["vehicleDetails"]
                else:
                    logger.warning(f"No vehicle details found for {registration_number}")
                    return None
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching from Vahan API: {str(e)}")
            return None
            
    def _parse_vehicle_data(self, vehicle_data: Dict[str, Any]) -> Optional[Vehicle]:
        """
        Parse raw vehicle data into Vehicle object
        
        Args:
            vehicle_data: Raw vehicle data
            
        Returns:
            Vehicle object or None if parsing failed
        """
        try:
            # Parse registration date
            reg_date_str = vehicle_data.get("registrationDate", "")
            if reg_date_str:
                # Convert string date to datetime object (assuming YYYY-MM-DD format)
                reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
            else:
                logger.error("Missing registration date")
                return None
                
            # Create Vehicle object
            vehicle = Vehicle(
                registration_number=vehicle_data.get("registrationNumber", ""),
                registration_date=reg_date,
                fuel_type=vehicle_data.get("fuelType", ""),
                owner_name=vehicle_data.get("ownerName", ""),
                vehicle_make=vehicle_data.get("makerName", ""),
                vehicle_model=vehicle_data.get("modelName", "")
            )
            
            return vehicle
        except Exception as e:
            logger.error(f"Error parsing vehicle data: {str(e)}")
            return None
    
    def get_vehicle_info(self, registration_number: str) -> Optional[Vehicle]:
        """
        Get vehicle information by registration number
        
        Args:
            registration_number: Vehicle registration number
            
        Returns:
            Vehicle object or None if not found
        """
        # Normalize the registration number (remove spaces, convert to uppercase)
        registration_number = registration_number.replace(" ", "").upper()
        
        try:
            # First try MongoDB if available
            if self.db:
                vehicle_doc = self.db[DB_COLLECTION].find_one({"registration_number": registration_number})
                
                if vehicle_doc:
                    # Convert document to Vehicle object
                    vehicle = Vehicle(
                        registration_number=vehicle_doc["registration_number"],
                        registration_date=vehicle_doc["registration_date"],
                        fuel_type=vehicle_doc["fuel_type"],
                        owner_name=vehicle_doc.get("owner_name"),
                        vehicle_make=vehicle_doc.get("vehicle_make"),
                        vehicle_model=vehicle_doc.get("vehicle_model")
                    )
                    logger.info(f"Vehicle found in MongoDB: {registration_number}")
                    return vehicle
            
            # If not in MongoDB, try CSV database as fallback
            if self.csv_db:
                vehicle = self.csv_db.get_vehicle_info(registration_number)
                if vehicle:
                    logger.info(f"Vehicle found in CSV database: {registration_number}")
                    return vehicle
            
            # If not in any database, try to fetch from Vahan API
            logger.info(f"Vehicle not found in databases, trying Vahan API: {registration_number}")
            vehicle_data = self._fetch_from_vahan_api(registration_number)
            
            if vehicle_data:
                vehicle = self._parse_vehicle_data(vehicle_data)
                
                if vehicle:
                    # Save to MongoDB for future reference
                    if self.db:
                        self._save_vehicle(vehicle)
                    return vehicle
            
            logger.warning(f"Vehicle not found: {registration_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting vehicle info: {str(e)}")
            return None
            
    def _save_vehicle(self, vehicle: Vehicle) -> bool:
        """
        Save vehicle information to database
        
        Args:
            vehicle: Vehicle object
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Convert to dictionary for MongoDB
            vehicle_doc = {
                "registration_number": vehicle.registration_number,
                "registration_date": vehicle.registration_date,
                "fuel_type": vehicle.fuel_type,
                "owner_name": vehicle.owner_name,
                "vehicle_make": vehicle.vehicle_make,
                "vehicle_model": vehicle.vehicle_model,
                "last_updated": datetime.now()
            }
            
            # Insert with upsert (update if exists, insert if not)
            result = self.db[DB_COLLECTION].update_one(
                {"registration_number": vehicle.registration_number},
                {"$set": vehicle_doc},
                upsert=True
            )
            
            logger.info(f"Vehicle saved to database: {vehicle.registration_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vehicle to database: {str(e)}")
            return False 