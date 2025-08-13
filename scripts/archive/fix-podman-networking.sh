#!/bin/bash

# Fix Podman networking configuration for RAG system
# This script helps configure the environment for Podman compatibility

set -e

echo "=== RAG System Podman Networking Fix ==="
echo

# Check if running with Podman or Docker
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
    COMPOSE_CMD="podman-compose"
    echo "✓ Podman detected"
elif command -v docker &> /dev/null; then
    CONTAINER_ENGINE="docker"
    COMPOSE_CMD="docker-compose"
    echo "✓ Docker detected"
else
    echo "❌ Neither Podman nor Docker found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ Found existing .env file"
fi

# Configure OLLAMA_HOST for the detected platform
echo "🔧 Configuring OLLAMA_HOST for $CONTAINER_ENGINE..."

if [ "$CONTAINER_ENGINE" = "podman" ]; then
    # For Podman, try different host options
    echo "Setting up for Podman..."
    
    # Check if host.containers.internal works
    if podman run --rm alpine ping -c 1 host.containers.internal &>/dev/null 2>&1; then
        OLLAMA_HOST="host.containers.internal:11434"
        echo "✓ Using host.containers.internal"
    else
        # Try to detect host IP
        HOST_IP=$(ip route | grep default | awk '{print $3}' | head -1 2>/dev/null || echo "")
        if [ -n "$HOST_IP" ]; then
            OLLAMA_HOST="$HOST_IP:11434"
            echo "✓ Using host IP: $HOST_IP"
        else
            # Fallback to common values
            echo "⚠️  Could not auto-detect host IP, using fallback"
            OLLAMA_HOST="10.0.2.2:11434"
        fi
    fi
else
    # For Docker
    OLLAMA_HOST="host.docker.internal:11434"
    echo "✓ Using host.docker.internal for Docker"
fi

# Update .env file
if grep -q "^OLLAMA_HOST=" .env; then
    sed -i.bak "s|^OLLAMA_HOST=.*|OLLAMA_HOST=$OLLAMA_HOST|" .env
else
    echo "OLLAMA_HOST=$OLLAMA_HOST" >> .env
fi

echo "✓ Updated OLLAMA_HOST to: $OLLAMA_HOST"

# Test connectivity if Ollama is running
echo
echo "🧪 Testing Ollama connectivity..."
if curl -s "http://${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
    echo "✅ Ollama is accessible at $OLLAMA_HOST"
elif curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo "✅ Ollama is running on localhost:11434"
    echo "   Container networking will route through configured host"
else
    echo "⚠️  Ollama not accessible - make sure it's running:"
    echo "   For host installation: ollama serve"
    echo "   For container: podman run -d -p 11434:11434 ollama/ollama"
fi

# Clean up and restart containers with new config
echo
echo "🔄 Restarting containers with new networking configuration..."
$COMPOSE_CMD down 2>/dev/null || true
$COMPOSE_CMD up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo
echo "📊 Checking service status..."
$COMPOSE_CMD ps

echo
echo "🎯 Configuration complete!"
echo "📋 Summary:"
echo "   - Container Engine: $CONTAINER_ENGINE"
echo "   - OLLAMA_HOST: $OLLAMA_HOST"
echo "   - Environment file: .env"
echo
echo "🌐 You can now access:"
echo "   - Reflex UI: http://localhost:3000"
echo "   - FastAPI Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo "   - ChromaDB: http://localhost:8002"
echo
echo "🔍 Check logs if needed:"
echo "   $COMPOSE_CMD logs -f"
echo