#!/bin/bash

# Start Backend in background
echo "Starting Backend..."
source venv/bin/activate
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Wait a moment for backend
sleep 2

# Start Frontend in foreground
echo "Starting Frontend..."
cd frontend
pnpm start -- -p 3000 --hostname 0.0.0.0
