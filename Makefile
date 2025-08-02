.PHONY: build start stop logs shell-rag shell-ollama pull-model health

# Build all containers
build:
	docker-compose build

# Start the system
start:
	docker-compose up -d

# Stop the system  
stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Shell into RAG app container
shell-rag:
	docker-compose exec rag-app bash

# Shell into Ollama container
shell-ollama:
	docker-compose exec ollama bash

# Pull a new model (usage: make pull-model MODEL=llama3.2:8b)
pull-model:
	docker-compose exec ollama ollama pull $(MODEL)

# Check system health
health:
	@echo "Checking system health..."
	@curl -s http://localhost:8501/_stcore/health > /dev/null && echo "✅ RAG App: Healthy" || echo "❌ RAG App: Unhealthy"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama: Healthy" || echo "❌ Ollama: Unhealthy"

# Complete setup
setup: build start
	@echo "⏳ Waiting for services to be ready..."
	@sleep 30
	@echo "📥 Downloading initial model..."
	@docker-compose exec ollama ollama pull llama3.2:3b
	@echo "✅ Setup complete! Visit http://localhost:8501"