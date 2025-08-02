# Local RAG System 🤖

A **fully local RAG (Retrieval-Augmented Generation) system** that runs completely offline using Docker containers. This system combines efficient document retrieval with local LLM generation to create an intelligent question-answering system that processes your documents without external API calls.

## 🚀 Quick Start

### Option 1: Automated Setup
```bash
# Clone or navigate to project directory
cd rag-example

# Run automated setup
chmod +x setup.sh && ./setup.sh
```

### Option 2: Using Makefile
```bash
make setup
```

### Option 3: Manual Setup
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Download initial model
docker-compose exec ollama ollama pull llama3.2:3b
```

## 🌐 Access Your System

- **Streamlit UI**: http://localhost:8501 (primary interface)
- **FastAPI Docs**: http://localhost:8000/docs (API documentation)
- **Ollama API**: http://localhost:11434 (LLM server)

## ✨ Features

- ✅ **Completely Offline** - No internet required after setup
- ✅ **Data Privacy** - Everything stays on your machine
- ✅ **Smart Chunking** - Semantic document splitting for optimal retrieval
- ✅ **Adaptive Retrieval** - Efficiency-optimized context selection
- ✅ **Multiple LLMs** - Switch between different Ollama models
- ✅ **Real-time Metrics** - Token usage and efficiency monitoring
- ✅ **Web Interface** - User-friendly Streamlit UI
- ✅ **REST API** - Full FastAPI backend with auto-documentation
- ✅ **MCP Protocol** - Standardized tool interface
- ✅ **Docker Containerized** - Easy deployment and scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │◄──►│   FastAPI        │◄──►│   ChromaDB      │
│   Web UI        │    │   REST API       │    │   Vector Store  │
│   Port: 8501    │    │   Port: 8000     │    │   Local Storage │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────►│   Ollama LLM    │
                        │   Port: 11434   │
                        │   Local Models  │
                        └─────────────────┘
```

### Core Components
- **Streamlit UI**: Document management and chat interface
- **FastAPI Backend**: REST API with automatic documentation
- **RAG Engine**: Smart chunking and adaptive retrieval
- **MCP Server**: Model Context Protocol for tool integration
- **Ollama**: Local LLM server supporting multiple models
- **ChromaDB**: Local vector database with persistence

## 📊 Performance Optimizations

### Smart Chunking Strategy
- **Semantic Boundaries**: Splits by paragraphs/sentences, not arbitrary tokens
- **Optimal Size**: 400 tokens per chunk for best retrieval performance
- **Context Overlap**: 50-token overlap for continuity
- **Edge Case Handling**: Manages short documents and large paragraphs

### Adaptive Retrieval System
- **Relevance Filtering**: Only retrieves chunks above 0.7 similarity threshold
- **Token Management**: Stops at context limits to prevent overflow
- **Quality First**: Prioritizes high-relevance chunks over quantity
- **Query Analysis**: Adapts chunk count based on query complexity

### Efficiency Metrics
- **Real-time Monitoring**: Track token usage and response times
- **Configurable Limits**: Adjust similarity thresholds and context windows
- **Performance Ratios**: Monitor chunks-per-token efficiency

## 🔧 Available Models

```bash
# Small models (3-4GB RAM)
make pull-model MODEL=llama3.2:3b
make pull-model MODEL=phi3:mini

# Medium models (8GB RAM)
make pull-model MODEL=llama3.2:8b
make pull-model MODEL=mistral:7b

# Large models (16GB+ RAM)
make pull-model MODEL=llama3.1:70b
make pull-model MODEL=codellama:34b
```

## 💾 Resource Requirements

| Component | Minimum RAM | Recommended RAM |
|-----------|-------------|-----------------|
| RAG App | 2GB | 4GB |
| Ollama + 3B Model | 4GB | 8GB |
| Ollama + 8B Model | 8GB | 16GB |
| **Total System** | **6GB** | **20GB** |

## 🛠️ Development Commands

### Container Management
```bash
make build          # Build all containers
make start          # Start services
make stop           # Stop services
make logs           # View logs
make health         # Check system health
```

### Shell Access
```bash
make shell-rag      # Access RAG app container
make shell-ollama   # Access Ollama container
```

### Testing
```bash
# Run system integration tests
python scripts/test_system.py

# Run performance benchmarks
python scripts/benchmark.py
```

## 📚 Usage Examples

### Document Upload via UI
1. Navigate to http://localhost:8501
2. Use sidebar "Add Documents" or "Bulk Upload"
3. Start asking questions in the chat interface

### Document Upload via API
```python
import requests

documents = [
    {
        "title": "My Document",
        "content": "Document content here...",
        "source": "api_upload"
    }
]

response = requests.post(
    "http://localhost:8000/documents",
    json=documents
)
```

### Query via API
```python
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "What is machine learning?",
        "max_chunks": 3
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
```

## 🧪 Testing

### System Integration Tests
```bash
python scripts/test_system.py
```
Tests all major functionality:
- Health checks
- Document upload
- Query processing
- Settings management

### Performance Benchmarking
```bash
python scripts/benchmark.py
```
Measures:
- Response times
- Token efficiency
- Concurrent query performance
- Throughput metrics

## 🔍 Troubleshooting

### Check System Status
```bash
make health
docker-compose ps
```

### View Logs
```bash
make logs                    # All services
docker-compose logs ollama   # Ollama only
docker-compose logs rag-app  # RAG app only
```

### Common Issues

**Ollama not responding:**
```bash
docker-compose restart ollama
docker-compose exec ollama ollama list  # Check available models
```

**Out of memory:**
- Use smaller models (3B instead of 8B)
- Reduce `max_context_tokens` in settings
- Increase Docker memory limits

**Slow responses:**
- Check if model is fully loaded: `docker-compose logs ollama`
- Reduce similarity threshold for more results
- Use faster models like `phi3:mini`

### Clean Restart
```bash
docker-compose down
docker-compose up -d
```

## 📁 Project Structure

```
rag-example/
├── app/                    # Python application
│   ├── main.py            # FastAPI REST API
│   ├── rag_backend.py     # RAG engine
│   ├── mcp_server.py      # MCP protocol server
│   ├── agent_ui.py        # Streamlit UI
│   └── requirements.txt   # Dependencies
├── data/                   # Persistent storage
│   ├── chroma_db/         # Vector database
│   └── documents/         # Document uploads
├── models/                 # Model storage
│   └── ollama_models/     # Ollama model files
├── scripts/               # Utility scripts
│   ├── test_system.py     # Integration tests
│   └── benchmark.py       # Performance tests
├── docs/                  # Documentation
├── agents/                # Agent configurations
├── planning/              # Project planning
├── docker-compose.yml     # Service orchestration
├── Dockerfile.rag-app     # RAG app container
├── Dockerfile.ollama      # Ollama container
├── setup.sh              # Automated setup
├── Makefile              # Development commands
└── README.md             # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python scripts/test_system.py`
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM serving
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [Streamlit](https://streamlit.io/) for the web interface
- [FastAPI](https://fastapi.tiangolo.com/) for the REST API