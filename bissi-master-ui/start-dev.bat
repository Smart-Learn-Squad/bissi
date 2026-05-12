@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

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
if not exist ".venv" (
    echo ❌ Error: .venv not found in project root
    exit /b 1
)
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Error: failed to activate .venv
    exit /b 1
)

for /f %%P in ('powershell -NoProfile -Command "$p = Start-Process -FilePath python -ArgumentList 'main.py' -PassThru -WindowStyle Hidden; $p.Id"') do set "BACKEND_PID=%%P"
if not defined BACKEND_PID (
    echo ❌ Error: failed to start backend process
    exit /b 1
)

REM Wait for backend health
set /a "COUNT=0"
:wait_backend
set /a "COUNT+=1"
curl -s http://localhost:8765/health >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ Backend is running on http://localhost:8765
    goto :backend_ready
)
tasklist /FI "PID eq !BACKEND_PID!" | find "!BACKEND_PID!" >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend process stopped unexpectedly
    exit /b 1
)
if !COUNT! geq 20 (
    echo ❌ Backend failed health check after 20s
    exit /b 1
)
timeout /T 1 /NOBREAK >nul
goto :wait_backend

:backend_ready

REM Start the Electron app
echo 🖥️  Starting Electron app...
cd bissi-master-ui
npm start
if errorlevel 1 (
    echo ❌ Electron app failed to start
)

REM Cleanup on exit
echo 🧹 Cleaning up...
taskkill /PID %BACKEND_PID% /F 2>nul
echo ✅ Development environment stopped
