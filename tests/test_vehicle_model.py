import unittest
from datetime import datetime, timedelta
from src.models.vehicle import Vehicle

class TestVehicleModel(unittest.TestCase):
    """Test cases for the Vehicle model"""
    
    def test_vehicle_age_calculation(self):
        """Test the age calculation property"""
        # Create a vehicle with registration date 5 years ago
        five_years_ago = datetime.now() - timedelta(days=5*365)
        vehicle = Vehicle(
            registration_number="ABC123", 
            registration_date=five_years_ago,
            fuel_type="PETROL"
        )
        
        # Check that age is approximately 5 years
        self.assertAlmostEqual(vehicle.age, 5.0, delta=0.1)
        
    def test_diesel_eligibility(self):
        """Test the eligibility check for diesel vehicles"""
        # Create a diesel vehicle with registration date 9 years ago (eligible)
        nine_years_ago = datetime.now() - timedelta(days=9*365)
        eligible_vehicle = Vehicle(
            registration_number="ABC123", 
            registration_date=nine_years_ago,
            fuel_type="DIESEL"
        )
        
        # Create a diesel vehicle with registration date 11 years ago (not eligible)
        eleven_years_ago = datetime.now() - timedelta(days=11*365)
        ineligible_vehicle = Vehicle(
            registration_number="XYZ789", 
            registration_date=eleven_years_ago,
            fuel_type="DIESEL"
        )
        
        # Test with default limits (diesel: 10 years)
        self.assertTrue(eligible_vehicle.is_eligible_for_fuel())
        self.assertFalse(ineligible_vehicle.is_eligible_for_fuel())
        
    def test_petrol_eligibility(self):
        """Test the eligibility check for petrol vehicles"""
        # Create a petrol vehicle with registration date 14 years ago (eligible)
        fourteen_years_ago = datetime.now() - timedelta(days=14*365)
        eligible_vehicle = Vehicle(
            registration_number="ABC123", 
            registration_date=fourteen_years_ago,
            fuel_type="PETROL"
        )
        
        # Create a petrol vehicle with registration date 16 years ago (not eligible)
        sixteen_years_ago = datetime.now() - timedelta(days=16*365)
        ineligible_vehicle = Vehicle(
            registration_number="XYZ789", 
            registration_date=sixteen_years_ago,
            fuel_type="PETROL"
        )
        
        # Test with default limits (petrol: 15 years)
        self.assertTrue(eligible_vehicle.is_eligible_for_fuel())
        self.assertFalse(ineligible_vehicle.is_eligible_for_fuel())
        
    def test_custom_age_limits(self):
        """Test eligibility with custom age limits"""
        # Create vehicles with registration dates 12 years ago
        twelve_years_ago = datetime.now() - timedelta(days=12*365)
        diesel_vehicle = Vehicle(
            registration_number="ABC123", 
            registration_date=twelve_years_ago,
            fuel_type="DIESEL"
        )
        petrol_vehicle = Vehicle(
            registration_number="XYZ789", 
            registration_date=twelve_years_ago,
            fuel_type="PETROL"
        )
        
        # Test with custom limits (diesel: 15 years, petrol: 10 years)
        self.assertTrue(diesel_vehicle.is_eligible_for_fuel(diesel_age_limit=15, petrol_age_limit=10))
        self.assertFalse(petrol_vehicle.is_eligible_for_fuel(diesel_age_limit=15, petrol_age_limit=10))
        
if __name__ == '__main__':
    unittest.main() 