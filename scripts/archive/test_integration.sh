#!/bin/bash
# Integration testing script for Reflex RAG application

set -e

echo "🧪 Reflex RAG Integration Testing"
echo "================================="

# Check if we're in the right directory
if [ ! -f "requirements.reflex.txt" ]; then
    echo "❌ Error: requirements.reflex.txt not found. Please run from project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Reflex dependencies..."
pip install --upgrade pip
pip install -r requirements.reflex.txt

# Check if Ollama is running
echo "🔍 Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama not running. Please start Ollama first:"
    echo "   ollama serve"
    echo "   ollama pull llama3.2:3b  # or your preferred model"
    exit 1
else
    echo "✅ Ollama is running"
fi

# Start RAG backend in background
echo "🚀 Starting RAG backend..."
cd app
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ RAG backend is healthy"
else
    echo "❌ RAG backend failed to start"
    kill $BACKEND_PID
    exit 1
fi

# Initialize Reflex project
echo "⚡ Initializing Reflex project..."
cd app/reflex_app

# Initialize if not already done
if [ ! -d ".web" ]; then
    reflex init --name rag_reflex_app --template blank
    
    # Copy our custom files
    echo "📋 Setting up custom Reflex app..."
    cp reflex_app.py rag_reflex_app/rag_reflex_app.py
    cp -r components/ rag_reflex_app/
    cp -r layouts/ rag_reflex_app/
    cp -r pages/ rag_reflex_app/
    cp -r state/ rag_reflex_app/
    cp -r services/ rag_reflex_app/
fi

# Start Reflex in development mode
echo "🎯 Starting Reflex application..."
echo "Frontend will be available at: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    kill $BACKEND_PID 2>/dev/null || true
    echo "✅ Services stopped"
}

trap cleanup EXIT

# Start Reflex (this will block)
reflex run --env dev