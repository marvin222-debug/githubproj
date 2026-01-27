import csv
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd

from src.models.vehicle import Vehicle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVVehicleDatabase:
    """
    CSV-based vehicle database for reading vehicle information from vahan_data.csv
    """
    
    def __init__(self, csv_file_path: str = "data/vahan_data.csv"):
        """
        Initialize the CSV vehicle database
        
        Args:
            csv_file_path: Path to the CSV file containing vehicle data
        """
        self.csv_file_path = csv_file_path
        self.vehicles_data = {}
        self._load_csv_data()
        
    def _load_csv_data(self) -> bool:
        """
        Load vehicle data from CSV file into memory
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.csv_file_path):
                logger.warning(f"CSV file not found: {self.csv_file_path}")
                return False
                
            # Load CSV data using pandas for better performance
            df = pd.read_csv(self.csv_file_path)
            
            # Convert to dictionary for faster lookups
            for _, row in df.iterrows():
                registration_number = str(row.get('registration_number', '')).strip().upper()
                if registration_number:
                    # Parse registration date
                    reg_date = None
                    if 'registration_date' in row and pd.notna(row['registration_date']):
                        try:
                            reg_date = pd.to_datetime(row['registration_date']).to_pydatetime()
                        except:
                            logger.warning(f"Invalid date format for {registration_number}: {row['registration_date']}")
                            continue
                    
                    # Create vehicle data dictionary
                    vehicle_data = {
                        'registration_number': registration_number,
                        'registration_date': reg_date,
                        'fuel_type': str(row.get('fuel_type', 'PETROL')).strip().upper(),
                        'owner_name': str(row.get('owner_name', '')).strip() if pd.notna(row.get('owner_name')) else None,
                        'vehicle_make': str(row.get('vehicle_make', '')).strip() if pd.notna(row.get('vehicle_make')) else None,
                        'vehicle_model': str(row.get('vehicle_model', '')).strip() if pd.notna(row.get('vehicle_model')) else None,
                        'chassis_number': str(row.get('chassis_number', '')).strip() if pd.notna(row.get('chassis_number')) else None,
                        'engine_number': str(row.get('engine_number', '')).strip() if pd.notna(row.get('engine_number')) else None,
                        'state': str(row.get('state', '')).strip() if pd.notna(row.get('state')) else None,
                        'district': str(row.get('district', '')).strip() if pd.notna(row.get('district')) else None,
                        'rto_office': str(row.get('rto_office', '')).strip() if pd.notna(row.get('rto_office')) else None,
                        'vehicle_class': str(row.get('vehicle_class', '')).strip() if pd.notna(row.get('vehicle_class')) else None,
                        'vehicle_category': str(row.get('vehicle_category', '')).strip() if pd.notna(row.get('vehicle_category')) else None,
                        'manufacturing_year': int(row.get('manufacturing_year', 0)) if pd.notna(row.get('manufacturing_year')) else None,
                        'engine_capacity': str(row.get('engine_capacity', '')).strip() if pd.notna(row.get('engine_capacity')) else None,
                        'seating_capacity': int(row.get('seating_capacity', 0)) if pd.notna(row.get('seating_capacity')) else None,
                        'gross_vehicle_weight': str(row.get('gross_vehicle_weight', '')).strip() if pd.notna(row.get('gross_vehicle_weight')) else None,
                        'unladen_weight': str(row.get('unladen_weight', '')).strip() if pd.notna(row.get('unladen_weight')) else None,
                        'vehicle_color': str(row.get('vehicle_color', '')).strip() if pd.notna(row.get('vehicle_color')) else None,
                        'norms': str(row.get('norms', '')).strip() if pd.notna(row.get('norms')) else None,
                        'fitness_upto': pd.to_datetime(row['fitness_upto']).to_pydatetime() if pd.notna(row.get('fitness_upto')) else None,
                        'insurance_upto': pd.to_datetime(row['insurance_upto']).to_pydatetime() if pd.notna(row.get('insurance_upto')) else None,
                        'permit_upto': pd.to_datetime(row['permit_upto']).to_pydatetime() if pd.notna(row.get('permit_upto')) else None,
                        'tax_upto': pd.to_datetime(row['tax_upto']).to_pydatetime() if pd.notna(row.get('tax_upto')) else None,
                        'puc_upto': pd.to_datetime(row['puc_upto']).to_pydatetime() if pd.notna(row.get('puc_upto')) else None,
                        'rc_status': str(row.get('rc_status', '')).strip() if pd.notna(row.get('rc_status')) else None,
                        'vehicle_status': str(row.get('vehicle_status', '')).strip() if pd.notna(row.get('vehicle_status')) else None,
                        'last_updated': datetime.now()
                    }
                    
                    self.vehicles_data[registration_number] = vehicle_data
            
            logger.info(f"Loaded {len(self.vehicles_data)} vehicles from CSV file: {self.csv_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {str(e)}")
            return False
    
    def get_vehicle_info(self, registration_number: str) -> Optional[Vehicle]:
        """
        Get vehicle information by registration number
        
        Args:
            registration_number: Vehicle registration number
            
        Returns:
            Vehicle object or None if not found
        """
        # Normalize the registration number
        registration_number = registration_number.replace(" ", "").upper()
        
        try:
            # Check if vehicle exists in our data
            if registration_number not in self.vehicles_data:
                logger.warning(f"Vehicle not found: {registration_number}")
                return None
            
            vehicle_data = self.vehicles_data[registration_number]
            
            # Create Vehicle object
            vehicle = Vehicle(
                registration_number=vehicle_data['registration_number'],
                registration_date=vehicle_data['registration_date'],
                fuel_type=vehicle_data['fuel_type'],
                owner_name=vehicle_data.get('owner_name'),
                vehicle_make=vehicle_data.get('vehicle_make'),
                vehicle_model=vehicle_data.get('vehicle_model'),
                chassis_number=vehicle_data.get('chassis_number'),
                engine_number=vehicle_data.get('engine_number')
            )
            
            logger.info(f"Vehicle found: {registration_number}")
            return vehicle
            
        except Exception as e:
            logger.error(f"Error getting vehicle info: {str(e)}")
            return None
    
    def get_vehicle_details(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed vehicle information including all CSV fields
        
        Args:
            registration_number: Vehicle registration number
            
        Returns:
            Dict with detailed vehicle information or None if not found
        """
        # Normalize the registration number
        registration_number = registration_number.replace(" ", "").upper()
        
        try:
            if registration_number not in self.vehicles_data:
                logger.warning(f"Vehicle not found: {registration_number}")
                return None
            
            vehicle_data = self.vehicles_data[registration_number]
            
            # Calculate age
            age = 0
            if vehicle_data['registration_date']:
                today = datetime.now()
                delta = today - vehicle_data['registration_date']
                age = delta.days / 365.25
            
            # Check fuel eligibility
            fuel_type = vehicle_data['fuel_type'].upper()
            if fuel_type == "DIESEL":
                eligible = age <= 10  # 10 years limit for diesel
                age_limit = 10
            elif fuel_type == "PETROL":
                eligible = age <= 15  # 15 years limit for petrol
                age_limit = 15
            else:
                eligible = True  # Electric, CNG, etc. have no age limit
                age_limit = None
            
            # Return detailed information
            return {
                **vehicle_data,
                'age': age,
                'fuel_eligibility': {
                    'eligible': eligible,
                    'age_limit': age_limit
                }
            }
            
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
            results = []
            
            for reg_num, vehicle_data in self.vehicles_data.items():
                match = True
                
                for key, value in filters.items():
                    if key in vehicle_data:
                        if isinstance(value, str):
                            if vehicle_data[key] and value.upper() not in str(vehicle_data[key]).upper():
                                match = False
                                break
                        else:
                            if vehicle_data[key] != value:
                                match = False
                                break
                    else:
                        match = False
                        break
                
                if match:
                    results.append(vehicle_data)
            
            logger.info(f"Found {len(results)} vehicles matching filters: {filters}")
            return results
            
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
            total_vehicles = len(self.vehicles_data)
            
            # Count by fuel type
            fuel_types = {}
            for vehicle_data in self.vehicles_data.values():
                fuel_type = vehicle_data.get('fuel_type', 'UNKNOWN')
                fuel_types[fuel_type] = fuel_types.get(fuel_type, 0) + 1
            
            # Count by state
            states = {}
            for vehicle_data in self.vehicles_data.values():
                state = vehicle_data.get('state', 'UNKNOWN')
                states[state] = states.get(state, 0) + 1
            
            # Count by vehicle make
            makes = {}
            for vehicle_data in self.vehicles_data.values():
                make = vehicle_data.get('vehicle_make', 'UNKNOWN')
                makes[make] = makes.get(make, 0) + 1
            
            return {
                'total_vehicles': total_vehicles,
                'fuel_types': fuel_types,
                'states': states,
                'vehicle_makes': makes
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def reload_data(self) -> bool:
        """
        Reload data from CSV file
        
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        self.vehicles_data.clear()
        return self._load_csv_data()
    
    def close(self):
        """
        Close database connection (not needed for CSV database)
        """
        pass


