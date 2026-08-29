@echo off
title Skinora MongoDB
cd /d "%~dp0"
if not exist "data\mongodb" mkdir "data\mongodb"

echo Checking if MongoDB is already running on port 27017...
powershell -NoProfile -Command "try { $null = [System.Net.Sockets.TcpClient]::new('127.0.0.1',27017); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo.
    echo  MongoDB is ALREADY running on port 27017.
    echo  You do NOT need to start it again.
    echo  Just run START-SERVER.bat in another window.
    echo.
    pause
    exit /b 0
)

echo Starting MongoDB on port 27017...
echo Data folder: %cd%\data\mongodb
echo.
mongod --dbpath "%cd%\data\mongodb"
