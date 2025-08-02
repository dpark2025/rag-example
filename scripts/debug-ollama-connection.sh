#!/bin/bash

echo "🔍 Debugging Ollama connectivity from container..."

echo "=== Host Ollama Status ==="
echo "1. Ollama status on host:"
curl -s http://localhost:11434/api/tags && echo "✅ Host can reach Ollama" || echo "❌ Host cannot reach Ollama"

echo ""
echo "2. Ollama process on host:"
ps aux | grep ollama | grep -v grep || echo "No ollama processes found"

echo ""
echo "3. Host network ports:"
netstat -tlnp | grep 11434 || echo "Ollama not listening on 11434"

echo ""
echo "=== Container Network Testing ==="
if podman ps | grep -q local-rag-app; then
    echo "4. Container network interface:"
    podman exec local-rag-app ip route | head -5

    echo ""
    echo "5. Testing different Ollama addresses from container:"
    
    echo "  - Testing localhost:11434:"
    podman exec local-rag-app curl -s --connect-timeout 3 http://localhost:11434/api/tags && echo "✅ localhost works" || echo "❌ localhost failed"
    
    echo "  - Testing 127.0.0.1:11434:"
    podman exec local-rag-app curl -s --connect-timeout 3 http://127.0.0.1:11434/api/tags && echo "✅ 127.0.0.1 works" || echo "❌ 127.0.0.1 failed"
    
    echo "  - Testing 10.0.2.2:11434 (default Podman host):"
    podman exec local-rag-app curl -s --connect-timeout 3 http://10.0.2.2:11434/api/tags && echo "✅ 10.0.2.2 works" || echo "❌ 10.0.2.2 failed"
    
    echo "  - Testing host.containers.internal:11434:"
    podman exec local-rag-app curl -s --connect-timeout 3 http://host.containers.internal:11434/api/tags && echo "✅ host.containers.internal works" || echo "❌ host.containers.internal failed"
    
    # Get the actual host IP
    HOST_IP=$(ip route | grep default | awk '{print $3}' | head -1)
    echo "  - Testing host IP ${HOST_IP}:11434:"
    podman exec local-rag-app curl -s --connect-timeout 3 http://${HOST_IP}:11434/api/tags && echo "✅ Host IP works" || echo "❌ Host IP failed"

    echo ""
    echo "6. DNS resolution test:"
    podman exec local-rag-app nslookup host.containers.internal 2>/dev/null || echo "DNS resolution failed"

    echo ""
    echo "7. What URL is the RAG system using?"
    podman exec local-rag-app python -c "
from rag_backend import get_rag_system
rag_sys = get_rag_system()
print('RAG system LLM URL:', rag_sys.llm_client.base_url)
print('Testing connection with RAG URL:')
try:
    health = rag_sys.llm_client.health_check()
    print('Health check result:', health)
except Exception as e:
    print('Health check error:', e)
"

else
    echo "❌ Container not running"
fi

echo ""
echo "=== Recommendations ==="
echo "If 10.0.2.2 works: Set OLLAMA_HOST=10.0.2.2:11434 in docker-compose.yml"
echo "If host IP works: Set OLLAMA_HOST=${HOST_IP:-HOST_IP}:11434 in docker-compose.yml"
echo "If localhost works: Ollama might be bound to all interfaces"