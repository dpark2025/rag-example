#!/bin/bash

echo "🔬 Comprehensive diagnosis and fix for FastAPI issue..."

echo "=== Step 1: Current Status ==="
echo "Container status:"
podman ps | grep local-rag-app || echo "No container running"

echo ""
echo "Port status on host:"
netstat -tlnp | grep -E "(8000|8501)" || echo "No services listening on 8000 or 8501"

echo ""
echo "=== Step 2: Container Logs ==="
if podman ps | grep -q local-rag-app; then
    echo "Recent container logs:"
    podman-compose logs --tail=20 rag-app
    
    echo ""
    echo "Processes in container:"
    podman exec local-rag-app ps aux || echo "Could not check processes"
    
    echo ""
    echo "Network status in container:"
    podman exec local-rag-app netstat -tlnp || echo "Could not check network"
fi

echo ""
echo "=== Step 3: Clean Rebuild ==="
echo "Stopping everything..."
podman-compose down 2>/dev/null || true
podman stop local-rag-app 2>/dev/null || true
podman rm local-rag-app 2>/dev/null || true

echo "Building with no cache..."
podman-compose build --no-cache

echo "Starting container..."
podman-compose up -d

echo "Waiting 10 seconds for startup..."
sleep 10

echo ""
echo "=== Step 4: Post-Start Diagnosis ==="
echo "Container status:"
podman ps | grep local-rag-app

echo ""
echo "Container logs:"
podman-compose logs --tail=30 rag-app

echo ""
echo "Testing connectivity:"
echo "- Testing Streamlit (8501):"
curl -s --connect-timeout 5 -I http://localhost:8501 | head -1 || echo "Streamlit connection failed"

echo "- Testing FastAPI docs (8000):"
curl -s --connect-timeout 5 -I http://localhost:8000/docs | head -1 || echo "FastAPI docs connection failed"

echo "- Testing FastAPI health (8000):"
curl -s --connect-timeout 5 http://localhost:8000/health || echo "FastAPI health connection failed"

echo ""
echo "=== Step 5: Manual FastAPI Test ==="
if podman ps | grep -q local-rag-app; then
    echo "Testing FastAPI import and startup manually:"
    podman exec local-rag-app python -c "
try:
    import uvicorn
    from main import app
    print('✅ FastAPI app imports successfully')
    print('✅ App object:', type(app))
except Exception as e:
    print('❌ Import error:', e)
    import traceback
    traceback.print_exc()
" || echo "Could not test imports"

    echo ""
    echo "Testing manual uvicorn start:"
    timeout 10s podman exec local-rag-app uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 5 || echo "Manual uvicorn test completed/failed"
fi

echo ""
echo "=== Results Summary ==="
echo "Check the output above for:"
echo "1. Container startup errors in logs"
echo "2. Import errors in Python"
echo "3. Network connectivity issues"
echo "4. Process failures"