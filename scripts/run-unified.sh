#!/bin/bash
# Run script for unified RAG container

set -e

# Check if podman or docker is available
if command -v podman &> /dev/null; then
    CONTAINER_CMD=podman
elif command -v docker &> /dev/null; then
    CONTAINER_CMD=docker
else
    echo "❌ Neither podman nor docker found. Please install one."
    exit 1
fi

# Stop and remove any existing container
echo "🧹 Stopping existing container..."
$CONTAINER_CMD stop local-rag-unified 2>/dev/null || true
$CONTAINER_CMD rm local-rag-unified 2>/dev/null || true

# Run the unified container
echo "🚀 Starting unified RAG container..."
$CONTAINER_CMD run -d \
    --name local-rag-unified \
    -p 3000:3000 \
    -p 3001:3001 \
    -p 8000:8000 \
    -p 8002:8002 \
    -v ./data:/app/data:Z \
    -e OLLAMA_HOST=${OLLAMA_HOST:-host.containers.internal:11434} \
    local-rag-unified:latest

echo "⏳ Waiting for services to start..."
echo "   This may take 60-90 seconds for full initialization..."

# Wait for readiness
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8000/ready >/dev/null 2>&1; then
        echo "✅ Application ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - checking readiness..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️ Application may still be starting up. Check logs:"
    echo "  $CONTAINER_CMD logs local-rag-unified"
    echo ""
fi

# Show status
echo ""
echo "📊 Service status:"
curl -s http://localhost:8000/ready | python3 -m json.tool 2>/dev/null || echo "Ready endpoint not accessible yet"

echo ""
echo "🌐 Access points:"
echo "  - Frontend: http://localhost:3000"
echo "  - WebSocket: ws://localhost:3001/_event"
echo "  - API: http://localhost:8000"
echo "  - ChromaDB: http://localhost:8002"
echo "  - Health: http://localhost:8000/health"
echo "  - Ready: http://localhost:8000/ready"

echo ""
echo "📝 To view logs:"
echo "  $CONTAINER_CMD logs -f local-rag-unified"

echo ""
echo "🛑 To stop:"
echo "  $CONTAINER_CMD stop local-rag-unified"