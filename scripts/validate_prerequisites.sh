#!/bin/bash
# Phase 1: Prerequisites Validation
# Validates system requirements and dependencies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/command_validator.sh"

log "${BLUE}=== PHASE 1: Prerequisites Validation ===${NC}"
log "Validating system requirements and dependencies"

# System version checks
log "${BLUE}--- System Requirements ---${NC}"

validate_command "python3 --version" "Python 3\.(11|12|13)" 10 "Python version check" true
validate_command "python --version || python3 --version" "Python 3\.(11|12|13)" 10 "Python availability" true

# Container runtime check (Docker or Podman)
log "${BLUE}--- Container Runtime ---${NC}"
if command -v docker >/dev/null 2>&1; then
    validate_command "docker --version" "Docker version" 10 "Docker availability"
    CONTAINER_CMD="docker"
elif command -v podman >/dev/null 2>&1; then
    validate_command "podman --version" "podman version" 10 "Podman availability"
    CONTAINER_CMD="podman"
else
    log "${RED}❌ Neither Docker nor Podman found${NC}"
    log "${YELLOW}Install one of:${NC}"
    log "  - Docker: https://docs.docker.com/get-docker/"
    log "  - Podman: https://podman.io/getting-started/installation"
    increment_total
    increment_failed
fi

# Build tools
log "${BLUE}--- Build Tools ---${NC}"
validate_command "make --version" "GNU Make" 10 "Make availability" true
validate_command "git --version" "git version" 10 "Git availability"

# Ollama check
log "${BLUE}--- Ollama LLM Runtime ---${NC}"
if command -v ollama >/dev/null 2>&1; then
    validate_command "ollama --version" "ollama version" 10 "Ollama installation"
else
    log "${RED}❌ Ollama not found${NC}"
    log "${YELLOW}Install Ollama:${NC}"
    log "  curl -fsSL https://ollama.ai/install.sh | sh"
    increment_total
    increment_failed
fi

# Port availability checks
log "${BLUE}--- Port Availability ---${NC}"
required_ports=(3000 8000 8001 8002 11434)
port_descriptions=("Reflex UI" "RAG Backend" "Reflex Backend" "ChromaDB" "Ollama")

for i in "${!required_ports[@]}"; do
    port="${required_ports[$i]}"
    desc="${port_descriptions[$i]}"
    
    if check_port_available "$port" "$desc"; then
        increment_passed
    else
        increment_failed
        log "${YELLOW}To free port $port:${NC} lsof -ti:$port | xargs kill -9"
    fi
    increment_total
done

# Resource availability checks
log "${BLUE}--- Resource Availability ---${NC}"

# Disk space check (need at least 2GB)
disk_available=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$disk_available" -gt 2 ]; then
    log "${GREEN}✅ Disk Space: ${disk_available}GB available${NC}"
    increment_passed
else
    log "${RED}❌ Disk Space: ${disk_available}GB available (need >2GB)${NC}"
    increment_failed
fi
increment_total

# Memory check (need at least 4GB)
mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
if [ "${mem_total:-0}" -gt 4 ]; then
    log "${GREEN}✅ System Memory: ${mem_total}GB total${NC}"
    increment_passed
else
    log "${YELLOW}⚠️  System Memory: ${mem_total}GB total (recommend >4GB for optimal performance)${NC}"
    increment_passed
fi
increment_total

# CPU check
cpu_cores=$(nproc)
if [ "$cpu_cores" -gt 1 ]; then
    log "${GREEN}✅ CPU Cores: $cpu_cores cores available${NC}"
    increment_passed
else
    log "${YELLOW}⚠️  CPU Cores: $cpu_cores core (recommend >2 cores)${NC}"
    increment_passed
fi
increment_total

# Network connectivity check
log "${BLUE}--- Network Connectivity ---${NC}"
validate_command "curl -s --max-time 10 https://ollama.ai >/dev/null" "" 10 "Internet connectivity (for downloads)"

# Python package manager
log "${BLUE}--- Python Package Manager ---${NC}"
validate_command "pip --version || pip3 --version" "pip" 10 "pip availability" true

# Optional but recommended tools
log "${BLUE}--- Optional Tools ---${NC}"
if command -v curl >/dev/null 2>&1; then
    validate_command "curl --version" "curl" 5 "curl availability"
else
    log "${YELLOW}⚠️  curl not found (recommended for API testing)${NC}"
fi

if command -v jq >/dev/null 2>&1; then
    validate_command "jq --version" "jq" 5 "jq availability"
else
    log "${YELLOW}⚠️  jq not found (helpful for JSON processing)${NC}"
fi

# Directory permissions check
log "${BLUE}--- Directory Permissions ---${NC}"
if [ -w "." ]; then
    log "${GREEN}✅ Current directory writable${NC}"
    increment_passed
else
    log "${RED}❌ Current directory not writable${NC}"
    increment_failed
fi
increment_total

# Summary and recommendations
log ""
log "${BLUE}--- Prerequisites Summary ---${NC}"

if [ $FAILED_COMMANDS -eq 0 ]; then
    log "${GREEN}🎉 All prerequisites met!${NC}"
    log "${GREEN}✅ System ready for RAG system installation${NC}"
else
    log "${RED}❌ Prerequisites not met (${FAILED_COMMANDS} issues)${NC}"
    log "${YELLOW}📋 Required actions:${NC}"
    
    # Specific recommendations based on what failed
    if ! command -v python3 >/dev/null 2>&1; then
        log "  - Install Python 3.11+: https://python.org/downloads/"
    fi
    
    if ! command -v docker >/dev/null 2>&1 && ! command -v podman >/dev/null 2>&1; then
        log "  - Install Docker: https://docs.docker.com/get-docker/"
        log "    OR"
        log "  - Install Podman: https://podman.io/getting-started/installation"
    fi
    
    if ! command -v ollama >/dev/null 2>&1; then
        log "  - Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    fi
    
    if ! command -v make >/dev/null 2>&1; then
        log "  - Install Make:"
        log "    macOS: xcode-select --install"
        log "    Ubuntu/Debian: sudo apt-get install build-essential"
        log "    CentOS/RHEL: sudo yum groupinstall 'Development Tools'"
    fi
    
    # Port conflict resolution
    for port in "${required_ports[@]}"; do
        if lsof -i ":$port" >/dev/null 2>&1; then
            log "  - Free port $port: lsof -ti:$port | xargs kill -9"
        fi
    done
fi

log "${BLUE}Prerequisites validation completed${NC}"
log ""

# Return appropriate exit code
if [ $FAILED_COMMANDS -eq 0 ]; then
    exit 0
else
    exit 1
fi