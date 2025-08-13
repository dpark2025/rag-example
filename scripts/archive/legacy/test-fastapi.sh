#!/bin/bash

echo "🧪 Testing FastAPI server directly..."

echo "1. Checking if container is running:"
podman ps | grep local-rag-app || echo "Container not running"

echo ""
echo "2. Trying to start FastAPI manually in container:"
podman exec local-rag-app python -c "
import sys
print('Python version:', sys.version)
try:
    print('Testing imports...')
    from fastapi import FastAPI
    print('✅ FastAPI import OK')
    
    from rag_backend import get_rag_system
    print('✅ RAG backend import OK')
    
    print('Testing RAG system initialization...')
    rag_sys = get_rag_system()
    print('✅ RAG system initialization OK')
    
    print('Testing LLM client...')
    print('LLM URL:', rag_sys.llm_client.base_url)
    
except Exception as e:
    print('❌ Error:', e)
    import traceback
    traceback.print_exc()
"

echo ""
echo "3. Trying to run FastAPI server manually:"
echo "Starting server in background..."
podman exec -d local-rag-app python main.py

echo "Waiting 5 seconds..."
sleep 5

echo "Testing connection:"
podman exec local-rag-app curl -s http://localhost:8000/health || echo "Connection failed"

echo ""
echo "4. Current processes in container:"
podman exec local-rag-app ps aux