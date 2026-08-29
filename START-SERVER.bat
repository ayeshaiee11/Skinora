@echo off
title Skinora Server
cd /d "%~dp0"

echo.
echo  ========================================
echo   SKINORA - Starting website server
echo  ========================================
echo.
echo  STEP 1: MongoDB must be running first!
echo          Double-click START-MONGODB.bat in another terminal,
echo          OR run:  mongod --dbpath "%cd%\data\mongodb"
echo.
echo  STEP 2: This window starts the Python API + website.
echo.
echo  Landing page:     http://localhost:8000
echo  Login / sign up:  http://localhost:8000/login/
echo.
echo  Installing Python packages (if needed)...
pip install -r backend\requirements.txt
echo.
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
