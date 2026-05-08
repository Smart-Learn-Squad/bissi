@echo off
chcp 65001 >nul

REM BISSI Master Development Startup Script
REM This script starts both the backend and frontend in development mode

echo Starting BISSI Master Development Environment...

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: Please run this script from the bissi-master-ui directory
    exit /b 1
)

REM Start the Python backend in the background
echo Starting Python backend...
cd ..
start /B python main.py
set "BACKEND_PID=%ERRORLEVEL%"

REM Wait a moment for the backend to start
timeout /T 3 /NOBREAK >nul

REM Check if backend is running
curl -s http://localhost:8765/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running on http://localhost:8765
) else (
    echo ⚠️  Backend might not be ready yet, but continuing...
)

REM Start the Electron app
echo 🖥️  Starting Electron app...
cd bissi-master-ui
npm start

REM Cleanup on exit
echo 🧹 Cleaning up...
taskkill /PID %BACKEND_PID% /F 2>nul
echo ✅ Development environment stopped
