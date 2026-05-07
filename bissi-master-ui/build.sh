#!/bin/bash

# BISSI Master Build Script
# This script builds the application for production

echo "🏗️  Building BISSI Master for production..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the bissi-master-ui directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build for current platform
echo "🔨 Building application..."
npm run build

echo "✅ Build complete! Check the 'dist' directory for output files."

# Show what was built
if [ -d "dist" ]; then
    echo "📁 Build artifacts:"
    ls -la dist/
else
    echo "⚠️  No dist directory found - build may have failed"
fi
