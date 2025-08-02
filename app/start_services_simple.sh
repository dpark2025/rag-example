#!/bin/bash
set -e

echo "🚀 Starting Local RAG System services..."

# Start FastAPI server
echo "📡 Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info &
FASTAPI_PID=$!

# Give FastAPI time to start
sleep 5

# Check if FastAPI is running
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "❌ FastAPI failed to start"
    exit 1
fi

echo "✅ FastAPI started on port 8000"

# Start Streamlit
echo "🎨 Starting Streamlit..."
streamlit run agent_ui.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true &
STREAMLIT_PID=$!

# Give Streamlit time to start  
sleep 5

# Check if Streamlit is running
if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "❌ Streamlit failed to start"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

echo "✅ Streamlit started on port 8501"
echo "🎉 Both services running!"

# Wait for any process to exit
wait