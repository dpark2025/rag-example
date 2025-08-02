#!/bin/bash
"""
Reflex UI Startup Script
========================
Starts the Reflex frontend with proper configuration and error handling.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REFLEX_APP_DIR="$PROJECT_ROOT/app/reflex_app"

echo -e "${BLUE}🚀 Starting Reflex UI for Local RAG System${NC}"
echo "========================================"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check if backend is running
check_backend() {
    echo -e "${BLUE}🔍 Checking backend services...${NC}"
    
    # Check FastAPI backend
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ FastAPI backend is running (port 8000)${NC}"
    else
        echo -e "${YELLOW}⚠️  FastAPI backend not detected on port 8000${NC}"
        echo -e "${YELLOW}   Start with: make start${NC}"
    fi
    
    # Check Ollama
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is running (port 11434)${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama not detected on port 11434${NC}"
        echo -e "${YELLOW}   Start with: ollama serve${NC}"
    fi
}

# Function to install dependencies
install_deps() {
    echo -e "${BLUE}📦 Checking Reflex dependencies...${NC}"
    
    if ! python -c "import reflex" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Reflex not found, installing...${NC}"
        pip install reflex>=0.8.0
    else
        echo -e "${GREEN}✅ Reflex is installed${NC}"
    fi
}

# Check if Reflex app directory exists
if [ ! -d "$REFLEX_APP_DIR" ]; then
    echo -e "${RED}❌ Reflex app directory not found: $REFLEX_APP_DIR${NC}"
    exit 1
fi

# Check if rxconfig.py exists
if [ ! -f "$REFLEX_APP_DIR/rxconfig.py" ]; then
    echo -e "${RED}❌ rxconfig.py not found in $REFLEX_APP_DIR${NC}"
    exit 1
fi

# Check port availability
echo -e "${BLUE}🔍 Checking port availability...${NC}"
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use${NC}"
    echo -e "${YELLOW}   Kill existing Reflex: pkill -f 'reflex'${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 (Reflex backend) is already in use${NC}"
fi

# Run checks
check_backend
install_deps

# Change to Reflex app directory
echo -e "${BLUE}📁 Changing to Reflex app directory...${NC}"
cd "$REFLEX_APP_DIR"

# Set PYTHONPATH for proper imports
export PYTHONPATH="$REFLEX_APP_DIR"
echo -e "${BLUE}🐍 PYTHONPATH set to: $PYTHONPATH${NC}"

# Start Reflex
echo -e "${GREEN}🚀 Starting Reflex UI...${NC}"
echo -e "${BLUE}   Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}   Backend:  http://localhost:8001${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start Reflex with error handling
reflex run || {
    echo -e "${RED}❌ Reflex failed to start${NC}"
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "   1. Check if dependencies are installed: pip install -r requirements.reflex.txt"
    echo "   2. Clear Reflex cache: rm -rf .web/"
    echo "   3. Check for component errors in the output above"
    echo "   4. Ensure backend services are running: make health"
    exit 1
}