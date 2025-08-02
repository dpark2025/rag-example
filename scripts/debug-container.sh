#!/bin/bash

echo "🐛 Debugging container issues..."

echo "📊 Container status:"
podman-compose ps

echo ""
echo "🔍 Recent logs from RAG app:"
podman-compose logs --tail=50 rag-app

echo ""
echo "🌐 Testing network connectivity:"
echo "- Testing if container is listening on port 8000:"
podman exec local-rag-app netstat -tlnp 2>/dev/null | grep :8000 || echo "Port 8000 not listening"

echo "- Testing if container is listening on port 8501:"  
podman exec local-rag-app netstat -tlnp 2>/dev/null | grep :8501 || echo "Port 8501 not listening"

echo ""
echo "🔧 Testing if processes are running in container:"
podman exec local-rag-app ps aux | grep -E "(python|uvicorn|streamlit)" || echo "No Python processes found"

echo ""
echo "📡 Testing Ollama connectivity from container:"
podman exec local-rag-app curl -s --connect-timeout 5 http://10.0.2.2:11434/api/tags || echo "Cannot reach Ollama from container"

echo ""
echo "🏥 Manual health check from inside container:"
podman exec local-rag-app curl -s http://localhost:8000/health || echo "Internal health check failed"