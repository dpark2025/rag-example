# Installation Guide

This guide provides step-by-step instructions for setting up the RAG system dependencies.

## Quick Installation

```bash
# Install all dependencies at once
pip install -r requirements.txt

# Or install Reflex dependencies directly
pip install -r requirements.reflex.txt
```

## Step-by-Step Installation

### 1. Core Dependencies
```bash
# Web framework and API
pip install reflex>=0.8.4 fastapi>=0.115.0 uvicorn[standard]>=0.24.0

# Data processing
pip install pydantic>=2.0.0 python-multipart>=0.0.6
```

### 2. RAG System Dependencies
```bash
# Vector database and embeddings
pip install sentence-transformers>=2.2.2 chromadb>=0.4.0

# HTTP clients
pip install requests>=2.31.0 httpx>=0.25.0
```

### 3. PDF Processing (Required for Tests)
```bash
# PDF processing libraries
pip install PyPDF2>=3.0.1 PyMuPDF>=1.23.14 pdfplumber>=0.10.3
```

### 4. Testing Dependencies
```bash
# Essential testing only (recommended)
pip install -r requirements-test-essential.txt

# Or comprehensive testing (includes frontend testing, linting, etc.)
pip install -r requirements-test.txt

# Or minimal core testing
pip install pytest>=7.4.0 pytest-asyncio>=0.21.0 pytest-html>=4.0.0
```

### 5. Optional Dependencies
```bash
# System monitoring
pip install psutil>=5.9.0 python-dotenv>=1.0.0

# Export features
pip install reportlab>=4.0.0 markdown>=3.5.0 beautifulsoup4>=4.12.0

# Multilingual support
pip install langdetect>=1.0.9 babel>=2.13.0 regex>=2023.10.0
```

## Requirements Files

- **`requirements.txt`**: Main production requirements (includes all dependencies)
- **`requirements.reflex.txt`**: Comprehensive Reflex app requirements
- **`../app/requirements.txt`**: Backend-specific dependencies
- **`requirements-test.txt`**: Extended testing and development tools (comprehensive)
- **`requirements-test-essential.txt`**: Essential testing dependencies only (recommended)

## Common Issues

### Missing `fitz` Module
```bash
# PyMuPDF provides the 'fitz' module for PDF processing
pip install PyMuPDF>=1.23.14
```

### ChromaDB Installation Issues
```bash
# On macOS with M1/M2 chips
pip install chromadb --no-binary chromadb

# Or use conda
conda install -c conda-forge chromadb
```

### Sentence Transformers GPU Support
```bash
# For CUDA support (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Verification

After installation, verify everything works:

```bash
# Run essential tests
python scripts/run_essential_tests.py

# Or run pytest directly
pytest tests/unit/test_essential_functionality.py -v
```

## Docker Installation (Alternative)

If you prefer Docker:

```bash
# Build and run with all dependencies
docker-compose -f docker-compose.production.yml up -d
```

## System Requirements

- Python 3.9 or higher
- 4GB+ RAM (8GB+ recommended for embedding models)
- Ollama installed and running (for LLM functionality)
- 2GB+ disk space for models and dependencies