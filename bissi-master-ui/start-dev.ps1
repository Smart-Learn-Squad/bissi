#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# BISSI Master Development Startup Script
# This script starts both the backend and frontend in development mode

Write-Host "Starting BISSI Master Development Environment..." -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "X Error: Please run this script from the bissi-master-ui directory" -ForegroundColor Red
    exit 1
}

# Start the Python backend in the background
Write-Host "-> Starting Python backend..." -ForegroundColor Yellow
Set-Location ..

if (-not (Test-Path ".venv")) {
    Write-Host "X Error: .venv not found in project root" -ForegroundColor Red
    exit 1
}

& ".venv\Scripts\Activate.ps1"

$BackendProc = Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "main.py" `
    -NoNewWindow `
    -PassThru
$BackendPID = $BackendProc.Id

# Cleanup function — kill backend when script exits
function Invoke-Cleanup {
    if ($BackendPID) {
        Stop-Process -Id $BackendPID -Force -ErrorAction SilentlyContinue
    }
}

# Register cleanup on Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Invoke-Cleanup }
try {

    # Wait for backend readiness
    function Test-Endpoint {
        param([string]$Url)
        try {
            $r = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            return $r.StatusCode -eq 200
        } catch { return $false }
    }

    $ready = $false
    for ($i = 1; $i -le 20; $i++) {
        if (Test-Endpoint "http://localhost:8765/health") {
            Write-Host "OK Backend is running on http://localhost:8765" -ForegroundColor Green
            $ready = $true
            break
        }
        if ($BackendProc.HasExited) {
            Write-Host "X Backend process stopped unexpectedly" -ForegroundColor Red
            exit 1
        }
        if ($i -eq 20) {
            Write-Host "X Backend failed health check after 20s" -ForegroundColor Red
            Invoke-Cleanup
            exit 1
        }
        Start-Sleep -Seconds 1
    }

    # Start the Electron app
    Write-Host "-> Starting Electron app..." -ForegroundColor Yellow
    Set-Location "bissi-master-ui"
    npm start   # Blocks until Electron closes

} finally {
    # Cleanup on exit
    Write-Host "-> Cleaning up..." -ForegroundColor Yellow
    Invoke-Cleanup
    Write-Host "OK Development environment stopped" -ForegroundColor Green
}
