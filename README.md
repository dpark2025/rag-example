# Local RAG System with Reflex UI 🚀

A **fully local RAG (Retrieval-Augmented Generation) system** with a modern Reflex web interface. This system runs completely offline, combining efficient document retrieval with local LLM generation to create an intelligent question-answering system that processes your documents without external API calls.

**✅ Current Status**: Reflex UI implementation complete with chat interface, source attribution, and real-time updates.

## 🎯 Features

- **🔒 100% Local**: All processing happens on your machine - no external API calls
- **💬 Modern Chat Interface**: Built with Reflex framework for responsive, real-time interactions
- **📚 Smart Document Processing**: Semantic chunking with configurable similarity thresholds
- **🔍 Source Attribution**: See exactly which documents and chunks informed each response
- **⚡ Performance Metrics**: Real-time response time and chunk usage tracking
- **🎨 Enhanced UX**: Auto-scroll, keyboard shortcuts, typing indicators
- **📄 PDF Support** (Phase 4): Coming soon - process PDF documents alongside text files

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Reflex UI      │◄──►│   RAG Backend    │◄──►│   ChromaDB      │
│  - Chat Interface│    │   - FastAPI      │    │   - Vector DB   │
│  - Port 3000    │    │   - Port 8000    │    │   - Embeddings  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────►│   Ollama LLM    │
                        │   - Local Models │
                        │   - Port 11434   │
                        └─────────────────┘
```

## 🚀 Quick Start

### TL;DR - Get Running in 2 Minutes
```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Start backend services  
make setup

# 3. Start Reflex UI (in new terminal)
cd app/reflex_app && reflex run

# 4. Visit http://localhost:3000
```

**👉 For detailed setup instructions, see [QUICK_START.md](QUICK_START.md)**

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

## 📖 Usage

1. **Access the UI**: Open http://localhost:3000 in your browser
2. **Upload Documents**: Use the document management interface (Phase 3 - coming soon)
3. **Ask Questions**: Type your questions in the chat interface
4. **View Sources**: Click on source badges to see which documents informed the response
5. **Adjust Settings**: Modify similarity threshold and max chunks for different results

### Quick Test Without Documents

Even without uploaded documents, you can test the system:
1. Start both backend and UI as described above
2. Ask general questions to test LLM connectivity
3. The system will indicate when no relevant documents are found

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

Run the test suites to verify your setup:
```bash
# Test Reflex components
python scripts/test_reflex_phase2.py

# Quick component test
python scripts/quick_test.py
```

### Docker Deployment (Optional)

For containerized deployment:
```bash
# Using Docker Compose
docker-compose -f docker-compose.reflex.yml up -d

# Using Podman
podman-compose -f docker-compose.reflex.yml up -d
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
| FastAPI Backend | 1GB | 2GB | 100MB |
| Ollama + 3B Model | 4GB | 8GB | 3GB |
| ChromaDB | 512MB | 1GB | Varies |
| **Total System** | **6GB** | **12GB** | **4GB+** |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Roadmap
- [x] Phase 1: Foundation Setup
- [x] Phase 2: Chat Interface
- [ ] Phase 3: Document Management
- [ ] Phase 4: PDF Processing
- [ ] Phase 5: Enhanced UI
- [ ] Phase 6: System Integration

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
lsof -ti:3000 | xargs kill -9  # Reflex
lsof -ti:8000 | xargs kill -9  # FastAPI
```

**Import Errors**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.reflex.txt
```

For more detailed troubleshooting, see [docs/guided_test.md](docs/guided_test.md)