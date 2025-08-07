# Command Troubleshooting Guide

**Purpose**: Comprehensive troubleshooting guide for all RAG system commands  
**Version**: 1.0  
**Last Updated**: 2025-08-07

---

## Table of Contents

1. [Quick Diagnosis](#1-quick-diagnosis)
2. [Common Issues by Category](#2-common-issues-by-category)
3. [Command-Specific Issues](#3-command-specific-issues)
4. [Error Code Reference](#4-error-code-reference)
5. [Recovery Procedures](#5-recovery-procedures)
6. [Advanced Troubleshooting](#6-advanced-troubleshooting)
7. [Prevention Tips](#7-prevention-tips)

---

## 1. Quick Diagnosis

### First Steps for Any Issue

```bash
# 1. Check system resources
df -h          # Disk space
free -h        # Memory
top            # CPU and processes

# 2. Check service status
make health    # Overall system health
docker ps      # Container status (or podman ps)

# 3. Check logs
make logs | tail -50    # Recent log entries

# 4. Check network connectivity  
curl -s http://localhost:8000/health
curl -s http://localhost:11434/api/tags
```

### Decision Tree for Quick Diagnosis

```
Command Failed?
├── Exit Code 127 → Command not found → Install missing tool
├── Exit Code 126 → Permission denied → Check file permissions
├── Exit Code 125 → Container error → Check Docker/Podman
├── Exit Code 1   → Generic error → Check logs
├── Timeout       → Performance issue → Check resources
└── Connection refused → Service down → Restart services
```

---

## 2. Common Issues by Category

### 2.1 Installation Issues

#### **Python Version Problems**
**Symptoms**: 
- `python: command not found`
- Version too old
- Import errors

**Solutions**:
```bash
# Check Python version
python --version || python3 --version

# Install Python 3.11+ (macOS)
brew install python@3.11

# Install Python 3.11+ (Ubuntu)
sudo apt update && sudo apt install python3.11 python3.11-pip

# Create alias if needed
echo 'alias python=python3' >> ~/.bashrc
```

#### **Docker/Podman Issues**
**Symptoms**:
- `docker: command not found`
- Permission denied
- Container won't start

**Solutions**:
```bash
# Install Docker (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Alternative: Install Podman
sudo apt install podman

# Test installation
docker run hello-world  # or podman run hello-world
```

#### **Ollama Installation Issues**
**Symptoms**:
- `ollama: command not found`
- Installation script fails
- Service won't start

**Solutions**:
```bash
# Install Ollama (official method)
curl -fsSL https://ollama.ai/install.sh | sh

# Manual installation (macOS)
brew install ollama

# Start service
ollama serve

# Verify installation
ollama --version
curl http://localhost:11434/api/tags
```

### 2.2 Port Conflicts

#### **Port Already in Use**
**Symptoms**:
- `bind: address already in use`
- `make start` fails
- Service won't start

**Diagnostic Commands**:
```bash
# Check what's using specific ports
lsof -i :3000   # Reflex UI
lsof -i :8000   # RAG Backend  
lsof -i :8001   # Reflex Backend
lsof -i :8002   # ChromaDB
lsof -i :11434  # Ollama

# Check all listening ports
netstat -tlnp | grep LISTEN
```

**Solutions**:
```bash
# Kill processes on specific ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9

# Kill all related processes
pkill -f "reflex"
pkill -f "uvicorn"
pkill -f "ollama"

# Clean restart
make clean && make start
```

### 2.3 Service Health Issues

#### **Ollama Service Problems**
**Symptoms**:
- `Connection refused` on port 11434
- `make check-ollama` fails
- Model download fails

**Diagnostic Steps**:
```bash
# Check if Ollama is running
curl -s http://localhost:11434/api/tags

# Check process
ps aux | grep ollama

# Check system resources
free -h  # Need 4GB+ for models
df -h    # Need 2GB+ for downloads
```

**Recovery Procedures**:
```bash
# Stop and restart Ollama
killall ollama
sleep 2
ollama serve &

# Wait for service to start
sleep 5
curl http://localhost:11434/api/tags

# Download model if missing
ollama pull llama3.2:3b

# Test model
ollama run llama3.2:3b "Hello"
```

#### **Backend API Issues**
**Symptoms**:
- `503 Service Unavailable`
- Health check fails
- API endpoints not responding

**Diagnostic Commands**:
```bash
# Check container status
docker ps -a | grep rag-backend
# or
podman ps -a | grep rag-backend

# Check container logs
docker logs local-rag-backend
# or  
podman logs local-rag-backend

# Check API directly
curl -v http://localhost:8000/health
curl -I http://localhost:8000/docs
```

**Solutions**:
```bash
# Restart backend
make stop && make start

# Rebuild if needed
make clean && make build && make start

# Check for dependency issues
docker exec local-rag-backend pip list
# or
podman exec local-rag-backend pip list
```

### 2.4 Resource Issues

#### **Out of Memory**
**Symptoms**:
- Model loading fails
- Container crashes
- System becomes unresponsive

**Diagnostic Commands**:
```bash
# Check memory usage
free -h
top -o %MEM | head -20

# Check container memory usage
docker stats --no-stream
# or
podman stats --no-stream
```

**Solutions**:
```bash
# Use smaller model
ollama pull llama3.2:3b  # Instead of larger models

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Restart with resource limits
docker run --memory=4g --cpus=2 ...
```

#### **Disk Space Issues**
**Symptoms**:
- Model download fails
- Container build fails
- `No space left on device`

**Diagnostic Commands**:
```bash
# Check disk usage
df -h
du -sh ~/.ollama/  # Ollama models
du -sh ./data/     # Project data

# Check Docker/Podman space usage
docker system df
# or
podman system df
```

**Solutions**:
```bash
# Clean up Docker/Podman
docker system prune -af
# or
podman system prune -af

# Remove unused models
ollama rm <unused-model>

# Clean project data
rm -rf ./data/uploads/*  # If safe to do so
```

---

## 3. Command-Specific Issues

### 3.1 Make Commands

#### **`make` command not found**
**Solution**:
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential

# CentOS/RHEL
sudo yum groupinstall 'Development Tools'
```

#### **`make check-ollama` fails**
**Common Causes & Solutions**:
```bash
# Cause: Ollama not installed
curl -fsSL https://ollama.ai/install.sh | sh

# Cause: Ollama not running
ollama serve &

# Cause: Wrong port
export OLLAMA_HOST=http://localhost:11434
```

#### **`make build` fails**
**Common Issues**:
```bash
# Issue: Docker daemon not running
sudo systemctl start docker  # Linux
# or check Docker Desktop is running (macOS/Windows)

# Issue: Permission denied
sudo usermod -aG docker $USER
newgrp docker

# Issue: Out of disk space
docker system prune -f
df -h  # Check available space
```

#### **`make start` hangs or fails**
**Diagnostic Steps**:
```bash
# Check detailed logs
make logs

# Check container status
docker ps -a
docker inspect local-rag-backend

# Manual container start for debugging
docker run -it --rm -p 8000:8000 localhost/rag-backend
```

### 3.2 Python Commands

#### **Import Errors**
**Symptoms**: `ModuleNotFoundError`, `ImportError`

**Solutions**:
```bash
# Install missing dependencies
pip install -r requirements.txt
pip install -r requirements.reflex.txt

# Check virtual environment
which python
pip list | grep reflex

# Reinstall problematic packages
pip uninstall reflex && pip install reflex

# Clear pip cache
pip cache purge
```

#### **Version Conflicts**
**Symptoms**: Dependency conflicts, version errors

**Solutions**:
```bash
# Create fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt

# Check for conflicts
pip check

# Fix specific conflicts
pip install --upgrade <package>
```

### 3.3 Curl Commands

#### **Connection Refused**
**Causes & Solutions**:
```bash
# Service not running
make start
make health

# Wrong URL/port
curl http://localhost:8000/health  # Correct
curl http://127.0.0.1:8000/health  # Alternative

# Firewall blocking
sudo ufw allow 8000  # Ubuntu
# or disable firewall temporarily for testing
```

#### **Timeout Issues**
**Solutions**:
```bash
# Increase timeout
curl --max-time 30 http://localhost:8000/health

# Check service performance
time curl http://localhost:8000/health

# Monitor service health
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

---

## 4. Error Code Reference

### Exit Codes
| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| 0    | Success | - | Normal completion |
| 1    | General error | Config issues, logic errors | Check logs, config |
| 2    | Misuse of shell builtins | Wrong arguments | Check command syntax |
| 126  | Permission denied | File not executable | `chmod +x script.sh` |
| 127  | Command not found | Missing binary | Install required tool |
| 128  | Invalid argument | Wrong exit code | Check script logic |
| 130  | Script terminated by Ctrl+C | User interrupt | Normal if intentional |

### HTTP Status Codes
| Code | Status | Meaning | Action |
|------|--------|---------|--------|
| 200  | OK | Request successful | Normal |
| 404  | Not Found | Endpoint doesn't exist | Check URL/API version |
| 500  | Internal Server Error | Server error | Check backend logs |
| 502  | Bad Gateway | Upstream server error | Check service dependencies |
| 503  | Service Unavailable | Service temporarily down | Wait/restart service |
| 504  | Gateway Timeout | Request timeout | Check performance |

### Container Error Codes
| Code | Meaning | Solutions |
|------|---------|-----------|
| 125  | Docker daemon error | Restart Docker service |
| 126  | Container command not executable | Check Dockerfile CMD/ENTRYPOINT |
| 127  | Container command not found | Verify base image, install dependencies |

---

## 5. Recovery Procedures

### 5.1 Complete System Reset

**When to Use**: Major failures, corruption, starting fresh

```bash
#!/bin/bash
# complete_reset.sh - Nuclear option

echo "🚨 COMPLETE SYSTEM RESET - This will destroy all data!"
read -p "Are you sure? (type 'yes' to continue): " confirm

if [[ $confirm != "yes" ]]; then
    echo "Aborted"
    exit 1
fi

# Stop all services
make stop || true

# Kill all related processes
pkill -f "reflex\|uvicorn\|ollama" || true

# Clean containers and volumes
docker system prune -af --volumes || true
podman system prune -af --volumes || true

# Remove project data (optional)
# rm -rf ./data/

# Remove Ollama models (optional)  
# rm -rf ~/.ollama/

# Restart from scratch
make setup

echo "✅ Complete reset finished"
```

### 5.2 Service-Specific Recovery

#### **Ollama Recovery**
```bash
#!/bin/bash
# ollama_recovery.sh

echo "🔧 Ollama Recovery Procedure"

# Stop Ollama
killall ollama || true
sleep 2

# Check for port conflicts
if lsof -i :11434; then
    echo "Killing processes on port 11434"
    lsof -ti:11434 | xargs kill -9
fi

# Start Ollama
nohup ollama serve > ollama.log 2>&1 &
sleep 5

# Verify startup
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama recovered successfully"
else
    echo "❌ Ollama recovery failed"
    cat ollama.log
    exit 1
fi

# Check/download models
if ! ollama list | grep -q llama3.2:3b; then
    echo "Downloading model..."
    ollama pull llama3.2:3b
fi

echo "✅ Ollama recovery complete"
```

#### **Container Recovery**
```bash
#!/bin/bash
# container_recovery.sh

echo "🔧 Container Recovery Procedure"

# Stop containers gracefully
make stop

# Force remove if needed
docker rm -f local-rag-backend local-rag-chromadb || true

# Clean networks and volumes
docker network prune -f
docker volume prune -f

# Rebuild and start
make clean
make build
make start

# Verify recovery
sleep 10
if make health; then
    echo "✅ Container recovery successful"
else
    echo "❌ Container recovery failed"
    make logs
    exit 1
fi
```

### 5.3 Data Recovery

#### **Backup Critical Data**
```bash
#!/bin/bash
# backup_data.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR"

# Backup ChromaDB data
if [ -d "./data" ]; then
    cp -r ./data "$BACKUP_DIR/"
    echo "✅ Backed up data directory"
fi

# Backup configuration
cp *.yml *.env* Makefile "$BACKUP_DIR/" 2>/dev/null || true

# Backup logs
cp *.log "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup complete: $BACKUP_DIR"
```

#### **Restore from Backup**
```bash
#!/bin/bash
# restore_data.sh

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-directory>"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restoring from $BACKUP_DIR"

# Stop services
make stop || true

# Restore data
if [ -d "$BACKUP_DIR/data" ]; then
    rm -rf ./data
    cp -r "$BACKUP_DIR/data" ./data
    echo "✅ Restored data directory"
fi

# Restart services
make start

echo "✅ Restore complete"
```

---

## 6. Advanced Troubleshooting

### 6.1 Performance Analysis

#### **Identify Bottlenecks**
```bash
# CPU usage by container
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Memory usage analysis
docker exec local-rag-backend python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"

# Disk I/O monitoring
iostat -x 1 5

# Network monitoring
netstat -i
```

#### **Database Performance**
```bash
# ChromaDB query performance
curl -X POST http://localhost:8002/api/v1/collections \
  -H "Content-Type: application/json" \
  -d '{"name":"test_performance"}'

# Time API responses
time curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"test","max_chunks":3}'
```

### 6.2 Network Troubleshooting

#### **Container Networking**
```bash
# Check container networks
docker network ls
docker inspect bridge

# Test inter-container connectivity
docker exec local-rag-backend ping local-rag-chromadb

# DNS resolution
docker exec local-rag-backend nslookup chromadb
```

#### **Port Mapping Issues**
```bash
# Verify port mappings
docker port local-rag-backend
docker port local-rag-chromadb

# Test from inside container
docker exec local-rag-backend curl http://localhost:8000/health

# Test from host
curl http://localhost:8000/health
```

### 6.3 Log Analysis

#### **Structured Log Analysis**
```bash
# Parse JSON logs
make logs | grep ERROR | jq '.'

# Extract specific timeframe
make logs | grep "2024-01-01 12:"

# Count error types
make logs | grep ERROR | cut -d' ' -f4 | sort | uniq -c
```

#### **Log Rotation and Management**
```bash
# Rotate logs
docker logs local-rag-backend > backend_$(date +%Y%m%d).log
docker logs --since=1h local-rag-backend

# Clean old logs
find . -name "*.log" -mtime +7 -delete
```

---

## 7. Prevention Tips

### 7.1 Proactive Monitoring

#### **Health Check Script**
```bash
#!/bin/bash
# health_monitor.sh - Run via cron every 5 minutes

LOGFILE="health_monitor.log"

health_check() {
    if make health > /tmp/health_check 2>&1; then
        echo "$(date): ✅ System healthy" >> $LOGFILE
    else
        echo "$(date): ❌ System unhealthy" >> $LOGFILE
        cat /tmp/health_check >> $LOGFILE
        
        # Auto-recovery attempt
        echo "$(date): Attempting auto-recovery" >> $LOGFILE
        make restart >> $LOGFILE 2>&1
    fi
}

health_check
```

#### **Resource Monitoring**
```bash
#!/bin/bash
# resource_monitor.sh

# Memory threshold (80%)
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f"), $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "⚠️ High memory usage: ${MEM_USAGE}%" 
    # Consider restarting services
fi

# Disk threshold (90%)  
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️ High disk usage: ${DISK_USAGE}%"
    # Clean up old files
    find ./data -type f -mtime +30 -delete
fi
```

### 7.2 Best Practices

#### **Development Environment**
- Use virtual environments for Python dependencies
- Pin dependency versions in requirements files
- Regularly update and test dependencies
- Keep development and production environments similar

#### **Container Management**
- Use health checks in Docker Compose
- Set appropriate resource limits
- Implement proper logging
- Regular cleanup of unused images/volumes

#### **System Maintenance**
- Regular backups of critical data
- Monitor disk space and clean up logs
- Keep system packages updated
- Document custom configurations

### 7.3 Validation Schedule

#### **Daily Checks** (Automated)
```bash
# Add to crontab: 0 6 * * * /path/to/daily_check.sh
./scripts/quick_validation.sh
```

#### **Weekly Checks** (Semi-automated)
```bash
# Add to crontab: 0 6 * * 1 /path/to/weekly_check.sh
./scripts/validate_all_commands.sh
```

#### **Monthly Checks** (Manual)
- Full system validation
- Performance benchmarking  
- Security updates
- Backup verification
- Documentation updates

---

## Emergency Contacts & Resources

### Quick Reference Commands
```bash
# Emergency stop all
pkill -f "reflex\|uvicorn\|ollama"
docker stop $(docker ps -q)

# Emergency logs
tail -100 /var/log/syslog
make logs | tail -100

# Emergency health check
curl -s http://localhost:8000/health | jq
curl -s http://localhost:11434/api/tags
```

### Useful Resources
- **Documentation**: [MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md)
- **Expected Outputs**: [EXPECTED_OUTPUTS.md](EXPECTED_OUTPUTS.md)
- **Validation Plan**: [COMMAND_VALIDATION_PLAN.md](COMMAND_VALIDATION_PLAN.md)
- **Docker Docs**: https://docs.docker.com/
- **Ollama Docs**: https://ollama.ai/
- **Reflex Docs**: https://reflex.dev/

---

**Remember**: When in doubt, check logs first, then try the simplest solution (restart), then escalate to more complex recovery procedures.