# Local RAG System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Unified Container Deployment](#unified-container-deployment)
5. [API Reference](#api-reference)
6. [Development Guide](#development-guide)
7. [Session Management & Features](#session-management--features)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Migration Guide](#migration-guide)

---

## System Overview

The Local RAG System is a fully offline Retrieval-Augmented Generation system that processes documents and answers questions using local LLMs. All processing happens on your machine with no external API calls.

### Key Features
- **Chat Interface** - Interactive chat with conversation history support
- **Document Upload** - Drag-and-drop file uploads with real-time processing status
- **Session Management** - Session-based document tracking and context awareness
- **System Monitoring** - Health checks and readiness endpoints for production deployments
- **Unified Container** - Single container deployment with orchestrated startup
- **100% Local** - Complete privacy with no data leaving your machine

### Recent Updates
- ✅ **Unified Container Architecture** - Single container replacing 3-container setup
- ✅ **Sequential Startup Orchestration** - Health checks ensure proper service initialization
- ✅ **Session-Based Document Tracking** - UI tracks documents per session
- ✅ **Conversation History Support** - Context maintained across queries
- ✅ **Application Readiness Endpoint** - `/ready` for load balancer integration

---

## Architecture

### Unified Container Architecture

The system now uses a single container with orchestrated startup sequencing:

```
Unified Container (Supervisord Management)
│
├── ChromaDB (Priority 10)
│   ├── Starts first
│   ├── Port: 8002
│   └── Health: /api/v1/heartbeat
│
├── RAG Backend (Priority 20)
│   ├── Starts after ChromaDB is healthy
│   ├── Port: 8000
│   ├── Health: /health
│   └── Ready: /ready
│
└── Reflex Frontend (Priority 30)
    ├── Starts after RAG Backend is healthy
    ├── Port: 3000
    └── Health: /_health
```

### Startup Orchestration Flow

1. **Container Start** → Executes `/app/scripts/orchestrate-startup.sh`
2. **Supervisord Launch** → Process management in background
3. **ChromaDB Initialization** → Vector database starts (30s timeout)
4. **RAG Backend Startup** → API service starts after ChromaDB ready (45s timeout)
5. **Reflex Frontend Launch** → UI starts after backend ready (60s timeout)
6. **Application Ready** → `/ready` endpoint returns success

### Service Components

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| ChromaDB | 8002 | Vector database for embeddings | `/api/v1/heartbeat` |
| RAG Backend | 8000 | FastAPI document processing | `/health`, `/ready` |
| Reflex Frontend | 3000 | React-based UI | `/_health` |
| Ollama | 11434 | Local LLM (runs separately) | `/api/tags` |

### Code Structure

```
/Users/dpark/projects/github.com/working/rag-example/
├── app/                           # Application code
│   ├── main.py                     # FastAPI with /ready endpoint
│   ├── rag_backend.py             # RAG with conversation history
│   └── reflex_app/                # Reflex frontend application
│       └── rag_reflex_app/
│           └── pages/
│               └── index_minimal.py # UI with session tracking
├── docs/                          # Documentation
│   ├── MASTER_DOCUMENTATION.md    # Complete system documentation  
│   └── startup-orchestration.md   # Container orchestration design
├── tests/                         # Test suite (8,500+ lines)
│   ├── README.md                  # Testing documentation
│   ├── conftest.py               # Test configuration
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── e2e/                      # End-to-end tests
│   ├── performance/              # Performance tests
│   ├── accessibility/            # WCAG compliance tests
│   ├── security/                 # Security tests
│   └── stress/                   # Stress tests
├── scripts/                       # Utility scripts
│   ├── build-unified.sh          # Container build script
│   ├── run-unified.sh           # Container run script
│   └── run_clean_tests.sh       # Test runner
├── data/                          # Runtime data (gitignored)
│   ├── chroma_db/                # ChromaDB vector store
│   └── documents/                # Uploaded documents
├── screenshots/                   # Test screenshots (gitignored)
├── .benchmarks/                   # Performance benchmarks (gitignored)
├── Dockerfile.unified             # Single container definition
├── supervisord.conf              # Process management configuration
├── build.sh                      # Convenience build script
├── run.sh                        # Convenience run script
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
└── README.md                     # Quick start guide
```

**Directory Purposes:**

- **Essential Directories** (version controlled):
  - `app/`: Core application code (FastAPI backend, Reflex frontend)
  - `docs/`: Comprehensive system documentation
  - `tests/`: Complete test suite with 90%+ coverage target
  - `scripts/`: Build, deployment, and utility scripts

- **Runtime Directories** (gitignored):
  - `data/`: Application runtime data (ChromaDB, uploaded documents)
  - `screenshots/`: Playwright test screenshots and visual artifacts
  - `.benchmarks/`: Performance testing results and metrics

---

## Installation & Setup

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB+ for models and data
- **OS**: Linux, macOS, or Windows with WSL2

### Prerequisites

1. **Install Ollama**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.2:3b  # Or your preferred model
```

2. **Install Container Runtime** (choose one):
```bash
# Podman (recommended for rootless)
brew install podman  # macOS
sudo apt install podman  # Ubuntu/Debian
sudo dnf install podman  # Fedora

# Or Docker
# Install Docker Desktop from docker.com
```

3. **Python Dependencies** (for local development):
```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (includes testing tools)
pip install -r requirements-dev.txt
```

### Quick Start Options

#### Option 1: Container Deployment (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd rag-example

# Quick start with container
make setup

# Or step by step
make container-build
make container-run

# Access application → http://localhost:3000
```

#### Option 2: Host Deployment (Development)
```bash
# Clone repository
git clone <repository-url>
cd rag-example

# Setup host environment
make host-setup

# Start backend services
make host-start

# Start UI (new terminal)
make host-ui

# Access application → http://localhost:3000
```

### Manual Container Run

```bash
# Using Podman
podman run -d --name local-rag-unified \
  -p 3000:3000 -p 8000:8000 -p 8002:8002 \
  -v ./data:/app/data:Z \
  -e OLLAMA_HOST=host.containers.internal:11434 \
  local-rag-unified:latest

# Using Docker
docker run -d --name local-rag-unified \
  -p 3000:3000 -p 8000:8000 -p 8002:8002 \
  -v ./data:/app/data \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  local-rag-unified:latest
```

### Deployment Method Comparison

| Feature | Container Deployment | Host Deployment |
|---------|---------------------|-----------------|
| **Setup Complexity** | Simple (`make setup`) | Moderate (dependencies) |
| **Resource Usage** | Higher (container overhead) | Lower (native processes) |
| **Isolation** | Complete service isolation | Shared host environment |
| **Development** | Rebuild required for changes | Live reload available |
| **Production Ready** | Yes (orchestrated startup) | Requires external coordination |
| **Debugging** | Container logs | Direct process access |
| **Best For** | Production, demos, testing | Active development |

### Traditional Setup (Development)

```bash
# Install Python dependencies
pip install -r requirements.txt

# For development/testing
pip install -r requirements-dev.txt

# Start backend services
make start

# Start UI (new terminal)
make start-ui

# Access application
# → http://localhost:3000
```

---

## Unified Container Deployment

### Build Script Details

The `build-unified.sh` script:
- Detects Podman or Docker automatically
- Cleans up existing containers
- Builds the unified image
- Provides run instructions

### Run Script Features

The `run-unified.sh` script:
- Stops any existing containers
- Starts the unified container
- Waits for readiness (up to 90 seconds)
- Shows service status
- Provides access URLs

### Dockerfile.unified Structure

```dockerfile
# Key components
FROM python:3.11-slim

# System dependencies
RUN apt-get install supervisor curl nodejs

# Python packages
RUN pip install chromadb reflex fastapi uvicorn

# Startup scripts
COPY supervisord.conf /etc/supervisor/conf.d/
COPY scripts/* /app/scripts/

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8000/ready || exit 1

CMD ["/app/scripts/orchestrate-startup.sh"]
```

### Supervisord Configuration

```ini
[program:chromadb]
priority=10
autostart=false
command=/app/scripts/start-chromadb.sh

[program:rag-backend]
priority=20
autostart=false
command=/app/scripts/start-rag-backend.sh

[program:reflex-frontend]
priority=30
autostart=false
command=/app/scripts/start-reflex-frontend.sh
```

---

## API Reference

### Base URLs
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:3000

### Health & Readiness Endpoints

#### GET /health
Comprehensive system health check.

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "chromadb": true,
    "rag_system": true,
    "ollama": true
  },
  "document_count": 42,
  "monitoring": {
    "enabled": true,
    "check_interval": 30
  }
}
```

#### GET /ready
Application readiness check for load balancers.

**Response**:
```json
{
  "ready": true,
  "services": {
    "chromadb": "ready",
    "rag_backend": "ready",
    "reflex_frontend": "ready"
  },
  "message": "Application ready"
}
```

### Query Endpoints

#### POST /query
Query the knowledge base with conversation history.

**Request**:
```json
{
  "question": "What documents are available?",
  "max_chunks": 3,
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "session_upload_count": 2
}
```

**Response**:
```json
{
  "answer": "Based on the documents...",
  "sources": [
    {"title": "doc.pdf", "score": "0.85", "content": "..."}
  ],
  "context_used": 3,
  "context_tokens": 1250,
  "efficiency_ratio": 0.75
}
```

### Document Management

#### GET /documents
List all documents with filtering.

**Query Parameters**:
- `file_type`: Filter by type (txt, pdf)
- `status`: Filter by status (ready, processing)
- `limit`: Results limit (1-100)
- `offset`: Pagination offset

#### POST /documents/upload
Upload files for processing.

**Request**: `multipart/form-data`
- `files`: One or more files

**Response**:
```json
{
  "message": "Successfully uploaded 2 files",
  "files_processed": 2,
  "processing_tasks": ["task_1", "task_2"]
}
```

#### DELETE /documents/{doc_id}
Delete a specific document.

#### GET /documents/stats
Get storage statistics.

### System Configuration

#### GET /settings
Get current RAG settings.

#### POST /settings
Update RAG settings.

```json
{
  "similarity_threshold": 0.75,
  "max_context_tokens": 3000,
  "chunk_size": 600,
  "chunk_overlap": 75
}
```

---

## Development Guide

### Project Structure
```
app/
├── main.py                         # FastAPI application
├── rag_backend.py                 # RAG logic with conversation history
├── document_processing_tracker.py # Upload status tracking
├── reflex_app/
│   └── rag_reflex_app/
│       └── pages/
│           └── index_minimal.py  # React UI with session management
└── [other modules]
```

### Key Files to Modify

1. **Frontend Changes**: `app/reflex_app/rag_reflex_app/pages/index_minimal.py`
   - State management in `MinimalChatState` class
   - UI components and layout
   - Session tracking logic

2. **Backend Changes**: `app/main.py`
   - API endpoints
   - Request/response models
   - Health checks

3. **RAG Logic**: `app/rag_backend.py`
   - Query processing
   - Conversation history handling
   - Token management

### Adding New Features

1. **Update State** (Frontend):
```python
class MinimalChatState(rx.State):
    # Add new state variable
    new_feature: bool = False
    
    def toggle_feature(self):
        self.new_feature = not self.new_feature
```

2. **Add API Endpoint** (Backend):
```python
@app.post("/api/new-feature")
async def new_feature(request: FeatureRequest):
    # Implementation
    return {"status": "success"}
```

3. **Rebuild Container**:
```bash
./build-unified.sh
./run-unified.sh
```

### Testing

```bash
# Run health check
curl http://localhost:8000/health

# Test readiness
curl http://localhost:8000/ready

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Test query"}'

# View logs
podman logs local-rag-unified
```

---

## Session Management & Features

### Session-Based Document Tracking

The UI maintains session state for uploaded documents:

```python
# Frontend state management
class MinimalChatState(rx.State):
    session_uploads: list[dict] = []  # Files uploaded this session
    
    async def handle_upload(self, files):
        # Process upload
        self.session_uploads.append({
            "title": file.name,
            "timestamp": datetime.now()
        })
```

### Conversation History Integration

Each query includes conversation context:

```python
# Automatically included in queries
conversation_history = [
    {"role": "user", "content": message1},
    {"role": "assistant", "content": response1},
    # ... previous messages
]

# Token management
def _truncate_conversation_history(history, max_tokens=1000):
    # Keep most recent messages within token limit
```

### Session Context in LLM Prompts

The system provides session awareness to the LLM:

```python
# Session info added to prompts
session_info = f"Session Info: {session_upload_count} documents uploaded"

# LLM responds appropriately
if session_upload_count == 0:
    return "No documents have been uploaded in this session"
```

---

## Production Deployment

### Environment Configuration

Create `.env` file:
```bash
# Ollama Configuration
OLLAMA_HOST=your-ollama-server:11434

# API Configuration
API_BASE_URL=http://localhost:8000
REFLEX_HOST=0.0.0.0
REFLEX_PORT=3000

# Performance
MAX_CONTEXT_TOKENS=2048
CHUNK_SIZE=500
CHUNK_OVERLAP=50
WORKERS=4
```

### Resource Limits

```bash
# Run with constraints
podman run -d \
  --name rag-prod \
  --memory=8g \
  --cpus=4 \
  --env-file .env \
  -p 3000:3000 -p 8000:8000 \
  -v /path/to/data:/app/data:Z \
  --restart unless-stopped \
  local-rag-unified:latest
```

### Load Balancer Configuration

**nginx example**:
```nginx
upstream rag_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name rag.example.com;

    location /health-check {
        proxy_pass http://rag_backend/ready;
        proxy_read_timeout 5s;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api/ {
        proxy_pass http://rag_backend/;
    }
}
```

### Monitoring

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rag-system'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 30s
```

### Backup & Recovery

```bash
#!/bin/bash
# backup-rag.sh
BACKUP_DIR="/backups/rag"
DATE=$(date +%Y%m%d_%H%M%S)

# Stop container
podman stop local-rag-unified

# Backup data
tar -czf "$BACKUP_DIR/backup-$DATE.tar.gz" ./data ./chroma_data

# Restart
podman start local-rag-unified

# Keep last 7 backups
find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +7 -delete
```

### Security Considerations

1. **Network Security**:
```bash
# Internal network only
podman run -d \
  --network=internal \
  --name rag-secure \
  local-rag-unified:latest
```

2. **File Permissions**:
```bash
chmod 700 ./data
chown -R 1000:1000 ./data
```

3. **Environment Secrets**:
```bash
podman secret create ollama_host echo "secure-host:11434"
podman run -d --secret ollama_host local-rag-unified:latest
```

---

## Troubleshooting

### Container Won't Start

1. **Check logs**:
```bash
podman logs local-rag-unified
```

2. **Verify ports**:
```bash
lsof -i :3000 -i :8000 -i :8002
```

3. **Check Ollama**:
```bash
curl http://localhost:11434/api/tags
```

### Services Not Ready

1. **Individual health checks**:
```bash
# ChromaDB
curl http://localhost:8002/api/v1/heartbeat

# RAG Backend
curl http://localhost:8000/health

# Reflex Frontend
curl http://localhost:3000/_health
```

2. **Supervisord status**:
```bash
podman exec local-rag-unified supervisorctl status
```

3. **Restart specific service**:
```bash
podman exec local-rag-unified supervisorctl restart rag-backend
```

### Performance Issues

1. **Check resources**:
```bash
podman stats local-rag-unified
```

2. **Adjust settings**:
```bash
-e CHUNK_SIZE=300 -e CHUNK_OVERLAP=30
```

3. **Use smaller model**:
```bash
ollama pull llama3.2:1b
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Service not ready | Wait for `/ready` endpoint |
| Module not found | Container rebuild needed | Run `./build-unified.sh` |
| Out of memory | Large documents | Reduce chunk size or increase memory |
| Slow responses | Large model | Use smaller model (1b vs 3b) |

---

## Migration Guide

### From Multi-Container to Unified

1. **Stop old setup**:
```bash
# If using old multi-container setup, stop all services
podman stop local-rag-reflex local-rag-backend local-rag-chromadb
podman rm local-rag-reflex local-rag-backend local-rag-chromadb
```

2. **Backup data**:
```bash
cp -r ./data ./data-backup
```

3. **Build unified container**:
```bash
./build.sh
```

4. **Run new container**:
```bash
./run.sh
```

5. **Verify**:
```bash
curl http://localhost:8000/ready
```

### Configuration Changes

| Old Setup | New (Unified) |
|-----------|---------------|
| 3 separate containers | Single container |
| Port mapping per service | All ports in one container |
| Service dependencies | Supervisord priorities |
| Individual health checks | Unified /ready endpoint |

### API Compatibility

All existing API endpoints remain compatible. New additions:
- `/ready` - Application readiness
- Session context in `/query`
- Conversation history support

---

## Appendix

### Make Commands Reference

#### Container Commands
```bash
make container-build   # Build unified container
make container-run     # Run unified container
make container-stop    # Stop container
make container-health  # Check container health
make container-logs    # View container logs
make container-clean   # Remove container
```

#### Host Commands
```bash
make host-setup        # Setup host environment
make host-start        # Start backend services on host
make host-ui           # Start Reflex UI on host
make host-stop         # Stop host services
make host-health       # Check host services
make host-logs         # View host logs
make host-clean        # Clean host processes
make host-restart      # Restart host services
```

#### Quick Start Commands (defaults to container)
```bash
make setup          # Complete setup
make start          # Start application
make stop           # Stop application
make health         # Check health
make logs           # View logs
make restart        # Clean restart
make clean          # Clean up
```

#### Utility Commands
```bash
make check-ollama   # Verify Ollama is running
make pull-model MODEL=llama3.2:3b  # Download model
make help           # Show all commands
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_HOST | host.containers.internal:11434 | Ollama server |
| CHUNK_SIZE | 500 | Document chunk size |
| CHUNK_OVERLAP | 50 | Chunk overlap |
| MAX_CONTEXT_TOKENS | 2048 | Max context for LLM |
| REFLEX_PORT | 3000 | Frontend port |
| API_BASE_URL | http://localhost:8000 | Backend URL |

### File Types Supported

- **Text**: `.txt`, `.md`, `.log`
- **PDF**: `.pdf` (with text extraction)
- **Future**: `.docx`, `.html`, `.csv`

### Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Container startup | 60-90s | All services ready |
| Document upload (1MB) | 2-5s | Including chunking |
| Query response | 1-3s | With 3b model |
| Health check | <100ms | All services |

---

*Last Updated: 2024*