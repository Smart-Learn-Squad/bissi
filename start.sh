#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━━ BISSI Launcher ━━━"

# 1. Check venv
if [ ! -d ".venv" ]; then
    echo "❌ Virtual env not found in .venv"
    exit 1
fi
source .venv/bin/activate

# 2. Kill stale processes
echo "→ Cleaning up old processes..."
pkill -f "llama_cpp.server" 2>/dev/null || true
pkill -f "uvicorn.*api.server" 2>/dev/null || true
sleep 1

# 3. Launch llama.cpp server
echo "→ Starting llama.cpp server on :8001..."
nohup python -m llama_cpp.server \
    --model gemma-4-E2B-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8001 \
    --n_ctx 4096 \
    --n_threads 4 \
    --use_mmap False \
    > /tmp/bissi-llama.log 2>&1 &
LLAMA_PID=$!

# Wait for llama.cpp to be ready
echo "→ Waiting for llama.cpp..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8001/v1/models > /dev/null 2>&1; then
        echo "✓ llama.cpp ready (PID $LLAMA_PID)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ llama.cpp failed to start after 30s"
        echo "  Log: /tmp/bissi-llama.log"
        tail -5 /tmp/bissi-llama.log
        kill $LLAMA_PID 2>/dev/null
        exit 1
    fi
    sleep 2
done

# 4. Launch FastAPI backend
echo "→ Starting BISSI backend on :8765..."
nohup uvicorn api.server:app \
    --host 127.0.0.1 \
    --port 8765 \
    --log-level info \
    > /tmp/bissi-api.log 2>&1 &
API_PID=$!

# Wait for FastAPI to be ready
echo "→ Waiting for backend..."
for i in $(seq 1 15); do
    if curl -sf http://127.0.0.1:8765/health > /dev/null 2>&1; then
        echo "✓ BISSI backend ready (PID $API_PID)"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Backend failed to start after 15s"
        echo "  Log: /tmp/bissi-api.log"
        tail -5 /tmp/bissi-api.log
        kill $API_PID $LLAMA_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# 5. Launch Electron
echo "→ Launching Electron app..."
cd bissi-master-ui
npm start

# Cleanup on exit (when Electron closes)
echo "→ Shutting down servers..."
kill $API_PID $LLAMA_PID 2>/dev/null
echo "✓ Done"
