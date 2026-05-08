@echo off
chcp 65001 >nul

REM BISSI Master Build Script
REM This script builds the application for production

echo 🏗️  Building BISSI Master for production...

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: Please run this script from the bissi-master-ui directory
    exit /b 1
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

REM Build for current platform
echo 🔨 Building application...
npm run build

echo ✅ Build complete! Check the 'dist' directory for output files.

REM Show what was built
if exist "dist" (
    echo 📁 Build artifacts:
    dir dist /b
) else (
    echo ⚠️  No dist directory found - build may have failed
)
