# Technology Stack

## Core Technologies
- **Python 3.11+**: Primary programming language
- **Reflex**: Python web framework for UI (≥0.8.4)
- **FastAPI**: Backend API framework with async support
- **ChromaDB**: Vector database for embeddings
- **Ollama**: Local LLM runtime
- **SentenceTransformers**: For embeddings generation

## Infrastructure & Deployment
- **Container Runtime**: Podman (primary) / Docker (alternative)
- **Monitoring**: Prometheus + Grafana
- **Process Management**: Docker Compose / Podman Compose
- **Health Checks**: Built-in health monitoring endpoints

## Development Tools
- **Testing**: pytest with comprehensive test suite
- **Coverage**: pytest-cov with 80% minimum coverage requirement
- **Code Quality**: Configured linting and formatting (via Makefile)
- **Async Support**: Full async/await support in testing and runtime

## File Formats Supported
- **Documents**: TXT, PDF, MD, and various document formats
- **Configuration**: YAML, JSON, ENV files
- **Deployment**: Docker Compose, Kubernetes manifests

## Database & Storage
- **Vector Storage**: ChromaDB with persistent storage
- **Document Processing**: Intelligent PDF processing with chunking
- **Caching**: Performance caching for optimized responses