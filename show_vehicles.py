#!/usr/bin/env python3
"""
Show vehicle data from CSV fallback
"""

import pandas as pd
import json

def main():
    # Load CSV data
    df = pd.read_csv('data/vahan_data.csv')
    
    print("=== VEHICLE DATA FROM CSV FALLBACK ===")
    print(f"Total vehicles: {len(df)}")
    print("\n=== ALL VEHICLES ===")
    
    for i, row in df.iterrows():
        print(f"{i+1:2d}. {row['registration_number']} - {row['vehicle_make']} {row['vehicle_model']} ({row['fuel_type']})")
        print(f"     Owner: {row['owner_name']}")
        print(f"     State: {row['state']}, District: {row['district']}")
        print(f"     Registration Date: {row['registration_date']}")
        print(f"     Chassis: {row['chassis_number']}")
        print(f"     Engine: {row['engine_number']}")
        print(f"     Status: {row['rc_status']}")
        print()
    
    # Convert to JSON format
    vehicles_json = df.to_dict('records')
    print("=== JSON FORMAT (first 3 records) ===")
    print(json.dumps(vehicles_json[:3], indent=2, default=str))

if __name__ == "__main__":
    main()

