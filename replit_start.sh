#!/bin/bash

echo "================================="
echo "   Dependify Replit Launcher"
echo "================================="
echo ""
echo "Which service do you want to run?"
echo "1) Backend (FastAPI)"
echo "2) Frontend (Next.js)"
echo ""
read -p "Enter 1 or 2: " choice

if [ "$1" == "1" ]; then
    echo "🚀 Starting Backend..."
    
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    echo "📦 Installing dependencies..."
    echo "This may take a few minutes..."
    python3 -m pip install -r backend/requirements.txt
    
    # Replit often needs 0.0.0.0
    echo "🔥 Running Server..."
    exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    
elif [ "$1" == "2" ]; then
    echo "🚀 Starting Frontend..."
    cd frontend
    
    echo "📦 Installing dependencies..."
    pnpm install
    
    echo "🔥 Running Next.js..."
    pnpm dev --port 3000 --hostname 0.0.0.0
    
else
    echo "❌ Invalid choice. Please Click 'Run' again."
fi
