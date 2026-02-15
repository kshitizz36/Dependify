#!/bin/bash
# Quick start script for Dependify 2.0 backend

echo "============================================================"
echo "Starting Dependify 2.0 Backend"
echo "============================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please run: python3 setup_env.py"
    exit 1
fi

# Validate configuration
echo "Validating configuration..."
python3 -c "from config import Config; is_valid, missing = Config.validate(); exit(0 if is_valid else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Configuration invalid!"
    echo "Please check your .env file"
    exit 1
fi

echo "✅ Configuration valid"

# Check if port is in use
PORT=${PORT:-5000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is already in use"
    echo "Attempting to kill process..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start server
echo "Starting server on port $PORT..."
python3 server.py

echo "Server stopped"
