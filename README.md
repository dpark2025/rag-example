# Local RAG System with Reflex UI 🚀

A **production-ready, fully local RAG (Retrieval-Augmented Generation) system** with a comprehensive document management interface. This enterprise-grade system runs completely offline, combining intelligent document processing with local LLM generation to create a powerful question-answering platform that processes your documents without external API calls.

**🚀 Current Status**: **PRODUCTION READY** - Feature-complete system with full document lifecycle management, PDF processing, monitoring stack, and enterprise-grade capabilities.

## 🎯 Features

### 🔒 **Privacy & Security**
- **100% Local Processing**: All data stays on your infrastructure - zero external API calls
- **Enterprise Security**: Container security, secrets management, SSL/TLS support
- **Data Privacy**: Complete control over your sensitive documents and queries

### 📚 **Document Management**
- **Complete Document Lifecycle**: Upload, process, manage, and delete documents
- **Multi-Format Support**: Text files, PDFs, and various document formats
- **Drag-and-Drop Upload**: Modern file upload with progress tracking
- **Bulk Operations**: Process multiple documents simultaneously
- **Smart Processing**: Intelligent document type detection and optimization

### 💬 **Intelligent Chat Interface**
- **Modern UI**: Built with Reflex framework for responsive, real-time interactions
- **Source Attribution**: See exactly which documents and chunks informed each response
- **Real-time Updates**: WebSocket-powered live updates and status tracking
- **Enhanced UX**: Auto-scroll, keyboard shortcuts, typing indicators

### ⚡ **Performance & Monitoring**
- **Production Monitoring**: Prometheus + Grafana stack with health checks
- **Performance Metrics**: Real-time response time and resource usage tracking
- **Smart Chunking**: Semantic document processing with configurable similarity thresholds
- **Error Recovery**: Comprehensive error handling and recovery mechanisms

### 🏗️ **Production Infrastructure**
- **Container Orchestration**: Docker/Podman support with monitoring
- **Health Monitoring**: Automated health checks and system diagnostics
- **CI/CD Ready**: Automated testing and deployment pipelines
- **Scalable Architecture**: Multi-service architecture for enterprise deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Reflex UI      │◄──►│   RAG Backend    │◄──►│   ChromaDB      │
│  - Chat + Docs  │    │   - FastAPI v1   │    │   - Vector DB   │
│  - Port 3000    │    │   - Document Mgmt│    │   - Embeddings  │
│  - Real-time UI │    │   - PDF Process  │    │   - Port 8002   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        │
         │              ┌─────────────────┐                │
         │              │   Monitoring    │                │
         │              │   - Prometheus  │                │
         │              │   - Grafana     │                │
         │              │   - Health Chks │                │
         │              └─────────────────┘                │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                        ┌─────────────────┐
                        │   Local LLM     │
                        │   - Ollama      │
                        │   - Port 11434  │
                        └─────────────────┘
```

**Core Components:**
- **Reflex UI**: Complete document management + chat interface
- **FastAPI Backend**: Full v1 API with document lifecycle endpoints  
- **Document Processing**: Multi-format PDF processing with intelligence
- **Monitoring Stack**: Production-grade Prometheus + Grafana monitoring
- **Vector Database**: ChromaDB with persistent storage and backup
- **Local LLM**: Ollama with automatic service discovery

## 🚀 Quick Start

### Production Deployment (Recommended)
```bash
# 1. Production setup with monitoring
make setup-monitoring  # Sets up Prometheus + Grafana
docker-compose -f docker-compose.production.yml up -d

# 2. Access interfaces
# - Main UI: http://localhost:3000
# - API Docs: http://localhost:8000/docs  
# - Monitoring: http://localhost:3001 (Grafana admin/admin)
# - Metrics: http://localhost:9090 (Prometheus)
```

### Development Setup (2 Minutes)
```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Start backend services  
make setup

# 3. Start Reflex UI (in new terminal)
cd app/reflex_app && reflex run

# 4. Visit http://localhost:3000
```

### Docker/Podman Deployment
```bash
# Complete stack with monitoring
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d

# Backend only (lightweight)
make start  # Uses Podman by default
```

### Prerequisites

**1. Install Ollama** (required for local LLM):
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull a model (e.g., llama3.2:3b for lower memory usage)
ollama pull llama3.2:3b
```

**2. Python 3.11+** with pip and Podman/Docker

## 🔌 API Endpoints

The system provides a comprehensive REST API with full v1 endpoints:

### Document Management API
- `GET /api/v1/documents` - List all documents with metadata
- `POST /api/v1/documents/upload` - Upload single document  
- `POST /api/v1/documents/bulk-upload` - Bulk document upload
- `DELETE /api/v1/documents/{doc_id}` - Delete specific document
- `DELETE /api/v1/documents/bulk` - Bulk document deletion
- `GET /api/v1/documents/{doc_id}/status` - Document processing status
- `GET /api/v1/documents/stats` - Storage and processing statistics

### Query & Search API
- `POST /query` - Submit RAG queries with source attribution
- `GET /settings` - Retrieve RAG configuration settings
- `POST /settings` - Update RAG parameters (similarity, max chunks)

### Upload Management API  
- `GET /api/v1/upload/tasks` - List upload tasks and progress
- `GET /api/v1/upload/tasks/{task_id}` - Get specific upload task status
- `POST /api/v1/upload/cleanup` - Clean up completed upload tasks
- `GET /api/v1/upload/stats` - Upload processing statistics

### Health & Monitoring API
- `GET /health` - System health status
- `GET /health/errors` - Error statistics and recent issues
- `GET /health/metrics` - Performance metrics and resource usage
- `GET /processing/status` - Document processing queue status

**👉 Complete API documentation available at: http://localhost:8000/docs**

## 📖 Usage

### Document Management
1. **Access the UI**: Open http://localhost:3000 in your browser
2. **Upload Documents**: 
   - Navigate to the Documents page
   - Drag-and-drop files or use the upload button
   - Support multiple formats: TXT, PDF, MD, etc.
   - Monitor processing status in real-time
3. **Manage Documents**: View, search, filter, and delete documents
4. **Bulk Operations**: Upload multiple files, bulk delete operations

### Intelligent Chat
1. **Ask Questions**: Type questions about your uploaded documents
2. **View Sources**: Click source badges to see which documents informed responses
3. **Real-time Responses**: Watch responses generate with typing indicators
4. **Adjust Settings**: Modify similarity threshold and max chunks for different results

### Monitoring & Administration
1. **Health Monitoring**: Visit http://localhost:8000/health for system status
2. **Performance Metrics**: Access Grafana dashboard at http://localhost:3001
3. **API Documentation**: Explore full API at http://localhost:8000/docs
4. **System Diagnostics**: Use built-in health checks and error reporting

### Production Features
- **Error Recovery**: Automatic retry and graceful error handling
- **Performance Optimization**: Intelligent caching and resource management
- **Security**: Container security and data privacy protection
- **Backup & Recovery**: Persistent data storage with backup capabilities

## 🛠️ Development

### Project Structure
```
rag-example/
├── app/
│   ├── reflex_app/        # Reflex UI application
│   │   ├── components/    # UI components (chat, documents, etc.)
│   │   ├── state/         # State management
│   │   ├── services/      # API client
│   │   └── pages/         # Page routes
│   ├── main.py            # FastAPI backend
│   ├── rag_backend.py     # RAG processing engine
│   └── requirements.txt   # Backend dependencies
├── requirements.reflex.txt # Reflex UI dependencies
├── docs/                  # Documentation
│   ├── reflex_migration_progress.md
│   └── guided_test.md
└── scripts/               # Utility scripts
```

### Testing

Comprehensive testing suite with multiple test levels:
```bash
# Quick development tests (~30s)
make test-quick

# Complete test suite with coverage
make test-all

# Run specific test categories
make test-unit          # Unit tests
make test-integration   # API integration tests
make test-e2e          # End-to-end tests

# Test with live system health checks
make test-with-health

# Generate coverage reports
make coverage          # HTML report in htmlcov/
```

### Production Deployment

Multiple deployment options with monitoring:
```bash
# Production deployment with full monitoring stack
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d

# Development with containers
docker-compose -f docker-compose.yml up -d

# Backend-only deployment (Podman)
make start

# Full system health check
make health
```

## 🔧 Configuration

### Environment Variables
- `OLLAMA_HOST`: Ollama server URL (default: `http://localhost:11434`)
- `API_BASE_URL`: FastAPI backend URL (default: `http://localhost:8000`)
- `REFLEX_PORT`: Reflex UI port (default: `3000`)

### Model Selection
```bash
# List available models
ollama list

# Pull different models
ollama pull llama3.2:3b    # Smaller, faster
ollama pull llama3.1:8b    # Balanced
ollama pull mistral:7b     # Alternative model
```

## 📊 Resource Requirements

| Component | Minimum RAM | Recommended RAM | Disk Space |
|-----------|-------------|-----------------|------------|
| Reflex UI | 512MB | 1GB | 200MB |
| FastAPI Backend | 2GB | 4GB | 500MB |
| Ollama + 3B Model | 4GB | 8GB | 3GB |
| Ollama + 8B Model | 8GB | 16GB | 8GB |
| ChromaDB + Monitoring | 1GB | 2GB | Varies |
| **Production System** | **8GB** | **20GB** | **5GB+** |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Roadmap
- ✅ **Phase 1**: Foundation Setup - Complete
- ✅ **Phase 2**: Chat Interface - Complete  
- ✅ **Phase 3**: Document Management - Complete
- ✅ **Phase 4**: PDF Processing & Intelligence - Complete
- ✅ **Phase 5**: Production Readiness & UX Polish - Complete
- ✅ **Production Infrastructure**: Monitoring, CI/CD, Security - Complete
- 🚀 **Status**: **PRODUCTION READY** - Enterprise deployment ready

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Reflex](https://reflex.dev/) - The Python web framework
- Powered by [Ollama](https://ollama.ai/) - Local LLM runtime
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- Embeddings via [SentenceTransformers](https://www.sbert.net/)

## 🐛 Troubleshooting

### Common Issues

**Ollama Connection Error**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama
ollama serve
```

**Port Already in Use**
```bash
# Kill existing processes
lsof -ti:3000 | xargs kill -9  # Reflex UI
lsof -ti:8000 | xargs kill -9  # RAG Backend
lsof -ti:8001 | xargs kill -9  # Reflex Backend
lsof -ti:9090 | xargs kill -9  # Prometheus
```

**System Health Issues**
```bash
# Check system health
make health

# View system logs
make logs

# Clean restart
make restart
```

**Container Issues**
```bash
# Clean up containers
make clean

# Fresh deployment
make setup
```

**Performance Issues**
```bash
# Check monitoring dashboard
# Visit: http://localhost:3001 (Grafana)
# Default credentials: admin/admin

# Check resource usage
docker stats  # or podman stats
```

For more detailed troubleshooting, see [docs/guided_test.md](docs/guided_test.md)