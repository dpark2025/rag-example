#!/bin/bash
# Quick Validation Script - Essential Commands Only
# Tests the most critical commands for basic functionality

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/command_validator.sh"

log "${BLUE}======================================${NC}"
log "${BLUE}RAG System Quick Validation${NC}" 
log "${BLUE}======================================${NC}"
log "${BLUE}Testing essential commands for basic functionality${NC}"
log "${BLUE}Estimated time: 5-10 minutes${NC}"

# Quick system check
check_system_resources

# Essential prerequisites (must pass)
log "${BLUE}--- Essential Prerequisites ---${NC}"
validate_command "python --version || python3 --version" "Python 3\.(11|12|13)" 10 "Python availability" true
validate_command "ollama --version" "ollama version" 10 "Ollama installation" true
validate_command "make --version" "GNU Make" 10 "Make availability" true

# Container runtime
if command -v docker >/dev/null 2>&1; then
    validate_command "docker --version" "Docker version" 10 "Docker availability"
elif command -v podman >/dev/null 2>&1; then
    validate_command "podman --version" "podman version" 10 "Podman availability"
else
    log "${RED}❌ No container runtime found (Docker or Podman required)${NC}"
    increment_total
    increment_failed
fi

# Quick port check (only critical ones)
log "${BLUE}--- Critical Ports ---${NC}"
critical_ports=(8000 11434)
for port in "${critical_ports[@]}"; do
    if ! lsof -i ":$port" >/dev/null 2>&1; then
        log "${GREEN}✅ Port $port available${NC}"
        increment_passed
    else
        log "${YELLOW}⚠️  Port $port in use (may need cleanup)${NC}"
        increment_passed
    fi
    increment_total
done

# Ollama quick test
log "${BLUE}--- Ollama Quick Test ---${NC}"
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log "${YELLOW}Starting Ollama service...${NC}"
    nohup ollama serve > ollama.log 2>&1 &
    sleep 5
fi

validate_command "curl -s http://localhost:11434/api/tags" "models" 10 "Ollama API test"

# Check for existing model or download minimal one
if ollama list 2>/dev/null | grep -q "llama3.2"; then
    log "${GREEN}✅ Model available${NC}"
    increment_passed
    increment_total
else
    log "${YELLOW}Downloading minimal model for testing...${NC}"
    validate_command "ollama pull llama3.2:3b" "success\|pulled" 300 "Download test model"
fi

# Essential make commands
log "${BLUE}--- Essential Make Commands ---${NC}"
validate_command "make check-ollama" "Ollama is installed and running" 15 "Ollama check"

# Try to start services (quick test)
log "${BLUE}--- Service Startup Test ---${NC}"
validate_command "make build" "" 180 "Build containers"
validate_command "make start" "" 60 "Start services"

# Quick health check
sleep 10
log "${BLUE}--- Quick Health Check ---${NC}"
validate_command "make health" "Healthy" 30 "Services health check"

# Basic API test
log "${BLUE}--- Basic API Test ---${NC}"
validate_command "curl -s http://localhost:8000/health" "healthy\|ok" 10 "Backend health API"

# Quick summary
log ""
log "${BLUE}--- Quick Validation Summary ---${NC}"

if [ $FAILED_COMMANDS -eq 0 ]; then
    log "${GREEN}🎉 Quick validation PASSED!${NC}"
    log "${GREEN}✅ Essential components are working${NC}"
    log "${GREEN}✅ System appears ready for full validation${NC}"
    log ""
    log "${BLUE}Next steps:${NC}"
    log "  1. Run full validation: ./scripts/validate_all_commands.sh"
    log "  2. Or continue with development: make start-ui"
    log "  3. Access UI at: http://localhost:3000"
    log "  4. Access API docs at: http://localhost:8000/docs"
else
    log "${RED}❌ Quick validation FAILED${NC}"
    log "${YELLOW}Issues found - run full validation for detailed diagnostics:${NC}"
    log "  ./scripts/validate_all_commands.sh"
fi

log "${BLUE}Quick validation completed in $(date)${NC}"

# Return appropriate exit code
if [ $FAILED_COMMANDS -eq 0 ]; then
    exit 0
else
    exit 1
fi