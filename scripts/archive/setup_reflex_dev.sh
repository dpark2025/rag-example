#!/bin/bash
# Development setup script for Reflex RAG application

set -e

echo "🚀 Setting up Reflex RAG Development Environment"

# Check if we're in the right directory
if [ ! -f "requirements.reflex.txt" ]; then
    echo "❌ Error: requirements.reflex.txt not found. Please run from project root."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.reflex.txt

# Initialize Reflex project
echo "⚡ Initializing Reflex..."
cd app/reflex_app
reflex init --name rag_reflex_app --template blank --no-frontend

# Copy our custom files
echo "📋 Setting up custom Reflex app..."
cp reflex_app.py rag_reflex_app/rag_reflex_app.py
cp -r components/ rag_reflex_app/
cp -r layouts/ rag_reflex_app/
cp -r pages/ rag_reflex_app/
cp -r state/ rag_reflex_app/
cp -r services/ rag_reflex_app/

cd ../..

echo "✅ Reflex development environment setup complete!"
echo ""
echo "📍 Next steps:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Start Reflex dev server: cd app/reflex_app && reflex run"
echo "  3. Open browser: http://localhost:3000"
echo ""
echo "🔧 Development commands:"
echo "  - Test setup: python scripts/test_reflex_phase1.py"
echo "  - Start backend: cd app && python main.py"
echo "  - Start Reflex: cd app/reflex_app && reflex run"