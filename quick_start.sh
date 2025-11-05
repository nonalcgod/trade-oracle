#!/bin/bash

# Trade Oracle - Quick Start Script
# This script helps you get started quickly

set -e

echo "=================================================="
echo "Trade Oracle - Quick Start"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found."
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✅ .env created. Please edit it and add your API keys:"
    echo "   - ALPACA_API_KEY"
    echo "   - ALPACA_SECRET_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo ""
    echo "Then run this script again."
    exit 0
fi

echo "✅ .env file found"
echo ""

# Check Python virtual environment
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install -q -r requirements.txt
cd ..
echo "✅ Python dependencies installed"

# Install Node dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo ""
    echo "📦 Installing Node dependencies..."
    cd frontend
    npm install --silent
    cd ..
    echo "✅ Node dependencies installed"
else
    echo "✅ Node dependencies already installed"
fi

echo ""
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Setup Supabase Database:"
echo "   - Go to your Supabase project"
echo "   - Open SQL Editor"
echo "   - Copy/paste backend/schema.sql"
echo "   - Run it"
echo ""
echo "2. Run Backtest (validate strategy):"
echo "   cd backtest"
echo "   python run_backtest.py"
echo ""
echo "3. Start Backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo "   # Visit http://localhost:8000/docs"
echo ""
echo "4. Start Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo "   # Visit http://localhost:3000"
echo ""
echo "=================================================="
echo "Documentation:"
echo "  - SETUP.md: Detailed setup instructions"
echo "  - PHASES_1-3_COMPLETE.md: What we built"
echo "  - README.md: Project overview"
echo "=================================================="

