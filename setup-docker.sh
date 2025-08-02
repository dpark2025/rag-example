#!/bin/bash

# Setup script for Local RAG System using Docker (Alternative)

echo "🐳 Setting up Local RAG System with Docker (Alternative)..."

# Check if Ollama is installed and running
echo "🔍 Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first:"
    echo "   Visit: https://ollama.ai/download"
    echo "   Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   Run: ollama serve"
    echo "   (or it may start automatically depending on your installation)"
    exit 1
fi

echo "✅ Ollama is installed and running"

# Create necessary directories
mkdir -p data/chroma_db data/documents

# Build container with Docker
echo "📦 Building RAG application container with Docker..."
docker-compose -f docker-compose.docker.yml build

# Start services
echo "🚀 Starting RAG application with Docker..."
docker-compose -f docker-compose.docker.yml up -d

# Wait for the service to be ready
echo "⏳ Waiting for RAG application to start..."
sleep 10

# Check if we need to pull a model
echo "🔍 Checking available models..."
if ! ollama list | grep -q llama3.2:3b; then
    echo "📥 Downloading Llama 3.2 (3B) model..."
    ollama pull llama3.2:3b
else
    echo "✅ Llama 3.2 (3B) model already available"
fi

echo "✅ Docker setup complete!"
echo ""
echo "🌐 Access your Local RAG System at: http://localhost:8501"
echo "🤖 Local Ollama API at: http://localhost:11434"
echo ""
echo "Docker-specific commands:"
echo "  docker-compose -f docker-compose.docker.yml logs -f  # view logs"
echo "  docker-compose -f docker-compose.docker.yml down     # stop services"
echo "  make -f Makefile.docker health                       # check health"
echo ""
echo "To pull more models:"
echo "  ollama pull llama3.2:8b"
echo "  ollama pull mistral:7b"
echo "  ollama list  # to see all available models"