# Local RAG System 🚀

A fully local RAG (Retrieval-Augmented Generation) system with a clean, stable Reflex UI. All processing runs offline with no external API calls.

## ✨ Features

- **Chat Interface** - Ask questions about your documents
- **Document Upload** - Drag-and-drop file uploads with processing
- **System Monitoring** - Health status for all services
- **Mobile Responsive** - Works on desktop and mobile devices
- **100% Local** - No data leaves your machine

## 🚀 Quick Start

### Prerequisites
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# 2. Pull a model
ollama pull llama3.2:3b

# 3. Install Python dependencies
pip install -r requirements.txt
pip install -r requirements.reflex.txt
```

### Start the System
```bash
# 1. Start backend services
make start

# 2. Start UI (in new terminal)
make start-ui

# 3. Open browser
# → http://localhost:3000
```

### Verify Everything Works
```bash
make health  # Should show all services healthy
```

## 🏗️ Architecture

**Clean & Simple:**
```
app/reflex_app/rag_reflex_app/
├── pages/index_minimal.py           # Single UI page (all features)
├── rag_reflex_app_minimal.py        # Main app
└── rxconfig.py                      # Config
```

**Backend Services:**
- **FastAPI** (port 8000) - Document processing API
- **ChromaDB** (port 8002) - Vector database  
- **Ollama** (port 11434) - Local LLM
- **Reflex UI** (port 3000) - Web interface

## 🛠️ Development

### Make Commands
```bash
make help          # Show all available commands
make build         # Build containers
make start         # Start backend services  
make start-ui      # Start UI
make health        # Check service status
make logs          # View service logs
make restart       # Clean restart
make clean         # Stop and remove containers
```

### Adding Features
1. Edit `app/reflex_app/rag_reflex_app/pages/index_minimal.py`
2. Add state variables to `MinimalChatState` class
3. Test with `make start-ui`

## 📋 Documentation

- **[🔧 Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[📋 Command Validation Plan](COMMAND_VALIDATION_PLAN.md)** - Testing procedures
- **[🚀 Enhanced RAG Implementation](ENHANCED_RAG_IMPLEMENTATION.md)** - Architecture details

## 🎯 Recent Cleanup

This repository was recently cleaned up to provide a single, stable UI version:
- ✅ Removed complex component architecture for simplicity
- ✅ Fixed React DOM lifecycle issues  
- ✅ Single source of truth: `index_minimal.py`
- ✅ All features working and browser-tested
- ✅ Clean, maintainable codebase

---

**That's it!** 🎉 A working local RAG system in 3 commands.