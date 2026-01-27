#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the API endpoints
"""

import requests
import json
import time

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testing API endpoints...")
    
    # Test health check
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test vehicles endpoint
    try:
        r = requests.get(f"{base_url}/api/vehicles", timeout=5)
        print(f"\nVehicles endpoint: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Total vehicles: {data['total_vehicles']}")
            print(f"Page: {data['page']}/{data['total_pages']}")
            print("\nFirst 5 vehicles:")
            for i, vehicle in enumerate(data['vehicles'][:5]):
                print(f"{i+1}. {vehicle['registration_number']} - {vehicle['vehicle_make']} {vehicle['vehicle_model']} ({vehicle['fuel_type']})")
                print(f"   Owner: {vehicle['owner_name']}")
                print(f"   Age: {vehicle['age_years']} years, Eligible: {vehicle['fuel_eligibility']['eligible']}")
                print()
        else:
            print(f"Error: {r.text}")
            
    except Exception as e:
        print(f"Vehicles endpoint failed: {e}")
    
    # Test specific vehicle lookup
    try:
        r = requests.get(f"{base_url}/api/check-plate?plate=KA01MJ2023", timeout=5)
        print(f"\nSpecific vehicle lookup: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Vehicle: {data['registration_number']}")
            print(f"Details: {data['vehicle_details']}")
            print(f"Eligible: {data['fuel_eligibility']['eligible']}")
    except Exception as e:
        print(f"Specific vehicle lookup failed: {e}")

if __name__ == "__main__":
    test_api()

