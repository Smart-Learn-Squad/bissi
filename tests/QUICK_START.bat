@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 🚀 BISSI Agentic Capabilities - Quick Start

echo ╔════════════════════════════════════════════════════════╗
echo ║  BISSI Agentic Capabilities Test Suite - Quick Start   ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo 📁 Project root: %PROJECT_ROOT%

REM Step 1: Activate venv
echo.
echo 1️⃣  Activating virtual environment...
if exist "%PROJECT_ROOT%\.venv" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    echo ✅ Virtual environment activated
) else (
    echo ❌ Virtual environment not found at %PROJECT_ROOT%\.venv
    exit /b 1
)

REM Step 2: Check pytest
echo.
echo 2️⃣  Checking pytest...
python -m pip show pytest >nul 2>&1
if !errorlevel! neq 0 (
    echo ⏳ Installing pytest...
    pip install pytest -q
    if errorlevel 1 (
        echo ❌ Failed to install pytest
        exit /b 1
    )
    echo ✅ pytest installed
) else (
    echo ✅ pytest already installed
)

REM Step 3: Run tests
echo.
echo 3️⃣  Running tests...
cd /d "%PROJECT_ROOT%"
python -m pytest tests/test_agentic_capabilities.py -v --tb=short
if errorlevel 1 (
    echo ❌ Test suite failed
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║              Test execution complete! 🎉               ║
echo ╚════════════════════════════════════════════════════════╝
