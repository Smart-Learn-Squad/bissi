#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# BISSI Master Build Script
# This script builds the application for production

Write-Host "Building BISSI Master for production..." -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "X Error: Please run this script from the bissi-master-ui directory" -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "-> Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X npm install failed" -ForegroundColor Red
        exit 1
    }
}

# Build for current platform
Write-Host "-> Building application..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "OK Build complete! Check the 'dist' directory for output files." -ForegroundColor Green

# Show what was built
if (Test-Path "dist") {
    Write-Host "Build artifacts:" -ForegroundColor White
    Get-ChildItem -Path "dist" | Format-Table Name, Length, LastWriteTime -AutoSize
} else {
    Write-Host "! No dist directory found - build may have failed" -ForegroundColor Yellow
}
