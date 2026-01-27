@echo off
title ANPR System Startup
color 0A
echo.
echo ========================================
echo    🚀 ANPR System Complete Startup
echo ========================================
echo.

cd /d "d:\MAJOR PROJECT\ANPR"

echo 📦 Installing/Updating dependencies...
python -m pip install -r requirements.txt --quiet --upgrade

echo.
echo 🔗 Starting MongoDB Atlas Service...
start "Atlas Service" cmd /k "python src/services/atlas_service.py"

echo ⏳ Waiting for Atlas service to initialize...
timeout /t 5 /nobreak >nul

echo.
echo 🎯 Starting ANPR Web Application...
echo 📋 System will be available at: http://127.0.0.1:5000
echo 📊 Performance metrics: http://127.0.0.1:5000/api/performance
echo 🔗 Atlas status: http://127.0.0.1:5000/api/atlas/status
echo.
echo ✅ System starting... Please wait for "Running on http://127.0.0.1:5000"
echo.

python src/api/web_app.py

pause
