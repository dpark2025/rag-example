#!/bin/bash
# Phase 2: Foundation Setup Validation
# Tests core system initialization and setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/command_validator.sh"

log "${BLUE}=== PHASE 2: Foundation Setup Validation ===${NC}"
log "Testing core system initialization and setup"

# Ollama service setup
log "${BLUE}--- Ollama Service Setup ---${NC}"

# Check if Ollama is already running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log "${YELLOW}Starting Ollama service...${NC}"
    
    # Start Ollama in background
    if command -v ollama >/dev/null 2>&1; then
        nohup ollama serve > ollama.log 2>&1 &
        OLLAMA_PID=$!
        log "${BLUE}Ollama started with PID: $OLLAMA_PID${NC}"
        
        # Wait for Ollama to be ready
        if wait_for_service "Ollama" "http://localhost:11434/api/tags" 30 5; then
            validate_command "curl -s http://localhost:11434/api/tags" "models" 10 "Ollama API accessibility"
        else
            log "${RED}❌ Ollama failed to start${NC}"
            increment_total
            increment_failed
        fi
    else
        log "${RED}❌ Ollama command not found${NC}"
        increment_total
        increment_failed
    fi
else
    log "${GREEN}✅ Ollama already running${NC}"
    validate_command "curl -s http://localhost:11434/api/tags" "models" 10 "Ollama API accessibility"
fi

# Model download (critical for functionality)
log "${BLUE}--- Model Management ---${NC}"

# Check if we have any models
if ollama list 2>/dev/null | grep -q "NAME"; then
    existing_models=$(ollama list | grep -v "NAME" | wc -l)
    if [ "$existing_models" -gt 0 ]; then
        log "${GREEN}✅ Found $existing_models existing model(s)${NC}"
        validate_command "ollama list" "" 10 "List existing models"
    fi
else
    log "${YELLOW}No models found, downloading recommended model...${NC}"
fi

# Try to download llama3.2:3b (smaller, faster model)
if ! ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
    log "${YELLOW}Downloading llama3.2:3b model (this may take several minutes)...${NC}"
    validate_command "ollama pull llama3.2:3b" "success\|pulled" 600 "Download llama3.2:3b model"
else
    log "${GREEN}✅ llama3.2:3b model already available${NC}"
    increment_total
    increment_passed
fi

# Verify model is available
validate_command "ollama list" "llama3.2" 10 "Verify model availability"

# Test model functionality
log "${BLUE}--- Model Functionality Test ---${NC}"
validate_command 'curl -s http://localhost:11434/api/generate -d '"'"'{"model":"llama3.2:3b","prompt":"Hello","stream":false}'"'"' | grep -q "response"' "" 30 "Test model inference"

# Python dependencies installation
log "${BLUE}--- Python Dependencies ---${NC}"

# Check if requirements files exist
if [ -f "requirements.txt" ]; then
    validate_command "pip install -r requirements.txt" "Successfully installed\|Requirement already satisfied" 180 "Install main requirements"
else
    log "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

if [ -f "requirements.reflex.txt" ]; then
    validate_command "pip install -r requirements.reflex.txt" "Successfully installed\|Requirement already satisfied" 120 "Install Reflex requirements"
else
    log "${YELLOW}⚠️  requirements.reflex.txt not found${NC}"
fi

# Test essential Python imports
log "${BLUE}--- Python Import Tests ---${NC}"
validate_command "python -c 'import reflex; print(reflex.__version__)'" "[0-9]+\.[0-9]+" 10 "Reflex import test"
validate_command "python -c 'import fastapi; print(fastapi.__version__)'" "[0-9]+\.[0-9]+" 10 "FastAPI import test"
validate_command "python -c 'import chromadb; print(chromadb.__version__)'" "[0-9]+\.[0-9]+" 10 "ChromaDB import test"
validate_command "python -c 'import sentence_transformers; print(\"OK\")'" "OK" 10 "SentenceTransformers import test"

# Make commands validation
log "${BLUE}--- Make Commands ---${NC}"

# Check ollama before proceeding
validate_command "make check-ollama" "Ollama is installed and running" 15 "Make check-ollama command" true

# Container build
log "${YELLOW}Building containers (this may take several minutes)...${NC}"
validate_command "make build" "" 300 "Make build command"

# Verify containers were built
if command -v docker >/dev/null 2>&1; then
    validate_command "docker images | grep -E '(rag|chroma)'" "" 10 "Verify Docker images built"
elif command -v podman >/dev/null 2>&1; then
    validate_command "podman images | grep -E '(rag|chroma)'" "" 10 "Verify Podman images built"
fi

# Start services
log "${BLUE}--- Service Startup ---${NC}"
validate_command "make start" "" 120 "Make start command"

# Wait for services to be ready
log "${YELLOW}Waiting for services to initialize...${NC}"
sleep 10

# Health checks
log "${BLUE}--- Service Health Checks ---${NC}"

# Define health check endpoints
declare -A health_endpoints=(
    ["RAG Backend"]="http://localhost:8000/health"
    ["ChromaDB"]="http://localhost:8002/api/v2/heartbeat"  
    ["Ollama"]="http://localhost:11434/api/tags"
)

# Wait for each service and then health check
for service in "${!health_endpoints[@]}"; do
    url="${health_endpoints[$service]}"
    
    case $service in
        "RAG Backend")
            if wait_for_service "$service" "$url" 60 5; then
                check_service_health "$service" "$url" "healthy\|ok"
            fi
            ;;
        "ChromaDB")
            if wait_for_service "$service" "$url" 60 5; then
                check_service_health "$service" "$url" "ok"
            fi
            ;;
        "Ollama")
            if wait_for_service "$service" "$url" 30 5; then
                check_service_health "$service" "$url" "models"
            fi
            ;;
    esac
done

# Comprehensive health check
validate_command "make health" "RAG Backend.*Healthy.*ChromaDB.*Healthy.*Ollama.*Healthy" 30 "Make health command"

# Test core API endpoints
log "${BLUE}--- Core API Tests ---${NC}"
validate_command 'curl -s http://localhost:8000/ | grep -q "FastAPI\|Local RAG System"' "" 10 "API root endpoint"
validate_command "curl -s http://localhost:8000/docs" "swagger\|openapi" 10 "API documentation endpoint"

# Test basic query endpoint (without documents)
log "${BLUE}--- Basic Functionality Test ---${NC}"
validate_command 'curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '"'"'{"question":"Hello","max_chunks":1}'"'"' | grep -q "answer\|response"' "" 15 "Basic query endpoint test"

# File system checks  
log "${BLUE}--- File System Setup ---${NC}"

# Check data directory creation
if [ -d "data" ]; then
    log "${GREEN}✅ Data directory exists${NC}"
    increment_passed
else
    log "${YELLOW}Creating data directory...${NC}"
    mkdir -p data
    increment_passed
fi
increment_total

# Check log files
validate_command "make logs | head -5" "" 10 "View service logs"

# Container status check
log "${BLUE}--- Container Status ---${NC}"
if command -v docker >/dev/null 2>&1; then
    validate_command "docker ps | grep -E '(rag|chroma)'" "Up" 10 "Docker container status"
elif command -v podman >/dev/null 2>&1; then
    validate_command "podman ps | grep -E '(rag|chroma)'" "Up" 10 "Podman container status"
fi

# Resource usage check
log "${BLUE}--- Resource Usage ---${NC}"
if command -v docker >/dev/null 2>&1; then
    validate_command "docker stats --no-stream | head -5" "" 10 "Container resource usage"
elif command -v podman >/dev/null 2>&1; then
    validate_command "podman stats --no-stream | head -5" "" 10 "Container resource usage"
fi

# Foundation summary
log ""
log "${BLUE}--- Foundation Setup Summary ---${NC}"

if [ $FAILED_COMMANDS -eq 0 ]; then
    log "${GREEN}🎉 Foundation setup completed successfully!${NC}"
    log "${GREEN}✅ Core services are running and healthy${NC}"
    log "${GREEN}✅ Dependencies installed correctly${NC}"
    log "${GREEN}✅ System ready for core operations testing${NC}"
else
    log "${RED}❌ Foundation setup issues detected${NC}"
    log "${YELLOW}📋 Common fixes:${NC}"
    log "  - Restart Ollama: killall ollama && ollama serve"
    log "  - Rebuild containers: make clean && make build && make start"
    log "  - Check logs: make logs"
    log "  - Free up ports: make clean"
    log "  - Check disk space: df -h"
    log "  - Check memory: free -h"
fi

log "${BLUE}Foundation setup validation completed${NC}"
log ""

# Cleanup on exit (optional)
if [[ "${CLEANUP_AFTER_TEST:-false}" == "true" ]]; then
    log "${YELLOW}Cleaning up test resources...${NC}"
    # Note: In production, you might want to keep services running
    # make stop
fi

# Return appropriate exit code
if [ $FAILED_COMMANDS -eq 0 ]; then
    exit 0
else
    exit 1
fi