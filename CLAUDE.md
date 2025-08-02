# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fully local RAG (Retrieval-Augmented Generation) system** designed to run completely offline using Docker containers. The system combines document retrieval with local LLM generation to create an intelligent question-answering system that processes user documents without external API calls.

## Architecture

The system uses a **3-component containerized architecture**:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent (UI)    │◄──►│   RAG Backend    │◄──►│   ChromaDB      │
│   - Streamlit   │    │   - FastAPI      │    │   - Local Vec DB│
│   - Chat UI     │    │   - Smart chunk  │    │   - Embeddings  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────►│   Local LLM     │
                        │   - Ollama      │
                        │   - Container   │
                        └─────────────────┘
```

**Core Components:**
- **Streamlit UI** (`agent_ui.py`): Web interface for document upload and chat
- **FastAPI Backend** (`main.py`): REST API server with RAG endpoints
- **RAG Engine** (`rag_backend.py`): Core processing with smart chunking and embedding
- **MCP Server** (`mcp_server.py`): Model Context Protocol interface for tools
- **Ollama**: Local LLM server for answer generation
- **ChromaDB**: Local vector database for document storage

## Development Commands

### Quick Start
```bash
# Complete system setup
chmod +x setup.sh && ./setup.sh

# Using Makefile (alternative)
make setup
```

### Container Management
```bash
# Start all services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Health check
make health
```

### Development Workflow
```bash
# Build containers
docker-compose build

# Pull different LLM models
make pull-model MODEL=llama3.2:8b
make pull-model MODEL=mistral:7b

# Access container shells
make shell-rag      # RAG application container
make shell-ollama   # Ollama LLM container
```

### Testing
```bash
# Run system tests
python scripts/test_system.py

# Performance benchmarking
python scripts/benchmark.py

# Check API health
curl http://localhost:8501/_stcore/health  # Streamlit
curl http://localhost:11434/api/tags       # Ollama
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
  - `rag_system_architecture.md`: Complete system implementation guide
  - `Building a 3 part agentic RAG system.md`: Development conversation history
- **Planning**: Project planning artifacts in `/planning/` (when created)
- **Agents**: Agent role definitions in `/agents/`

## Technology Stack Rationale

**FastAPI**: Chosen for automatic API documentation, type validation, async support, and modern Python features over Flask
**Streamlit**: Selected for rapid UI development, Python-native approach, and data-centric components ideal for RAG interfaces
**ChromaDB**: Local vector database with simple API, built-in metadata support, and persistence
**Ollama**: Container-friendly local LLM server with simple API and model management
**SentenceTransformers**: Local embedding generation using `all-MiniLM-L6-v2` model (384 dimensions, 80MB)

## Resource Requirements

| Component | Minimum RAM | Recommended RAM |
|-----------|-------------|-----------------|
| RAG App | 2GB | 4GB |
| Ollama + 3B Model | 4GB | 8GB |
| Ollama + 8B Model | 8GB | 16GB |
| **Total System** | **6GB** | **20GB** |

## Interface Access Points

- **Streamlit UI**: http://localhost:8501 (primary interface)
- **FastAPI Docs**: http://localhost:8000/docs (API documentation)
- **Ollama API**: http://localhost:11434 (LLM server)

## Important Implementation Details

### Document Upload Methods
1. **Streamlit UI**: Manual entry, file upload, bulk processing
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
- Persistent storage survives container restarts

## Development Guidelines

- Follow existing patterns in `rag_backend.py` for RAG functionality
- Use Pydantic models for API validation in FastAPI endpoints
- Implement proper error handling and logging throughout
- Add comprehensive tests for new RAG features
- Monitor token usage and efficiency metrics
- Use absolute paths in Docker configurations
- Follow the project's emphasis on local-first, privacy-preserving design

The system is designed for rapid development and deployment while maintaining production-ready performance and comprehensive RAG capabilities.