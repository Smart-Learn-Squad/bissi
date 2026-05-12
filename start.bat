@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ━━━ BISSI Launcher ━━━

REM 1. Check venv
if not exist ".venv" (
    echo ❌ Virtual env not found in .venv
    exit /b 1
)
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    exit /b 1
)

REM Check required commands
for %%T in (python curl uvicorn npm) do (
    where %%T >nul 2>&1
    if errorlevel 1 (
        echo ❌ Missing required command: %%T
        exit /b 1
    )
)

REM Check model path
set "MODEL_PATH=gemma-4-E2B-it-Q4_K_M.gguf"
if not exist "%MODEL_PATH%" (
    set "MODEL_PATH=models\gemma-4-E2B-it-Q4_K_M.gguf"
)
if not exist "%MODEL_PATH%" (
    echo ❌ Model not found:
    echo    - %SCRIPT_DIR%gemma-4-E2B-it-Q4_K_M.gguf
    echo    - %SCRIPT_DIR%models\gemma-4-E2B-it-Q4_K_M.gguf
    exit /b 1
)

REM 2. Kill stale processes
echo → Cleaning up old processes...
taskkill /F /FI "IMAGENAME eq python*" 2>nul
timeout /T 1 /NOBREAK >nul

REM 3. Launch llama.cpp server
echo → Starting llama.cpp server on :8001...
start /B python -m llama_cpp.server ^
    --model "%MODEL_PATH%" ^
    --host 127.0.0.1 ^
    --port 8001 ^
    --n_ctx 4096 ^
    --n_threads 4 ^
    --use_mmap False ^
    > "%TEMP%\bissi-llama.log" 2>&1

REM Get PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "python.exe"') do set "LLAMA_PID=%%i"

REM Wait for llama.cpp to be ready
echo → Waiting for llama.cpp...
set /a "count=0"
:wait_llama
set /a "count+=1"
curl -s http://127.0.0.1:8001/v1/models >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ llama.cpp ready ^(PID %LLAMA_PID%^)
    goto :llama_ready
)
curl -s http://127.0.0.1:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ llama.cpp ready ^(PID %LLAMA_PID%^)
    goto :llama_ready
)
if %count% geq 30 (
    echo ❌ llama.cpp failed to start after 30s
    echo   Log: %TEMP%\bissi-llama.log
    powershell "Get-Content '%TEMP%\bissi-llama.log' | Select-Object -Last 5"
    taskkill /PID %LLAMA_PID% /F 2>nul
    exit /b 1
)
timeout /T 2 /NOBREAK >nul
goto :wait_llama

:llama_ready

REM 4. Launch FastAPI backend
echo → Starting BISSI backend on :8765...
start /B uvicorn api.server:app ^
    --host 127.0.0.1 ^
    --port 8765 ^
    --log-level info ^
    > "%TEMP%\bissi-api.log" 2>&1

REM Get PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "python.exe" ^| find /V "%LLAMA_PID%"') do set "API_PID=%%i"

REM Wait for FastAPI to be ready
echo → Waiting for backend...
set /a "count=0"
:wait_api
set /a "count+=1"
curl -s http://127.0.0.1:8765/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ BISSI backend ready ^(PID %API_PID%^)
    goto :api_ready
)
if %count% geq 15 (
    echo ❌ Backend failed to start after 15s
    echo   Log: %TEMP%\bissi-api.log
    powershell "Get-Content '%TEMP%\bissi-api.log' | Select-Object -Last 5"
    taskkill /PID %API_PID% /F 2>nul
    taskkill /PID %LLAMA_PID% /F 2>nul
    exit /b 1
)
timeout /T 1 /NOBREAK >nul
goto :wait_api

:api_ready

REM 5. Launch Electron
echo → Launching Electron app...
cd bissi-master-ui
npm start
if errorlevel 1 (
    echo ❌ Electron app failed to start
)

REM Cleanup on exit (when Electron closes)
echo → Shutting down servers...
taskkill /PID %API_PID% /F 2>nul
taskkill /PID %LLAMA_PID% /F 2>nul
echo ✓ Done
