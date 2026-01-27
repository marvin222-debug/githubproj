# MongoDB Integration Guide for ANPR System

This guide explains how to integrate MongoDB database with your ANPR (Automatic Number Plate Recognition) system.

## 🎯 Overview

The ANPR system now supports MongoDB as the primary database for storing vehicle information, with CSV as a fallback option. This provides better performance, scalability, and advanced querying capabilities.

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB Community Server 4.4 or higher
- All existing ANPR system dependencies

## 🚀 Quick Start

### 1. Install MongoDB

#### Windows
```bash
# Download from: https://www.mongodb.com/try/download/community
# Run installer and follow setup wizard
# Add MongoDB to PATH environment variable
```

#### Linux (Ubuntu/Debian)
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package database
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS
```bash
# Install using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

### 2. Configure Environment

Create a `.env` file in your project root:

```env
# MongoDB Configuration
DB_URI=mongodb://localhost:27017/
DB_NAME=anpr_database
DB_COLLECTION=vehicles

# Database Type Configuration
USE_MONGODB=true
USE_CSV_FALLBACK=true
CSV_FILE_PATH=data/vahan_data.csv

# Other existing configurations...
```

### 3. Setup MongoDB Database

Run the setup script to configure MongoDB:

```bash
# Setup MongoDB database structure
python scripts/setup_mongodb.py

# Check MongoDB installation only
python scripts/setup_mongodb.py --check-only

# Create database structure only
python scripts/setup_mongodb.py --create-structure

# Test database connection only
python scripts/setup_mongodb.py --test-connection
```

### 4. Import Vehicle Data

Import your vehicle data from CSV to MongoDB:

```bash
# Import all vehicle data
python scripts/import_csv_to_mongodb.py

# Import with custom settings
python scripts/import_csv_to_mongodb.py --csv-file data/vahan_data.csv --mongo-uri mongodb://localhost:27017/ --db-name anpr_database

# Import and show statistics
python scripts/import_csv_to_mongodb.py --show-stats
```

### 5. Migrate Existing Data (Alternative)

If you have existing CSV data, use the migration script:

```bash
# Complete migration process
python scripts/migrate_to_mongodb.py

# Check prerequisites only
python scripts/migrate_to_mongodb.py --check-only

# Verify existing migration
python scripts/migrate_to_mongodb.py --verify-only

# Backup existing data only
python scripts/migrate_to_mongodb.py --backup-only
```

## 🔧 Configuration Options

### Database Priority Order

The system uses the following priority order for vehicle lookups:

1. **MongoDB** (Primary) - Fast, scalable, advanced querying
2. **CSV Database** (Fallback) - Local file-based storage
3. **Vahan API** (External) - Government vehicle database
4. **Mock Data** (Development) - Sample data for testing

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MONGODB` | `true` | Enable MongoDB as primary database |
| `USE_CSV_FALLBACK` | `true` | Enable CSV as fallback database |
| `DB_URI` | `mongodb://localhost:27017/` | MongoDB connection URI |
| `DB_NAME` | `anpr_database` | MongoDB database name |
| `DB_COLLECTION` | `vehicles` | MongoDB collection name |
| `CSV_FILE_PATH` | `data/vahan_data.csv` | CSV file path for fallback |

## 📊 Database Structure

### MongoDB Collection Schema

```json
{
  "_id": "ObjectId",
  "registration_number": "KA01MJ2023",
  "registration_date": "2023-01-15T00:00:00Z",
  "fuel_type": "PETROL",
  "owner_name": "John Doe",
  "vehicle_make": "Toyota",
  "vehicle_model": "Corolla",
  "chassis_number": "MALA851CMKM123456",
  "engine_number": "1ZZ1234567",
  "state": "Karnataka",
  "district": "Bangalore Urban",
  "rto_office": "Bangalore Central",
  "vehicle_class": "LMV",
  "vehicle_category": "Private",
  "manufacturing_year": 2023,
  "engine_capacity": "1800",
  "seating_capacity": 5,
  "gross_vehicle_weight": "1500",
  "unladen_weight": "1200",
  "vehicle_color": "White",
  "norms": "BS6",
  "fitness_upto": "2025-01-15T00:00:00Z",
  "insurance_upto": "2024-01-15T00:00:00Z",
  "permit_upto": "2025-01-15T00:00:00Z",
  "tax_upto": "2025-01-15T00:00:00Z",
  "puc_upto": "2024-01-15T00:00:00Z",
  "rc_status": "Active",
  "vehicle_status": "Active",
  "imported_at": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

### Indexes

The system automatically creates the following indexes for optimal performance:

- `registration_number` (Unique)
- `state`
- `fuel_type`
- `vehicle_make`
- `registration_date`
- Compound indexes for common queries

## 🔍 Usage Examples

### Basic Vehicle Lookup

```python
from src.database.vehicle_db import VehicleDatabase

# Initialize database
db = VehicleDatabase()

# Get vehicle information
vehicle = db.get_vehicle_info("KA01MJ2023")
if vehicle:
    print(f"Owner: {vehicle.owner_name}")
    print(f"Make: {vehicle.vehicle_make}")
    print(f"Age: {vehicle.age} years")
    print(f"Fuel Eligible: {vehicle.is_eligible_for_fuel()}")
```

### Advanced Vehicle Search

```python
# Search by fuel type
diesel_vehicles = db.search_vehicles(fuel_type="DIESEL")

# Search by state
karnataka_vehicles = db.search_vehicles(state="Karnataka")

# Search by vehicle make
toyota_vehicles = db.search_vehicles(vehicle_make="Toyota")

# Complex search
old_diesel_vehicles = db.search_vehicles(
    fuel_type="DIESEL",
    state="Karnataka",
    vehicle_make="Mahindra"
)
```

### Get Detailed Information

```python
# Get complete vehicle details
details = db.get_vehicle_details("KA01MJ2023")
if details:
    print(f"Complete details: {details}")
    print(f"Age: {details['age']} years")
    print(f"Fuel eligible: {details['fuel_eligibility']['eligible']}")
```

### Database Statistics

```python
# Get database statistics
stats = db.get_statistics()
print(f"Total vehicles: {stats['total_vehicles']}")
print(f"Fuel types: {stats['fuel_types']}")
print(f"States: {stats['states']}")
print(f"Vehicle makes: {stats['vehicle_makes']}")
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed
```bash
# Check if MongoDB is running
sudo systemctl status mongod  # Linux
brew services list | grep mongodb  # macOS
net start MongoDB  # Windows

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log  # Linux
```

#### 2. Import Script Fails
```bash
# Check CSV file exists
ls -la data/vahan_data.csv

# Check MongoDB connection
python scripts/setup_mongodb.py --check-only

# Check CSV file format
head -5 data/vahan_data.csv
```

#### 3. Database Not Found
```bash
# Verify database exists
python -c "from src.database.vehicle_db import VehicleDatabase; db = VehicleDatabase(); print(db.get_statistics())"
```

### Performance Optimization

1. **Index Optimization**: Ensure all required indexes are created
2. **Connection Pooling**: Use connection pooling for high-traffic applications
3. **Query Optimization**: Use specific field projections for large collections
4. **Memory Management**: Monitor MongoDB memory usage

## 📈 Monitoring and Maintenance

### Database Health Check

```bash
# Check database status
python scripts/setup_mongodb.py --test-connection

# Get database statistics
python -c "from src.database.vehicle_db import VehicleDatabase; db = VehicleDatabase(); print(db.get_statistics())"
```

### Backup and Restore

```bash
# Backup MongoDB data
mongodump --db anpr_database --out backup/

# Restore MongoDB data
mongorestore --db anpr_database backup/anpr_database/
```

### Data Migration

```bash
# Migrate from CSV to MongoDB
python scripts/migrate_to_mongodb.py

# Verify migration
python scripts/migrate_to_mongodb.py --verify-only
```

## 🔄 Switching Between Databases

### Use MongoDB Only
```env
USE_MONGODB=true
USE_CSV_FALLBACK=false
```

### Use CSV Only
```env
USE_MONGODB=false
USE_CSV_FALLBACK=true
```

### Use Both (Recommended)
```env
USE_MONGODB=true
USE_CSV_FALLBACK=true
```

## 📚 Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas (Cloud)](https://www.mongodb.com/atlas)
- [MongoDB Compass (GUI)](https://www.mongodb.com/products/compass)

## 🆘 Support

If you encounter issues with MongoDB integration:

1. Check the troubleshooting section above
2. Verify MongoDB installation and configuration
3. Check application logs for specific error messages
4. Ensure all required dependencies are installed
5. Verify database permissions and connectivity

---

**Note**: This integration maintains backward compatibility with existing CSV-based systems while providing the benefits of a modern NoSQL database.

