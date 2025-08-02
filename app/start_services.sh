#!/bin/bash

echo "🚀 Starting Local RAG System services..."

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Shutting down services..."
    kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null
    wait
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start FastAPI in the background
echo "📡 Starting FastAPI server on port 8000..."
python main.py &
FASTAPI_PID=$!

# Wait a moment for FastAPI to start
sleep 3

# Check if FastAPI started successfully
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "✅ FastAPI server started (PID: $FASTAPI_PID)"
else
    echo "❌ FastAPI server failed to start"
    exit 1
fi

# Start Streamlit in the background
echo "🎨 Starting Streamlit UI on port 8501..."
streamlit run agent_ui.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true &
STREAMLIT_PID=$!

# Wait a moment for Streamlit to start
sleep 3

# Check if Streamlit started successfully
if kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "✅ Streamlit UI started (PID: $STREAMLIT_PID)"
else
    echo "❌ Streamlit UI failed to start"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

echo "🎉 All services started successfully!"
echo "📊 Service status:"
echo "  - FastAPI (PID: $FASTAPI_PID) - http://localhost:8000"
echo "  - Streamlit (PID: $STREAMLIT_PID) - http://localhost:8501"

# Wait for either process to exit
wait -n $FASTAPI_PID $STREAMLIT_PID

# If we get here, one of the processes died
echo "⚠️ One of the services stopped unexpectedly"
cleanup