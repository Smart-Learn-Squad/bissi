#!/bin/bash

# BISSI Master Development Startup Script
# This script starts both the backend and frontend in development mode

echo "🚀 Starting BISSI Master Development Environment..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the bissi-master-ui directory"
    exit 1
fi

# Start the Python backend in the background
echo "📦 Starting Python backend..."
cd ..
python main.py &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8765/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8765"
else
    echo "⚠️  Backend might not be ready yet, but continuing..."
fi

# Start the Electron app
echo "🖥️  Starting Electron app..."
cd bissi-master-ui
npm start

# Cleanup on exit
echo "🧹 Cleaning up..."
kill $BACKEND_PID 2>/dev/null
echo "✅ Development environment stopped"
