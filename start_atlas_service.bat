@echo off
echo 🚀 Starting MongoDB Atlas Service for ANPR System...
echo.

cd /d "d:\MAJOR PROJECT\ANPR"

echo 📋 Activating Python environment...
call python -m pip install schedule pymongo certifi --quiet

echo 🔗 Starting Atlas Service...
python src/services/atlas_service.py

pause
