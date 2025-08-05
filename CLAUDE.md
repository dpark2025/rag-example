# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fully local RAG (Retrieval-Augmented Generation) system** with a modern Reflex web interface. The system runs completely offline, combining document retrieval with local LLM generation to create an intelligent question-answering system that processes user documents without external API calls.

**✅ Current Status**: Feature-complete RAG system with all phases implemented. Full document lifecycle management, PDF processing, production monitoring stack, and comprehensive error handling. The system is production-ready with enterprise-grade features including monitoring, security, and automated deployments.

## Architecture

The system uses a **modern 3-tier architecture**:

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
- **Reflex UI** (`app/reflex_app/`): Complete document management + chat interface
- **FastAPI Backend** (`main.py`): Full v1 API with document lifecycle endpoints
- **RAG Engine** (`rag_backend.py`): Advanced processing with intelligent chunking
- **Document Manager** (`document_manager.py`): Complete CRUD operations
- **PDF Processor** (`pdf_processor.py`): Multi-format document extraction
- **Document Intelligence** (`document_intelligence.py`): Smart document analysis
- **Upload Handler** (`upload_handler.py`): Robust file upload processing
- **Error Handlers** (`error_handlers.py`): Comprehensive error management
- **Health Monitor** (`health_monitor.py`): System health and diagnostics
- **MCP Server** (`mcp_server.py`): Model Context Protocol interface
- **Monitoring Stack**: Prometheus, Grafana, AlertManager
- **Ollama**: Local LLM server (auto-detected by containers)
- **ChromaDB**: Production vector database with persistence

## Development Commands

### Quick Start (Production)
```bash
# Production deployment with monitoring
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d

# Access interfaces
# - Main UI: http://localhost:3000
# - API Docs: http://localhost:8000/docs
# - Monitoring: http://localhost:3001 (Grafana)
# - Metrics: http://localhost:9090 (Prometheus)
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.reflex.txt
pip install -r app/requirements.txt

# Start services with monitoring
make setup-monitoring
make run-development

# Or start services individually
cd app && python main.py  # Backend
cd app/reflex_app && reflex run  # Frontend
```

### Development Workflow
```bash
# Run comprehensive tests
pytest tests/  # Full test suite
python -m pytest tests/unit/test_document_management.py  # Document tests
python -m pytest tests/unit/test_pdf_processing.py  # PDF tests

# Development testing
python tests/comprehensive_test.py  # End-to-end tests
python scripts/test_processing_status.py  # Processing workflow
python scripts/run_comprehensive_tests.py  # Full test suite

# Access all interfaces
# - Main UI: http://localhost:3000
# - API v1 Docs: http://localhost:8000/docs
# - Health Status: http://localhost:8000/health
# - Metrics: http://localhost:9090
# - Monitoring: http://localhost:3001
# - Ollama API: http://localhost:11434
```

## Key Architecture Patterns

### RAG Efficiency Optimizations
The system implements several performance optimizations:

1. **Smart Chunking**: Documents are split by semantic boundaries (paragraphs/sentences) rather than arbitrary token counts, with 400-token chunks and 50-token overlap
2. **Adaptive Retrieval**: Only retrieves chunks above 0.7 similarity threshold, stops at context limit
3. **Hierarchical Context**: Most relevant chunk shown in full, others as bullet points
4. **Query-Adaptive Selection**: Simple queries use 2 chunks, complex comparisons use 5 chunks
5. **Token Management**: Real-time token counting with configurable limits

### Document Processing Pipeline
```
📄 Upload → 🔍 Type Detection → 📝 Content Extraction → 🧠 Intelligence Analysis → 
🔪 Smart Chunking → 🧠 Embeddings → 💾 ChromaDB → 📊 Status Tracking → ✅ Ready for Queries
```

### Document Management Pipeline
```
📁 Document Dashboard → 📊 Status View → 🔄 Bulk Operations → 🗑️ Safe Deletion → 
📈 Processing Metrics → 🔍 Search & Filter → 📋 Metadata Display
```

### Query Processing Pipeline  
```
❓ Query → 🧠 Query Embedding → 🔍 Vector Search → 📋 Context Building → 🤖 LLM Generation → 💬 Answer
```

## Agent Specializations

The `/agents/` directory contains specialized agent configurations:
- **ai-ml-engineer-agent.md**: AI/ML systems, semantic search, embeddings
- **backend-lead-agent.md**: API design, system architecture  
- **devops-engineer-agent.md**: Container orchestration, deployment
- **performance-engineer-agent.md**: System optimization, benchmarking
- **security-engineer-agent.md**: Security hardening, vulnerability assessment

## Document Structure

- **Documentation**: All technical docs in `/docs/`
  - `reflex_migration_progress.md`: Migration phases and progress
  - `guided_test.md`: Runtime testing guide
  - `rag_system_architecture.md`: Complete system implementation guide
- **Planning**: Project planning artifacts in `/planning/`
- **Agents**: Agent role definitions in `/agents/`

## Technology Stack Rationale

**Reflex**: Modern Python web framework with real-time reactivity and type safety
**FastAPI**: Automatic API documentation, type validation, async support, and modern Python features
**ChromaDB**: Local vector database with simple API, built-in metadata support, and persistence
**Ollama**: Local LLM server with simple API and model management (runs on host, auto-detected by containers)
**SentenceTransformers**: Local embedding generation using `all-MiniLM-L6-v2` model (384 dimensions, 80MB)

## Resource Requirements

| Component | Minimum RAM | Recommended RAM |
|-----------|-------------|-----------------|
| Reflex UI | 512MB | 1GB |
| RAG Backend | 2GB | 4GB |
| Ollama + 3B Model | 4GB | 8GB |
| Ollama + 8B Model | 8GB | 16GB |
| **Total System** | **6GB** | **20GB** |

## Interface Access Points

- **Reflex UI**: http://localhost:3000 (primary interface)
- **FastAPI Docs**: http://localhost:8000/docs (API documentation)  
- **System Health**: http://localhost:8000/health (health monitoring)
- **Grafana Dashboard**: http://localhost:3001 (production monitoring)
- **Prometheus Metrics**: http://localhost:9090 (metrics collection)
- **Ollama API**: http://localhost:11434 (LLM server)

## Port Architecture

The system uses a multi-port architecture for service separation and scalability:

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    HTTP Calls    ┌─────────────────┐
│  Frontend UI    │◄──────────────►│ Reflex Backend  │◄───────────────►│   RAG Backend   │
│  Port 3000      │                │  Port 8001      │                 │   Port 8000     │
│  (React)        │                │  (State Mgmt)   │                 │  (RAG Engine)   │
└─────────────────┘                └─────────────────┘                 └─────────────────┘
         │                                   │                                   │
         │                                   │                                   ▼
         │                                   │                         ┌─────────────────┐
         │                                   │                         │   ChromaDB      │
         │                                   │                         │   Port 8002     │
         │                                   │                         │   (Vector DB)   │
         │                                   │                         └─────────────────┘
         │                                   │
         └───────────────────────────────────┼─────────────────────────────────────────────┐
                                             │                                             │
                                             ▼                                             ▼
                                   ┌─────────────────┐                           ┌─────────────────┐
                                   │   Local LLM     │                           │   All Services  │
                                   │   Port 11434    │                           │   Auto-detected │
                                   │   (Ollama)      │                           │   by containers │
                                   └─────────────────┘                           └─────────────────┘
```

### Port Assignments

| Port | Service | Purpose | Technology |
|------|---------|---------|------------|
| **3000** | Reflex Frontend | User interface (React) | React/JavaScript |
| **8001** | Reflex Backend | State management, WebSocket | Python/FastAPI |
| **8000** | RAG Backend | Document processing, LLM queries | FastAPI/Python |
| **8002** | ChromaDB | Vector database storage | ChromaDB |
| **11434** | Ollama | Local LLM inference | Ollama/Go |

### Communication Flow

1. **User Interaction**: Browser → Port 3000 (React UI)
2. **State Updates**: Port 3000 ↔ Port 8001 (WebSocket)
3. **RAG Queries**: Port 8001 → Port 8000 (HTTP/REST)
4. **Vector Search**: Port 8000 → Port 8002 (HTTP)
5. **LLM Generation**: Port 8000 → Port 11434 (HTTP)

### Why This Architecture?

- **Separation of Concerns**: UI logic vs. business logic vs. data storage
- **Real-time Updates**: WebSocket for instant UI feedback
- **Scalability**: Independent scaling of each service
- **Development**: Can develop/test each service separately
- **Framework Design**: Follows Reflex's dual-backend pattern

## Important Implementation Details

### Document Upload Methods
1. **Reflex UI**: Drag-and-drop upload, bulk processing, progress tracking
2. **REST API v1**: Complete `/api/v1/documents/*` endpoints with status tracking
3. **MCP Protocol**: Tool-based integration for agent systems
4. **Bulk Upload**: Multi-file processing with parallel execution
5. **PDF Processing**: Multi-format PDF support with text and metadata extraction

### Enhanced RAG Query Process
The system uses an intelligent multi-phase approach:
1. **Query Analysis**: Analyze query intent and complexity
2. **Document Intelligence**: Apply document-type-specific retrieval strategies
3. **Retrieval Phase**: Multi-stage vector search with adaptive filtering
4. **Context Building**: Hierarchical context assembly with source attribution
5. **Generation Phase**: LLM synthesis with error handling and fallbacks
6. **Response Enhancement**: Source linking, confidence scoring, and metrics tracking

### Production-Ready Local-First Design
- **Complete Offline Operation**: All components run locally after setup
- **Zero External Dependencies**: No API calls to external services
- **Data Privacy**: All data stays on your infrastructure
- **Persistent Storage**: Full data persistence with backup strategies
- **Smart Connectivity**: Auto-detection of Ollama and service discovery
- **High Availability**: Multi-replica deployments with health monitoring
- **Monitoring & Alerting**: Complete observability stack
- **Error Recovery**: Comprehensive error handling and recovery mechanisms
- **Performance Optimization**: Caching, connection pooling, and resource management
- **Security Hardening**: Container security, secrets management, SSL/TLS

## Development Guidelines

- Follow existing patterns in `rag_backend.py` for RAG functionality
- Use Pydantic models for API validation in FastAPI endpoints
- Implement proper error handling and logging throughout
- Add comprehensive tests for new features
- Monitor token usage and efficiency metrics
- Use relative paths in code and configurations
- Follow the project's emphasis on local-first, privacy-preserving design
- Remember that code changes require rebuilds when using containers
- Use diagnostic scripts in `/scripts/` directory for troubleshooting

## Current Development Status

- ✅ **Phase 1**: Foundation Setup - Complete
- ✅ **Phase 2**: Chat Interface - Complete
- ✅ **Phase 3**: Document Management - Complete (upload, dashboard, operations)
- ✅ **Phase 4**: PDF Processing & Intelligence - Complete
- ✅ **Phase 5**: Production Readiness & UX Polish - Complete
- ✅ **Production Infrastructure**: Complete (monitoring, CI/CD, security)
- 🚀 **Status**: **PRODUCTION READY** - Feature-complete system ready for deployment

**Latest Capabilities Added:**
- Complete document lifecycle management with drag-and-drop upload
- Multi-format PDF processing with intelligent text extraction
- Real-time processing status tracking and error recovery
- Production monitoring stack with Prometheus + Grafana
- Comprehensive error handling and health monitoring
- Bulk document operations and advanced search/filtering
- Enterprise-grade security and deployment configurations
- Automated backup and recovery procedures

The system is now a fully-featured, production-ready RAG platform suitable for enterprise deployment with comprehensive document management, monitoring, and operational capabilities.