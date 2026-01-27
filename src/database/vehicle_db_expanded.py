import json
import logging
import os
import random
from datetime import datetime, timedelta
import requests
from src.database.csv_vehicle_db import CSVVehicleDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for age restrictions
DIESEL_AGE_LIMIT = 10
PETROL_AGE_LIMIT = 15

class VehicleDatabase:
    """Class to handle vehicle database operations with expanded functionality"""
    
    def __init__(self, use_mock=True, api_key=None, csv_file_path="data/vahan_data.csv"):
        """
        Initialize the vehicle database
        
        Args:
            use_mock (bool): Whether to use mock data (True) or live API (False)
            api_key (str): API key for online data service (if use_mock is False)
            csv_file_path (str): Path to CSV file containing vehicle data
        """
        self.use_mock = use_mock
        self.api_key = api_key
        self.csv_file_path = csv_file_path
        
        # Initialize CSV database
        self.csv_db = CSVVehicleDatabase(csv_file_path)
        
        # Load sample vehicle data for fallback
        self.vehicles = self._load_mock_data()
        logger.info(f"Vehicle database initialized with CSV data and {len(self.vehicles)} mock records")

    def _load_mock_data(self):
        """Load sample vehicle data"""
        # Sample vehicle data with plate numbers from various states
        return {
            # Karnataka vehicles (KA)
            "KA01MJ2023": {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "chassis_number": "MALA851CMKM123456",
                "engine_number": "1ZZ1234567"
            },
            "KA02AB5678": {
                "registration_number": "KA02AB5678",
                "registration_date": datetime(2018, 6, 22),
                "fuel_type": "DIESEL",
                "owner_name": "Sarah Johnson",
                "vehicle_make": "Mahindra",
                "vehicle_model": "Scorpio",
                "chassis_number": "MA1VM2BVKJ5678901",
                "engine_number": "MHK7896543"
            },
            "KA03XY4321": {
                "registration_number": "KA03XY4321",
                "registration_date": datetime(2021, 3, 10),
                "fuel_type": "PETROL",
                "owner_name": "Vijay Kumar",
                "vehicle_make": "Maruti Suzuki",
                "vehicle_model": "Swift",
                "chassis_number": "MA3FXYZ76543219",
                "engine_number": "K12MN765432"
            },
            
            # Delhi vehicles (DL)
            "DL05AB1234": {
                "registration_number": "DL05AB1234",
                "registration_date": datetime(2010, 6, 10),
                "fuel_type": "DIESEL",
                "owner_name": "Jane Smith",
                "vehicle_make": "Honda",
                "vehicle_model": "City",
                "chassis_number": "MAKZZZ12345678",
                "engine_number": "R18Z12345678"
            },
            "DL01RT5566": {
                "registration_number": "DL01RT5566",
                "registration_date": datetime(2016, 11, 5),
                "fuel_type": "PETROL",
                "owner_name": "Arvind Sharma",
                "vehicle_make": "Hyundai",
                "vehicle_model": "i20",
                "chassis_number": "MALHT789012345",
                "engine_number": "G4LA123456"
            },
            "DL07KL9988": {
                "registration_number": "DL07KL9988",
                "registration_date": datetime(2009, 1, 30),
                "fuel_type": "DIESEL",
                "owner_name": "Priya Gupta",
                "vehicle_make": "Tata",
                "vehicle_model": "Safari",
                "chassis_number": "MAT623451234567",
                "engine_number": "TD2345678"
            },
            
            # Maharashtra vehicles (MH)
            "MH02CD5678": {
                "registration_number": "MH02CD5678",
                "registration_date": datetime(2008, 3, 22),
                "fuel_type": "PETROL",
                "owner_name": "Raj Kumar",
                "vehicle_make": "Maruti",
                "vehicle_model": "Swift",
                "chassis_number": "MA3EZD12345678",
                "engine_number": "K12MN987654"
            },
            "MH01AB7777": {
                "registration_number": "MH01AB7777",
                "registration_date": datetime(2020, 9, 14),
                "fuel_type": "PETROL",
                "owner_name": "Anil Kapoor",
                "vehicle_make": "Kia",
                "vehicle_model": "Seltos",
                "chassis_number": "MAKTE123456789",
                "engine_number": "G4FLKM12345"
            },
            "MH04FG2468": {
                "registration_number": "MH04FG2468",
                "registration_date": datetime(2013, 7, 8),
                "fuel_type": "DIESEL",
                "owner_name": "Neha Mehta",
                "vehicle_make": "Volkswagen",
                "vehicle_model": "Vento",
                "chassis_number": "WVWZZ12345678",
                "engine_number": "CJZA123456"
            },
            
            # Tamil Nadu vehicles (TN)
            "TN01TV1111": {
                "registration_number": "TN01TV1111",
                "registration_date": datetime(2022, 4, 18),
                "fuel_type": "ELECTRIC",
                "owner_name": "Ramesh Subramaniam",
                "vehicle_make": "Tata",
                "vehicle_model": "Nexon EV",
                "chassis_number": "MAT765432109876",
                "engine_number": "NA-ELECTRIC"
            },
            "TN07BJ3344": {
                "registration_number": "TN07BJ3344",
                "registration_date": datetime(2014, 12, 3),
                "fuel_type": "PETROL",
                "owner_name": "Lakshmi Narayan",
                "vehicle_make": "Ford",
                "vehicle_model": "EcoSport",
                "chassis_number": "MAJCS12345678",
                "engine_number": "DURATEC987654"
            },
            "TN10CF5522": {
                "registration_number": "TN10CF5522",
                "registration_date": datetime(2011, 5, 20),
                "fuel_type": "DIESEL",
                "owner_name": "Karthik Raja",
                "vehicle_make": "Toyota",
                "vehicle_model": "Innova",
                "chassis_number": "MBJ123456789012",
                "engine_number": "2KD1234567"
            },
            
            # Gujarat vehicles (GJ)
            "GJ01HZ9900": {
                "registration_number": "GJ01HZ9900",
                "registration_date": datetime(2019, 8, 11),
                "fuel_type": "CNG",
                "owner_name": "Hardik Patel",
                "vehicle_make": "Maruti Suzuki",
                "vehicle_model": "Ertiga",
                "chassis_number": "MA3ERFG12345678",
                "engine_number": "K15BS678901"
            },
            "GJ05MK8523": {
                "registration_number": "GJ05MK8523",
                "registration_date": datetime(2007, 2, 14),
                "fuel_type": "DIESEL",
                "owner_name": "Amit Shah",
                "vehicle_make": "Mahindra",
                "vehicle_model": "Bolero",
                "chassis_number": "MA1YV123456789",
                "engine_number": "MEC123456"
            }
        }
    
    def get_vehicle_info(self, registration_number):
        """
        Get vehicle information by registration number
        
        Args:
            registration_number (str): Registration number of the vehicle
            
        Returns:
            dict: Vehicle information or None if not found
        """
        # Normalize registration number
        registration_number = registration_number.replace(" ", "").upper()
        
        # Log the search
        logger.info(f"Looking up vehicle with registration number: {registration_number}")
        
        # First try CSV database
        vehicle_details = self.csv_db.get_vehicle_details(registration_number)
        if vehicle_details:
            logger.info(f"Vehicle found in CSV database: {registration_number}")
            return vehicle_details
        
        # If not in CSV database, check mock database
        if self.use_mock:
            vehicle_data = self.vehicles.get(registration_number)
            
            if not vehicle_data:
                logger.warning(f"Vehicle not found in mock database: {registration_number}")
                return None
                
            # Calculate age of the vehicle
            vehicle_age = self._calculate_age(vehicle_data["registration_date"])
            
            # Check if the vehicle is eligible for fuel
            eligible = self._check_eligibility(vehicle_data["fuel_type"], vehicle_age)
            
            # Return formatted vehicle information
            return {
                "registration_number": vehicle_data["registration_number"],
                "registration_date": vehicle_data["registration_date"],
                "fuel_type": vehicle_data["fuel_type"],
                "owner_name": vehicle_data.get("owner_name"),
                "vehicle_make": vehicle_data.get("vehicle_make"),
                "vehicle_model": vehicle_data.get("vehicle_model"),
                "chassis_number": vehicle_data.get("chassis_number"),
                "engine_number": vehicle_data.get("engine_number"),
                "age": vehicle_age,
                "fuel_eligibility": {
                    "eligible": eligible,
                    "age_limit": DIESEL_AGE_LIMIT if vehicle_data["fuel_type"].upper() == "DIESEL" else PETROL_AGE_LIMIT
                }
            }
        else:
            # Try to fetch from online source
            try:
                return self._fetch_online(registration_number)
            except Exception as e:
                logger.error(f"Error fetching vehicle information online: {str(e)}")
                return None
    
    def _calculate_age(self, registration_date):
        """Calculate the age of the vehicle in years"""
        today = datetime.now()
        delta = today - registration_date
        return delta.days / 365.25
    
    def _check_eligibility(self, fuel_type, age):
        """Check if the vehicle is eligible for fuel based on age limits"""
        fuel_type = fuel_type.upper()
        if fuel_type == "DIESEL":
            return age <= DIESEL_AGE_LIMIT
        elif fuel_type == "PETROL":
            return age <= PETROL_AGE_LIMIT
        elif fuel_type in ["ELECTRIC", "CNG"]:
            # Electric and CNG vehicles are always eligible
            return True
        else:
            # For unknown fuel types, assume eligibility
            return True
    
    def _fetch_online(self, registration_number):
        """
        Fetch vehicle information from online source
        
        In a real implementation, this would call an actual API
        For this demo, we'll simulate an API response
        """
        if not self.api_key:
            raise ValueError("API key is required for online fetching")
            
        logger.info(f"Fetching vehicle information online for: {registration_number}")
        
        # In a real implementation, you would make an API call like:
        # url = "https://api.vehicleinfo.com/v1/lookup"
        # params = {"registrationNumber": registration_number, "apiKey": self.api_key}
        # response = requests.get(url, params=params)
        # data = response.json()
        
        # For this demo, we'll simulate a response by generating random data
        # This simulates what you would do with a real API response
        
        # First, check if it matches a pattern we can generate data for
        valid_patterns = [
            {"prefix": "KA", "state": "Karnataka"},
            {"prefix": "DL", "state": "Delhi"},
            {"prefix": "MH", "state": "Maharashtra"},
            {"prefix": "TN", "state": "Tamil Nadu"},
            {"prefix": "GJ", "state": "Gujarat"},
            {"prefix": "UP", "state": "Uttar Pradesh"},
            {"prefix": "AP", "state": "Andhra Pradesh"},
            {"prefix": "TS", "state": "Telangana"},
            {"prefix": "WB", "state": "West Bengal"},
            {"prefix": "HR", "state": "Haryana"}
        ]
        
        state_info = None
        for pattern in valid_patterns:
            if registration_number.startswith(pattern["prefix"]):
                state_info = pattern
                break
        
        if not state_info:
            logger.warning(f"Unknown state prefix for registration number: {registration_number}")
            return None
            
        # Simulate random registration date between 2000 and 2023
        year = random.randint(2000, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Using 28 to avoid invalid dates
        registration_date = datetime(year, month, day)
        
        # Random fuel type weighted towards petrol and diesel
        fuel_types = ["PETROL", "PETROL", "DIESEL", "DIESEL", "CNG", "ELECTRIC"]
        fuel_type = random.choice(fuel_types)
        
        # Random vehicle make and model
        makes_models = [
            {"make": "Maruti Suzuki", "models": ["Swift", "Baleno", "Alto", "WagonR", "Ertiga"]},
            {"make": "Hyundai", "models": ["i10", "i20", "Creta", "Venue", "Verna"]},
            {"make": "Tata", "models": ["Nexon", "Tiago", "Harrier", "Altroz", "Safari"]},
            {"make": "Mahindra", "models": ["Scorpio", "XUV700", "Thar", "Bolero", "XUV300"]},
            {"make": "Honda", "models": ["City", "Amaze", "WR-V", "Jazz"]},
            {"make": "Toyota", "models": ["Innova", "Fortuner", "Glanza", "Urban Cruiser"]},
            {"make": "Kia", "models": ["Seltos", "Sonet", "Carens", "Carnival"]},
            {"make": "Volkswagen", "models": ["Polo", "Vento", "Taigun", "Virtus"]}
        ]
        
        make_model = random.choice(makes_models)
        make = make_model["make"]
        model = random.choice(make_model["models"])
        
        # Generate a random owner name
        first_names = ["Raj", "Priya", "Amit", "Neha", "Vikram", "Sunita", "Rahul", "Ananya", "Karthik", "Deepa"]
        last_names = ["Sharma", "Patel", "Kumar", "Singh", "Verma", "Gupta", "Reddy", "Nair", "Joshi", "Malhotra"]
        owner_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Generate random chassis and engine numbers
        chassis_prefix = "MA" + make[0] + model[0]
        chassis_number = chassis_prefix + ''.join(random.choices('0123456789ABCDEFGHJKLMNPRSTUVWXYZ', k=10))
        
        engine_prefix = model[0] + make[0]
        engine_number = engine_prefix + ''.join(random.choices('0123456789', k=8))
        
        # Calculate age
        age = self._calculate_age(registration_date)
        
        # Check eligibility
        eligible = self._check_eligibility(fuel_type, age)
        
        # Return formatted vehicle information
        return {
            "registration_number": registration_number,
            "registration_date": registration_date,
            "fuel_type": fuel_type,
            "owner_name": owner_name,
            "vehicle_make": make,
            "vehicle_model": model,
            "chassis_number": chassis_number,
            "engine_number": engine_number,
            "age": age,
            "state": state_info["state"],
            "fuel_eligibility": {
                "eligible": eligible,
                "age_limit": DIESEL_AGE_LIMIT if fuel_type.upper() == "DIESEL" else PETROL_AGE_LIMIT
            }
        }
    
    def get_random_vehicle(self):
        """Get a random vehicle from the database (useful for testing)"""
        registration_number = random.choice(list(self.vehicles.keys()))
        return self.get_vehicle_info(registration_number)
    
    def save_vehicle(self, vehicle_data):
        """
        Save vehicle information to the database
        
        Args:
            vehicle_data (dict): Vehicle information to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize registration number
            registration_number = vehicle_data["registration_number"].replace(" ", "").upper()
            
            # Update the vehicles dictionary
            self.vehicles[registration_number] = vehicle_data
            
            logger.info(f"Vehicle saved to database: {registration_number}")
            return True
        except Exception as e:
            logger.error(f"Error saving vehicle: {str(e)}")
            return False
    
    def get_vehicle_details(self, registration_number):
        """
        Get detailed vehicle information including all CSV fields
        
        Args:
            registration_number (str): Registration number of the vehicle
            
        Returns:
            dict: Detailed vehicle information or None if not found
        """
        return self.csv_db.get_vehicle_details(registration_number)
    
    def search_vehicles(self, **filters):
        """
        Search vehicles based on various filters
        
        Args:
            **filters: Filter criteria (e.g., fuel_type='DIESEL', state='Karnataka')
            
        Returns:
            list: List of matching vehicle records
        """
        return self.csv_db.search_vehicles(**filters)
    
    def get_statistics(self):
        """
        Get database statistics
        
        Returns:
            dict: Database statistics
        """
        return self.csv_db.get_statistics()
    
    def reload_csv_data(self):
        """
        Reload data from CSV file
        
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        return self.csv_db.reload_data()
    
    def close(self):
        """Close database connection"""
        self.csv_db.close() 