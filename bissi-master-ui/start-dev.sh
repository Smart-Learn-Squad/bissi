#!/bin/bash
set -euo pipefail

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
if [ ! -d ".venv" ]; then
    echo "❌ Error: .venv not found in project root"
    exit 1
fi
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

cleanup() {
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Wait for backend readiness
for i in $(seq 1 20); do
    if curl -sf --max-time 2 http://localhost:8765/health > /dev/null 2>&1; then
        echo "✅ Backend is running on http://localhost:8765"
        break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "❌ Backend process stopped unexpectedly"
        wait "$BACKEND_PID" || true
        exit 1
    fi
    if [ "$i" -eq 20 ]; then
        echo "❌ Backend failed health check after 20s"
        exit 1
    fi
    sleep 1
done

# Start the Electron app
echo "🖥️  Starting Electron app..."
cd bissi-master-ui
npm start

# Cleanup on exit
echo "🧹 Cleaning up..."
echo "✅ Development environment stopped"
