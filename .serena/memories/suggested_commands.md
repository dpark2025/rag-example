# Essential Development Commands

## Setup and Management
- `make setup` - Complete backend setup (check-ollama + build + start + model)
- `make check-ollama` - Verify Ollama is installed and running
- `make build` - Build RAG backend container with Podman
- `make start` - Start RAG backend services (requires Ollama running)
- `make stop` - Stop RAG backend services
- `make restart` - Clean restart (clean + build + start)
- `make clean` - Remove existing containers for fresh start

## Development Workflow
- `make start-ui` - Start Reflex UI natively (recommended for development)
- `cd app/reflex_app && reflex run` - Alternative Reflex UI startup
- `make health` - Check system health status
- `make logs` - View real-time container logs
- `make shell-rag` - Access RAG application container shell

## Testing Commands
- `make test-quick` - Run fast unit tests (~30s)
- `make test-unit` - Run complete unit test suite
- `make test-integration` - Run API integration tests
- `make test-all` - Run complete test suite with coverage
- `make coverage` - Generate HTML coverage report
- `make lint` - Run code quality checks

## Model Management
- `make pull-model MODEL=llama3.2:3b` - Download specific Ollama model
- `make list-models` - List available Ollama models
- `ollama serve` - Start Ollama service manually
- `ollama list` - List installed models

## Production Deployment
- `docker-compose -f docker-compose.production.yml up -d` - Production deployment
- `docker-compose -f docker-compose.monitoring.yml up -d` - Start monitoring stack
- `make setup-monitoring` - Setup Prometheus + Grafana

## Access Points
- **Reflex UI**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090