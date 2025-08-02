#!/bin/bash

# Setup script for Local RAG System

echo "🐳 Setting up Local RAG System..."

# Create necessary directories
mkdir -p data/chroma_db data/documents models/ollama_models

# Build containers
echo "📦 Building containers..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
sleep 30

# Pull a small model to start with
echo "📥 Downloading Llama 3.2 (3B) model..."
docker-compose exec ollama ollama pull llama3.2:3b

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your Local RAG System at: http://localhost:8501"
echo "🤖 Ollama API available at: http://localhost:11434"
echo ""
echo "To pull more models:"
echo "  docker-compose exec ollama ollama pull llama3.2:8b"
echo "  docker-compose exec ollama ollama pull mistral:7b"
echo ""
echo "To stop the system:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"