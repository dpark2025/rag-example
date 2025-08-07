# Quick Start Guide

**This file has been moved to `docs/guides/quick_start.md`**

Please refer to the new location for the complete quick start guide:
- [Quick Start Guide](docs/guides/quick_start.md)

This file will be removed in a future version.

## 🚀 Prerequisites

1. **Ollama** - Install from https://ollama.ai/download
2. **Python 3.11+** with pip
3. **Podman** or **Docker** for containers
4. **Make** (usually pre-installed on macOS/Linux)

## ⚡ Production Quick Start (Recommended)

```bash
# 1. Production deployment with monitoring (use podman or docker)
podman-compose -f docker-compose.production.yml up -d
podman-compose -f docker-compose.monitoring.yml up -d

# Alternative: Use the networking fix script for automatic configuration
./scripts/fix-podman-networking.sh

# 2. Access production interfaces
# - Main UI: http://localhost:3000
# - Monitoring: http://localhost:3001 (Grafana: admin/admin)
# - API Docs: http://localhost:8000/docs
```

**🚀 Enterprise Features Available:**
- Complete document lifecycle management
- Multi-format PDF processing
- Production monitoring (Prometheus + Grafana)
- Health checks and error recovery
- Bulk operations and advanced search

## ⚡ Development Quick Start

```bash
# 1. Development backend services
make start

# 2. Start frontend UI
make start-ui
```

That's it! 🎉 System ready at http://localhost:3000

## 📋 Detailed Setup

### Step 1: Verify Prerequisites
```bash
# Check Ollama is running
ollama serve

# Pull a model (optional)
ollama pull llama3.2:3b

# Install Python dependencies
pip install -r requirements.reflex.txt
```

### Step 2: Start Backend Services
```bash
# Start containerized backend (FastAPI + ChromaDB)
make start

# Check everything is healthy
make health
```

**Expected Output:**
```
✅ RAG Backend: Healthy
✅ ChromaDB: Healthy  
✅ Ollama: Healthy
ℹ️  Reflex UI: Not running (start with: make start-ui)
```

### Step 3: Start Frontend UI
```bash
# Start Reflex UI with automated script
make start-ui
```

The startup script will automatically:
- ✅ Check dependencies and backend connectivity
- ✅ Set proper environment variables  
- ✅ Start Reflex on http://localhost:3000

### Step 4: Access the Full System
- **Main UI**: http://localhost:3000 (Complete document management + chat)
- **Document Dashboard**: http://localhost:3000/documents (Upload & manage documents)
- **API Docs**: http://localhost:8000/docs (Full v1 API documentation)
- **Health Monitoring**: http://localhost:8000/health (Real-time system health)
- **Grafana Dashboard**: http://localhost:3001 (Production monitoring - admin/admin)
- **Prometheus Metrics**: http://localhost:9090 (Raw metrics)

#### Port Architecture
The system uses multiple ports for different services:

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    HTTP Calls    ┌─────────────────┐
│  Frontend UI    │◄──────────────►│ Reflex Backend  │◄───────────────►│   RAG Backend   │
│  Port 3000      │                │  Port 8001      │                 │   Port 8000     │
│  (React)        │                │  (State Mgmt)   │                 │  (RAG Engine)   │
└─────────────────┘                └─────────────────┘                 └─────────────────┘
```

- **Port 3000**: Reflex Frontend (Complete UI with document management)
- **Port 8001**: Reflex Backend (State management, WebSocket, real-time updates)
- **Port 8000**: RAG Backend (FastAPI v1, document lifecycle, PDF processing)
- **Port 8002**: ChromaDB (Production vector database with persistence)
- **Port 11434**: Ollama (Local LLM server with auto-discovery)
- **Port 3001**: Grafana (Production monitoring dashboard)
- **Port 9090**: Prometheus (Metrics collection and alerting)

## 🔧 Development Commands

### Backend Management
```bash
make start          # Start backend containers
make stop           # Stop backend containers
make restart        # Clean restart
make logs           # View backend logs
make health         # Check all services
make clean          # Clean up containers
```

### Frontend Development  
```bash
make start-ui       # Start UI with script (recommended)
make build-reflex   # Build UI container (experimental)
make start-reflex   # Start UI in container (experimental)
```

### Testing & Validation
```bash
# Quick development tests
make test-quick                 # Fast unit tests (~30s)

# Comprehensive testing
make test-all                   # Full test suite with coverage
make test-integration           # API integration tests
make test-e2e                   # End-to-end user workflows

# System validation
make health                     # Complete system health check
python scripts/quick_test.py    # Component import validation
curl http://localhost:8000/health  # Real-time health status

# Performance testing
python tests/comprehensive_test.py  # End-to-end performance
```

### Model Management
```bash
ollama list                     # List installed models
ollama pull llama3.2:8b        # Pull specific model
make pull-model MODEL=phi3:mini # Alternative pull command
```

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Kill existing processes
pkill -f "reflex"
pkill -f "uvicorn"

# Check what's using ports
lsof -i :3000   # Reflex Frontend (React UI)
lsof -i :8000   # RAG Backend (FastAPI)
lsof -i :8001   # Reflex Backend (State management)
lsof -i :8002   # ChromaDB (Vector database)
lsof -i :11434  # Ollama (LLM server)
```

### Backend Issues
```bash
# Check containers are running
podman ps  # or docker ps

# Clean restart
make clean && make start

# For container networking issues
./scripts/fix-podman-networking.sh  # Auto-configure for your platform

# View detailed logs
make logs

# Check individual services
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### Reflex UI Issues
```bash
# Install/update dependencies
pip install -r requirements.reflex.txt

# Test component imports
python scripts/quick_test.py

# Clear Reflex cache
rm -rf app/reflex_app/.web/

# Manual start (for debugging)
cd app/reflex_app
export PYTHONPATH="/absolute/path/to/app/reflex_app"
reflex run
```

**"RuntimeError: There should not be an `__init__.py` file in your app root directory"**
- ✅ **RESOLVED**: Removed `__init__.py` file from `app/reflex_app/` directory
- Reflex requires app root to have no `__init__.py` file
- No action needed - fix already applied

### Ollama Issues
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Test connectivity
curl http://localhost:11434/api/tags

# List/pull models
ollama list
ollama pull llama3.2:3b
```

## 🧪 Testing Your Changes

### 1. Component Testing
```bash
python scripts/quick_test.py
```
Should show all 3 tests passing:
- ✅ Reflex Component Imports
- ✅ Component Creation  
- ✅ API Client

### 2. Backend API Testing
```bash
# Check system health
curl http://localhost:8000/health

# Get API information
curl http://localhost:8000/info

# Test query endpoint
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What documents do you have?", "max_chunks": 3}'
```

### 3. UI Testing
1. Visit http://localhost:3000
2. Verify chat interface loads without errors
3. Check sidebar navigation and system status
4. Try sending a test message
5. Verify error handling (try with backend stopped)

### 4. Development Workflow
```bash
# Make code changes to components in app/reflex_app/rag_reflex_app/
# Reflex auto-reloads during development

# For backend changes in app/main.py or app/rag_backend.py:
make restart  # Rebuild and restart containers
```

## 📁 Project Structure

```
rag-example/
├── app/
│   ├── main.py                 # FastAPI v1 backend with complete API
│   ├── rag_backend.py          # Enhanced RAG processing engine
│   ├── document_manager.py     # Complete document lifecycle management
│   ├── pdf_processor.py        # Multi-format PDF processing pipeline  
│   ├── document_intelligence.py # Smart document analysis & optimization
│   ├── upload_handler.py       # Robust multi-file upload processing
│   ├── error_handlers.py       # Comprehensive error management
│   ├── health_monitor.py       # Production health monitoring & diagnostics
│   ├── mcp_server.py          # Model Context Protocol interface
│   └── reflex_app/            # Complete Reflex UI application
│       ├── rag_reflex_app/    # Main app with document management
│       │   ├── components/    # Full UI component library
│       │   ├── state/         # Advanced state management  
│       │   ├── pages/         # Chat + Documents + Dashboard pages
│       │   └── services/      # API integration services
│       └── rxconfig.py        # Production Reflex configuration
├── docs/                      # Complete technical documentation
├── planning/                  # Project roadmaps & development plans
├── scripts/                   # Comprehensive testing & utility scripts
├── tests/                     # Full test suite (unit, integration, e2e)
├── docker-compose.*.yml       # Production deployment configurations
├── Makefile                   # Complete build & deployment automation
└── requirements*.txt          # Comprehensive dependency management
```

## 📚 Next Steps

1. **Upload Documents**: Navigate to Documents page, drag-and-drop files, monitor processing
2. **Document Management**: Organize, search, filter, and manage your document library
3. **Intelligent Chat**: Ask questions about your documents with source attribution
4. **Monitor Performance**: Use Grafana dashboard for system health and performance
5. **Extend & Customize**: Modify components and add new features
6. **Production Deploy**: Use monitoring stack for enterprise deployment

## 🚀 Production Features Available

**Document Management:**
- ✅ Drag-and-drop document upload with progress tracking
- ✅ Multi-format PDF processing with intelligent text extraction
- ✅ Document dashboard with search, filter, and bulk operations
- ✅ Real-time processing status and error recovery

**Intelligence & Chat:**
- ✅ Advanced RAG with source attribution and confidence scoring
- ✅ Multi-document queries with intelligent context building
- ✅ Real-time chat with typing indicators and auto-scroll

**Production Infrastructure:**
- ✅ Complete monitoring stack (Prometheus + Grafana)
- ✅ Health checks, error tracking, and automated recovery
- ✅ Performance metrics and resource usage monitoring
- ✅ Enterprise security and deployment configurations
- ✅ Comprehensive testing suite and CI/CD readiness

## 💡 Development Tips

- **Use `make start-ui`** for faster development (auto-reload)
- **Check `make logs`** for backend errors
- **Use browser dev tools** for frontend debugging
- **Run `make health`** to verify all services
- **Test changes with `python scripts/quick_test.py`**

---

**Questions?** Run `make help` for all available commands or check the troubleshooting section above.

The system runs completely locally - your data never leaves your machine! 🔒