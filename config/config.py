import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database Configuration
DB_URI = os.getenv("DB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "anpr_database")
DB_COLLECTION = os.getenv("DB_COLLECTION", "vehicles")

# Database Type Configuration
USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() == "true"
USE_CSV_FALLBACK = os.getenv("USE_CSV_FALLBACK", "true").lower() == "true"
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "data/vahan_data.csv")

# API Configuration
API_PORT = int(os.getenv("API_PORT", "5000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# Vehicle Age Limits (in years)
DIESEL_AGE_LIMIT = int(os.getenv("DIESEL_AGE_LIMIT", "10"))
PETROL_AGE_LIMIT = int(os.getenv("PETROL_AGE_LIMIT", "15"))

# OCR Configuration
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

# Vehicle Database API Configuration
VAHAN_API_URL = os.getenv("VAHAN_API_URL", "https://vahan.example.gov.in/api/vehicle")
VAHAN_API_KEY = os.getenv("VAHAN_API_KEY", "dummy_key")

# Camera settings
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", 0)  # Default to first webcam
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "640"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "480"))

# Image processing settings
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.5"))  # Minimum confidence for detected license plates 