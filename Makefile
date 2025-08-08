.PHONY: help start stop start-ui health logs clean restart build check-ollama setup pull-model

# Default target
help:
	@echo "🚀 Local RAG System - Essential Commands"
	@echo "========================================"
	@echo ""
	@echo "🎯 Quick Start:"
	@echo "  setup           Complete setup (ollama + build + start + model)"
	@echo "  start           Start backend services (FastAPI + ChromaDB)"
	@echo "  start-ui        Start Reflex UI (http://localhost:3000)"
	@echo "  health          Check all services status"
	@echo ""
	@echo "🔧 Management:"
	@echo "  stop            Stop backend services"
	@echo "  restart         Clean restart (clean + build + start)"
	@echo "  clean           Remove containers for fresh start"
	@echo "  logs            View service logs"
	@echo ""
	@echo "🤖 Models:"
	@echo "  pull-model      Download model (usage: make pull-model MODEL=llama3.2:3b)"
	@echo "  check-ollama    Verify Ollama is running"
	@echo ""
	@echo "🌐 Access Points:"
	@echo "  UI:       http://localhost:3000"
	@echo "  API:      http://localhost:8000"
	@echo "  ChromaDB: http://localhost:8002"
	@echo ""

# Check if Ollama is installed and running
check-ollama:
	@echo "🔍 Checking Ollama..."
	@command -v ollama >/dev/null 2>&1 || { echo "❌ Ollama not installed. Visit https://ollama.ai/download"; exit 1; }
	@curl -s http://localhost:11434/api/tags >/dev/null 2>&1 || { echo "❌ Ollama not running. Run: ollama serve"; exit 1; }
	@echo "✅ Ollama is installed and running"

# Build containers
build:
	@echo "🏗️ Building containers..."
	podman-compose -f docker-compose.backend.yml build

# Start backend services
start: check-ollama
	@echo "🚀 Starting backend services..."
	podman-compose -f docker-compose.backend.yml up -d
	@echo "⏳ Waiting for services to start..."
	@sleep 5
	@echo "✅ Backend services started"

# Stop backend services
stop:
	@echo "🛑 Stopping backend services..."
	podman-compose -f docker-compose.backend.yml down

# Start Reflex UI
start-ui:
	@echo "🖥️  Starting Reflex UI..."
	@./scripts/start_reflex.sh

# Check system health
health:
	@echo "🏥 Checking system health..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ RAG Backend: Healthy" || echo "❌ RAG Backend: Unhealthy"
	@curl -s http://localhost:8002/api/v1/heartbeat > /dev/null && echo "✅ ChromaDB: Healthy" || echo "❌ ChromaDB: Unhealthy"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama: Healthy" || echo "❌ Ollama: Unhealthy"
	@curl -s http://localhost:3000/ > /dev/null && echo "✅ Reflex UI: Healthy" || echo "ℹ️  Reflex UI: Not running (start with: make start-ui)"

# View service logs
logs:
	@echo "📋 Recent service logs..."
	@echo "=== RAG Backend ==="
	@podman-compose -f docker-compose.backend.yml logs --tail 20 rag-backend || true
	@echo ""
	@echo "=== ChromaDB ==="
	@podman-compose -f docker-compose.backend.yml logs --tail 20 chromadb || true

# Clean up containers
clean:
	@echo "🧹 Cleaning up..."
	@podman-compose -f docker-compose.backend.yml down 2>/dev/null || true
	@podman stop local-rag-backend 2>/dev/null || true
	@podman rm local-rag-backend 2>/dev/null || true
	@podman stop local-rag-chromadb 2>/dev/null || true
	@podman rm local-rag-chromadb 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Restart everything
restart: clean build start
	@echo "🔄 System restarted successfully"

# Complete setup from scratch
setup: check-ollama build start
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "📥 Ensuring model is available..."
	@ollama list | grep -q llama3.2:3b || ollama pull llama3.2:3b
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   Next: Run 'make start-ui' and visit http://localhost:3000"

# Pull Ollama model
pull-model:
	@echo "📥 Downloading model: $(MODEL)"
	ollama pull $(MODEL)
	@echo "✅ Model $(MODEL) downloaded"