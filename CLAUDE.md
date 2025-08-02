# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fully local RAG (Retrieval-Augmented Generation) system** with a modern Reflex web interface. The system runs completely offline, combining document retrieval with local LLM generation to create an intelligent question-answering system that processes user documents without external API calls.

**✅ Current Status**: Reflex UI implementation complete (Phase 2) with chat interface, source attribution, and real-time updates. The system features automatic Ollama connectivity detection and smart host gateway resolution for seamless communication.

## Architecture

The system uses a **modern 3-tier architecture**:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Reflex UI      │◄──►│   RAG Backend    │◄──►│   ChromaDB      │
│  - Chat Interface│    │   - FastAPI      │    │   - Local Vec DB│
│  - Port 3000    │    │   - Smart chunk  │    │   - Embeddings  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────►│   Local LLM     │
                        │   - Ollama      │
                        │   - Local Models │
                        └─────────────────┘
```

**Core Components:**
- **Reflex UI** (`app/reflex_app/`): Modern web interface with real-time chat
- **FastAPI Backend** (`main.py`): REST API server with RAG endpoints
- **RAG Engine** (`rag_backend.py`): Core processing with smart chunking and embedding
- **MCP Server** (`mcp_server.py`): Model Context Protocol interface for tools
- **Ollama**: Local LLM server for answer generation (runs on host)
- **ChromaDB**: Local vector database for document storage

## Development Commands

### Quick Start
```bash
# Install dependencies
pip install -r requirements.reflex.txt
pip install -r app/requirements.txt

# Start RAG Backend
cd app && python main.py

# Start Reflex UI (new terminal)
cd app/reflex_app
reflex init --name rag_reflex_app --template blank
reflex run
```

### Development Workflow
```bash
# Test Reflex components
python scripts/test_reflex_phase2.py

# Quick component test
python scripts/quick_test.py

# Access interfaces
# - Reflex UI: http://localhost:3000
# - FastAPI Docs: http://localhost:8000/docs
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
📄 Upload → 🔪 Smart Chunking → 🧠 Embeddings → 💾 ChromaDB → ✅ Ready for Queries
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
1. **Reflex UI**: Manual entry, file upload, bulk processing (Phase 3)
2. **REST API**: Programmatic uploads via `/documents` endpoints  
3. **MCP Protocol**: Tool-based integration for agent systems

### RAG Query Process
The system uses a two-phase approach:
1. **Retrieval Phase**: Convert query to embedding, search vector DB, filter by relevance
2. **Generation Phase**: Build context from retrieved chunks, send to LLM for synthesis

### Local-First Design
- All components run offline after initial setup
- No external API dependencies 
- Data never leaves the local machine
- Persistent storage survives restarts
- Smart host gateway detection for seamless Ollama connectivity

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
- 🔄 **Phase 3**: Document Management - Next
- ⏳ **Phase 4**: PDF Processing - Planned
- ⏳ **Phase 5**: Enhanced UI - Planned
- ⏳ **Phase 6**: System Integration - Planned

The system is designed for rapid development and deployment while maintaining production-ready performance and comprehensive RAG capabilities.