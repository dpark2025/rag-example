# Quick Start Guide

Get the Local RAG System running in under 5 minutes.

## 🚀 Prerequisites

1. **Ollama** - Install from https://ollama.ai/download
2. **Python 3.11+** with pip
3. **Podman** or **Docker** for containers
4. **Make** (usually pre-installed on macOS/Linux)

## ⚡ Two-Command Setup

```bash
# 1. Start backend services (containers)
make start

# 2. Start frontend UI (native)
make start-ui
```

That's it! 🎉 System is ready at http://localhost:3000

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

### Step 4: Access the System
- **Main UI**: http://localhost:3000 (Reflex chat interface)
- **API Docs**: http://localhost:8000/docs (Interactive API docs)
- **API Info**: http://localhost:8000/info (Endpoint reference)
- **Health Check**: http://localhost:8000/health (System status)

#### Port Architecture
The system uses multiple ports for different services:

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    HTTP Calls    ┌─────────────────┐
│  Frontend UI    │◄──────────────►│ Reflex Backend  │◄───────────────►│   RAG Backend   │
│  Port 3000      │                │  Port 8001      │                 │   Port 8000     │
│  (React)        │                │  (State Mgmt)   │                 │  (RAG Engine)   │
└─────────────────┘                └─────────────────┘                 └─────────────────┘
```

- **Port 3000**: Reflex Frontend (React UI)
- **Port 8001**: Reflex Backend (State management, WebSocket)
- **Port 8000**: RAG Backend (FastAPI, document processing, LLM queries)
- **Port 8002**: ChromaDB (Vector database)
- **Port 11434**: Ollama (Local LLM server)

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

### Testing & Debugging
```bash
python scripts/quick_test.py    # Test component imports
make help                       # Show all commands
curl http://localhost:8000/info # API endpoint reference
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
podman ps

# Clean restart
make clean && make start

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
│   ├── main.py                 # FastAPI backend
│   ├── rag_backend.py         # RAG processing engine  
│   └── reflex_app/            # Reflex UI application
│       ├── rag_reflex_app/    # Main app module
│       │   ├── components/    # UI components
│       │   ├── state/         # App state management
│       │   └── layouts/       # Page layouts
│       └── rxconfig.py        # Reflex configuration
├── scripts/
│   ├── start_reflex.sh        # UI startup script
│   └── quick_test.py          # Component test suite
├── Makefile                   # Development commands
├── docker-compose.backend.yml # Backend containers
└── requirements.reflex.txt    # Python dependencies
```

## 📚 Next Steps

1. **Add Documents**: Upload documents via the Reflex UI
2. **Chat**: Ask questions about your documents  
3. **Customize**: Modify components in `app/reflex_app/rag_reflex_app/`
4. **Extend**: Add new API endpoints in `app/main.py`
5. **Deploy**: Use container setup for production

## 💡 Development Tips

- **Use `make start-ui`** for faster development (auto-reload)
- **Check `make logs`** for backend errors
- **Use browser dev tools** for frontend debugging
- **Run `make health`** to verify all services
- **Test changes with `python scripts/quick_test.py`**

---

**Questions?** Run `make help` for all available commands or check the troubleshooting section above.

The system runs completely locally - your data never leaves your machine! 🔒