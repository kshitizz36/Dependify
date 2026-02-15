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

# Default to argument if provided, else use interactive choice
TARGET=${1:-$choice}

if [ "$TARGET" == "1" ]; then
    echo "🚀 Starting Backend..."
    
    # Check for critical backend secrets
    if [ -z "$SUPABASE_URL" ]; then
        echo "⚠️  WARNING: SUPABASE_URL is missing in Replit Secrets."
        echo "   Some backend features may not work."
    fi

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
    
elif [ "$TARGET" == "2" ]; then
    echo "🚀 Starting Frontend..."
    cd frontend

    # Check for critical frontend secrets
    if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
        echo "❌ ERROR: NEXT_PUBLIC_SUPABASE_URL is missing in Replit Secrets."
        echo "   The frontend WILL CRASH without this."
        echo "👉 Please add 'NEXT_PUBLIC_SUPABASE_URL' to Replit Secrets (same as SUPABASE_URL)."
        exit 1
    fi
    
    echo "📦 Installing dependencies..."
    pnpm install
    
    echo "🔥 Running Next.js..."
    pnpm dev --port 3000 --hostname 0.0.0.0
    
else
    echo "❌ Invalid choice. Please Click 'Run' again."
fi
