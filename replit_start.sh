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

if [ "$choice" == "1" ]; then
    echo "🚀 Starting Backend..."
    cd backend
    
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python -m venv venv
    fi
    
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    # Replit often needs 0.0.0.0
    echo "🔥 Running Server..."
    python server.py
    
elif [ "$choice" == "2" ]; then
    echo "🚀 Starting Frontend..."
    cd frontend
    
    echo "📦 Installing dependencies..."
    pnpm install
    
    echo "🔥 Running Next.js..."
    pnpm dev --port 3000 --hostname 0.0.0.0
    
else
    echo "❌ Invalid choice. Please Click 'Run' again."
fi
