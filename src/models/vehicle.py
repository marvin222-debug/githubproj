from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Vehicle:
    """
    Model class for vehicle data
    """
    registration_number: str
    registration_date: datetime
    fuel_type: str  # "PETROL" or "DIESEL"
    owner_name: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    # Optional regional fields present in Atlas docs
    state: Optional[str] = None
    district: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    
    @property
    def age(self) -> float:
        """
        Calculate the age of the vehicle in years
        """
        today = datetime.now()
        delta = today - self.registration_date
        return delta.days / 365.25
    
    def is_eligible_for_fuel(self, diesel_age_limit: int = 10, petrol_age_limit: int = 15) -> bool:
        """
        Check if vehicle is eligible for fuel based on age limits
        
        Args:
            diesel_age_limit: Maximum age for diesel vehicles in years
            petrol_age_limit: Maximum age for petrol vehicles in years
            
        Returns:
            bool: True if eligible, False otherwise
        """
        if self.fuel_type.upper() == "DIESEL":
            return self.age <= diesel_age_limit
        elif self.fuel_type.upper() == "PETROL":
            return self.age <= petrol_age_limit
        else:
            # For other fuel types (CNG, Electric, etc.), assume no age restriction
            return True 