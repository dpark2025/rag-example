.PHONY: build start stop logs shell-rag pull-model health check-ollama clean restart help build-reflex start-reflex stop-reflex start-ui logs-reflex test test-unit test-integration test-e2e test-all test-quick test-watch clean-tests coverage lint format install-test-deps

# Show help information  
help:
	@echo "🐳 Local RAG System - Podman Commands (Default)"
	@echo "=============================================="
	@echo ""
	@echo "📋 Setup & Management:"
	@echo "  setup           Complete backend setup (check-ollama + build + start + model)"
	@echo "  check-ollama    Verify Ollama is installed and running"
	@echo "  build           Build RAG backend container with Podman (backend + chromadb)"
	@echo "  start           Start RAG backend services with Podman (requires Ollama running)"
	@echo "  stop            Stop RAG backend services"
	@echo "  restart         Clean restart (clean + build + start)"
	@echo "  clean           Remove existing containers for fresh start"
	@echo ""
	@echo "📊 Monitoring & Access:" 
	@echo "  health          Check system health status"
	@echo "  logs            View real-time container logs"
	@echo "  shell-rag       Access RAG application container shell"
	@echo ""
	@echo "🤖 Model Management:"
	@echo "  pull-model      Download Ollama model (usage: make pull-model MODEL=llama3.2:8b)"
	@echo "  list-models     List available Ollama models"
	@echo ""
	@echo "🌐 Access Points:"
	@echo "  FastAPI Backend: http://localhost:8000"
	@echo "  FastAPI Docs:    http://localhost:8000/docs"  
	@echo "  Ollama API:      http://localhost:11434"
	@echo "  ChromaDB:        http://localhost:8002"
	@echo ""
	@echo "🖥️  Reflex UI Options:"
	@echo "  start-ui        Start Reflex UI natively (recommended)"
	@echo "  build-reflex    Build Reflex container (experimental)"
	@echo "  start-reflex    Start Reflex in container (experimental)"
	@echo "  stop-reflex     Stop Reflex container"
	@echo "  logs-reflex     View Reflex container logs"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  test-quick      Run fast unit tests (~30s)"
	@echo "  test-unit       Run complete unit test suite"
	@echo "  test-integration Run API integration tests"
	@echo "  test-all        Run complete test suite with coverage"
	@echo "  coverage        Generate HTML coverage report"
	@echo "  lint            Run code quality checks"
	@echo ""
	@echo "🛠️ Troubleshooting:"
	@echo "  ./fix-container.sh            Fix container name conflicts"
	@echo "  make clean && make start      Fresh restart"
	@echo ""
	@echo "💡 Examples:"
	@echo "  make setup                    # Backend setup"
	@echo "  make pull-model MODEL=phi3:mini    # Download small model"
	@echo "  make restart                  # Clean restart"
	@echo ""
	@echo "🔄 For Docker: Use 'make -f Makefile.docker <command>' instead"
	@echo ""

# Check if Ollama is installed and running
check-ollama:
	@echo "🔍 Checking Ollama..."
	@command -v ollama >/dev/null 2>&1 || { echo "❌ Ollama not installed. Visit https://ollama.ai/download"; exit 1; }
	@curl -s http://localhost:11434/api/tags >/dev/null 2>&1 || { echo "❌ Ollama not running. Run: ollama serve"; exit 1; }
	@echo "✅ Ollama is installed and running"

# Build RAG container with Podman (backend + chromadb only)
build:
	podman-compose -f docker-compose.backend.yml build

# Start the RAG application with Podman (backend + chromadb only)
start: check-ollama
	podman-compose -f docker-compose.backend.yml up -d

# Stop the RAG application
stop:
	podman-compose -f docker-compose.backend.yml down

# View logs
logs:
	@echo "📋 Showing logs for all services..."
	@echo "=== RAG Backend Logs ==="
	@podman-compose -f docker-compose.backend.yml logs --tail 20 rag-backend || true
	@echo ""
	@echo "=== ChromaDB Logs ==="
	@podman-compose -f docker-compose.backend.yml logs --tail 20 chromadb || true

# Shell into RAG app container
shell-rag:
	podman-compose -f docker-compose.backend.yml exec rag-backend bash

# Pull a new model (usage: make -f Makefile.podman pull-model MODEL=llama3.2:8b)
pull-model:
	ollama pull $(MODEL)

# List available models
list-models:
	ollama list

# Check system health
health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ RAG Backend: Healthy" || echo "❌ RAG Backend: Unhealthy"
	@curl -s http://localhost:8002/api/v2/heartbeat > /dev/null && echo "✅ ChromaDB: Healthy" || echo "❌ ChromaDB: Unhealthy"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama: Healthy" || echo "❌ Ollama: Unhealthy"
	@curl -s http://localhost:3000/ > /dev/null && echo "✅ Reflex UI: Healthy" || echo "ℹ️  Reflex UI: Not running (start with: make start-ui)"

# Clean up containers and restart fresh
clean:
	@echo "🧹 Cleaning up containers..."
	@podman stop local-rag-backend 2>/dev/null || true
	@podman rm local-rag-backend 2>/dev/null || true
	@podman stop local-rag-reflex 2>/dev/null || true
	@podman rm local-rag-reflex 2>/dev/null || true
	@podman-compose -f docker-compose.backend.yml down 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Restart with clean slate
restart: clean check-ollama build start
	@echo "🔄 System restarted successfully"

# Complete setup
setup: check-ollama build start
	@echo "⏳ Waiting for RAG application to be ready..."
	@sleep 10
	@echo "📥 Checking for initial model..."
	@ollama list | grep -q llama3.2:3b || ollama pull llama3.2:3b
	@echo "✅ Setup complete! Visit http://localhost:3000"

# Reflex UI Commands
# =================

# Start Reflex UI natively (recommended)
start-ui:
	@echo "🚀 Starting Reflex UI natively..."
	@./scripts/start_reflex.sh

# Build Reflex container (experimental)
build-reflex:
	@echo "🏗️ Building Reflex container..."
	podman build -f Dockerfile.reflex -t local-rag-reflex .

# Start Reflex container (experimental)
start-reflex: check-ollama
	@echo "🐳 Starting Reflex in container..."
	podman-compose -f docker-compose.reflex.yml up -d

# Stop Reflex container
stop-reflex:
	@echo "🛑 Stopping Reflex container..."
	podman-compose -f docker-compose.reflex.yml down

# View Reflex container logs
logs-reflex:
	@echo "📋 Viewing Reflex logs..."
	podman-compose -f docker-compose.reflex.yml logs -f reflex-app

# ========================================
# Testing Commands (Added by QA Engineer)
# ========================================

# Quick test cycle for development
test-quick:
	@echo "🏃 Running quick unit tests..."
	pytest tests/unit/ -v --tb=short -x --disable-warnings

# Unit tests
test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v --cov=app --cov-report=term-missing

# Integration tests
test-integration:
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ -v --tb=short

# End-to-end tests (requires running services)
test-e2e:
	@echo "🎯 Running end-to-end tests..."
	@echo "Note: Ensure RAG backend is running on localhost:8000"
	pytest tests/e2e/ -v --tb=short

# Complete test suite
test-all:
	@echo "🎪 Running complete test suite..."
	pytest -v --cov=app --cov-report=html --cov-report=term-missing

# Watch mode for development
test-watch:
	@echo "👀 Running tests in watch mode..."
	pytest-watch -- tests/unit/ -v --tb=short

# Coverage reporting
coverage:
	@echo "📊 Generating coverage report..."
	pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality
lint:
	@echo "🔍 Running code linting..."
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503 || true
	mypy app/ --ignore-missing-imports || true

format:
	@echo "🎨 Formatting code..."
	black app/ tests/ --line-length=100 || true
	isort app/ tests/ --profile black || true

# Install testing dependencies
install-test-deps:
	@echo "📦 Installing testing dependencies..."
	pip install -r requirements-test.txt

# Clean test artifacts
clean-tests:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf test-results.xml
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Test with service health check
test-with-health:
	@echo "🏥 Running tests with health checks..."
	make health
	make test-integration