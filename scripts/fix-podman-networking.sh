#!/bin/bash

echo "🔧 Fixing Podman networking and container issues..."

# Stop and remove any existing containers
echo "Cleaning up existing containers..."
podman stop local-rag-app 2>/dev/null || true
podman rm local-rag-app 2>/dev/null || true

# Clean up any compose services
echo "Stopping compose services..."
podman-compose down 2>/dev/null || true

# Remove any dangling containers and images
echo "Removing any dangling containers..."
podman container prune -f 2>/dev/null || true

# Build fresh with no cache to ensure new networking code
echo "Building fresh container (with updated networking code)..."
podman-compose build --no-cache

# Start with new networking
echo "Starting with proper Podman networking..."
podman-compose up -d

# Wait a moment for startup
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
echo "📊 Checking service status..."
podman-compose ps

echo ""
echo "✅ Podman networking fixed!"
echo ""
echo "🌐 You should now be able to access:"
echo "  - Streamlit UI: http://localhost:8501"
echo "  - FastAPI Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "🔍 Check logs if needed:"
echo "  podman-compose logs -f"
echo ""
echo "🩺 The container now:"
echo "  - Auto-detects Podman networking and connects to Ollama at 10.0.2.2:11434"
echo "  - Runs both FastAPI (port 8000) and Streamlit (port 8501) services"
echo "  - Has proper health checks for both services"