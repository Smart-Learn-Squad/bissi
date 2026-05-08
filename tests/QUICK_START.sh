#!/bin/bash

# 🚀 BISSI Agentic Capabilities - Quick Start

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  BISSI Agentic Capabilities Test Suite - Quick Start   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Step 1: Activate venv
echo
echo "1️⃣  Activating virtual environment..."
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/.venv"
    exit 1
fi

# Step 2: Check pytest
echo
echo "2️⃣  Checking pytest..."
if ! python -m pip show pytest > /dev/null 2>&1; then
    echo "⏳ Installing pytest..."
    pip install pytest -q
    echo "✅ pytest installed"
else
    echo "✅ pytest already installed"
fi

# Step 3: Run tests
echo
echo "3️⃣  Running tests..."
cd "$PROJECT_ROOT"
python -m pytest tests/test_agentic_capabilities.py -v --tb=short

echo
echo "╔════════════════════════════════════════════════════════╗"
echo "║              Test execution complete! ��               ║"
echo "╚════════════════════════════════════════════════════════╝"
