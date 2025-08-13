#!/bin/bash
# Build script for unified RAG container

set -e

echo "🔨 Building unified RAG container..."

# Check if podman or docker is available
if command -v podman &> /dev/null; then
    CONTAINER_CMD=podman
    echo "📦 Using Podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD=docker  
    echo "🐳 Using Docker"
else
    echo "❌ Neither podman nor docker found. Please install one."
    exit 1
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
$CONTAINER_CMD stop local-rag-unified 2>/dev/null || true
$CONTAINER_CMD rm local-rag-unified 2>/dev/null || true

# Build the unified image
echo "🏗️ Building unified container image..."
$CONTAINER_CMD build -f Dockerfile.unified -t local-rag-unified:latest .

echo "✅ Build complete!"
echo ""
echo "🚀 To run the unified container:"
echo "  $CONTAINER_CMD run -d --name local-rag-unified \\"
echo "    -p 3000:3000 -p 8000:8000 \\"
echo "    -v ./data:/app/data:Z \\"
echo "    -e OLLAMA_HOST=${OLLAMA_HOST:-host.containers.internal:11434} \\"
echo "    local-rag-unified:latest"
echo ""
echo "🔍 To check readiness:"
echo "  curl http://localhost:8000/ready"
echo ""
echo "🌐 Access points:"
echo "  - Frontend: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - Health: http://localhost:8000/health"
echo "  - Ready: http://localhost:8000/ready"