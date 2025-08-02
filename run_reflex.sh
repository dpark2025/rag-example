#!/bin/bash
cd /Users/dpark/projects/github.com/rag-example/app/reflex_app
echo "Starting Reflex UI from: $(pwd)"
echo "Backend services should be running on:"
echo "  - FastAPI Backend: http://localhost:8000"
echo "  - ChromaDB: http://localhost:8002"
echo "  - Ollama: http://localhost:11434"
echo ""
echo "Starting Reflex UI on http://localhost:3000..."
reflex run