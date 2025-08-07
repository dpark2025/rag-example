# Expected Command Outputs & Success Criteria

**Purpose**: Document expected outputs and success criteria for all commands in MASTER_DOCUMENTATION.md  
**Version**: 1.0  
**Last Updated**: 2025-08-07

---

## Table of Contents

1. [Prerequisites Commands](#1-prerequisites-commands)
2. [Foundation Setup Commands](#2-foundation-setup-commands)
3. [Core Operations Commands](#3-core-operations-commands)
4. [API Commands](#4-api-commands)
5. [Testing Commands](#5-testing-commands)
6. [Monitoring Commands](#6-monitoring-commands)
7. [Troubleshooting Commands](#7-troubleshooting-commands)
8. [Error Conditions](#8-error-conditions)

---

## 1. Prerequisites Commands

### System Version Checks

#### `python --version` or `python3 --version`
**Expected Output**:
```
Python 3.11.x
```
**Success Criteria**: Version >= 3.11.0  
**Timeout**: 10s  
**Failure Actions**: Install Python 3.11+

#### `docker --version`
**Expected Output**:
```
Docker version 24.0.x, build xxxxx
```
**Success Criteria**: Contains "Docker version"  
**Timeout**: 10s  
**Alternative**: `podman --version`

#### `ollama --version`
**Expected Output**:
```
ollama version is 0.1.x
```
**Success Criteria**: Contains "ollama version"  
**Timeout**: 10s  
**Failure Actions**: Install via `curl -fsSL https://ollama.ai/install.sh | sh`

#### `make --version`
**Expected Output**:
```
GNU Make 4.x
Built for x86_64-...
```
**Success Criteria**: Contains "GNU Make"  
**Timeout**: 10s

### Port Availability Checks

#### `lsof -i :3000` (should return nothing)
**Expected Output**: No output (port available)  
**Success Criteria**: Exit code 1 (no processes found)  
**Failure**: Shows process using port

#### `lsof -i :8000` (should return nothing)
**Expected Output**: No output (port available)  
**Success Criteria**: Exit code 1 (no processes found)  
**Failure**: Shows process using port

---

## 2. Foundation Setup Commands

### Ollama Service Management

#### `ollama serve`
**Expected Output**:
```
time=2024-01-01T12:00:00.000Z level=INFO source=server.go:123 msg="Ollama server starting" port=11434
```
**Success Criteria**: Server starts without error  
**Timeout**: 30s  
**Background Process**: Yes

#### `ollama list`
**Expected Output (with models)**:
```
NAME            ID          SIZE      MODIFIED
llama3.2:3b     abc123...   2.0 GB    2 hours ago
```
**Expected Output (no models)**:
```
NAME    ID    SIZE    MODIFIED
```
**Success Criteria**: Table header present  
**Timeout**: 10s

#### `ollama pull llama3.2:3b`
**Expected Output**:
```
pulling manifest
pulling xxxxx... 100% ▕████████████████▏ 2.0 GB
verifying sha256 digest
writing manifest
removing any unused layers
success
```
**Success Criteria**: Contains "success" or "pulled"  
**Timeout**: 600s (10 minutes)  
**File Size**: ~2GB download

### API Connectivity Tests

#### `curl -s http://localhost:11434/api/tags`
**Expected Output**:
```json
{"models":[{"name":"llama3.2:3b","model":"llama3.2:3b","size":2000000000,"digest":"abc123..."}]}
```
**Success Criteria**: Contains "models" key  
**Timeout**: 10s

### Dependency Installation

#### `pip install -r requirements.txt`
**Expected Output**:
```
Requirement already satisfied: reflex>=0.8.4 in /usr/local/lib/python3.11/site-packages (0.8.4)
Requirement already satisfied: fastapi>=0.115.0 in /usr/local/lib/python3.11/site-packages (0.115.0)
...
Successfully installed [package-list]
```
**Success Criteria**: Contains "Successfully installed" or "Requirement already satisfied"  
**Timeout**: 180s

---

## 3. Core Operations Commands

### Make Commands

#### `make check-ollama`
**Expected Output**:
```
🔍 Checking Ollama...
✅ Ollama is installed and running
```
**Success Criteria**: Contains "✅ Ollama is installed and running"  
**Timeout**: 15s  
**Critical**: Yes

#### `make build`
**Expected Output**:
```
podman-compose -f docker-compose.backend.yml build
Building rag-backend...
...
Successfully built xxxxx
Successfully tagged localhost/rag-backend:latest
```
**Success Criteria**: No error messages, exit code 0  
**Timeout**: 300s (5 minutes)

#### `make start`
**Expected Output**:
```
podman-compose -f docker-compose.backend.yml up -d
Creating network rag-example_default
Creating volume rag-example_chroma_data
Creating local-rag-chromadb ... done
Creating local-rag-backend  ... done
```
**Success Criteria**: Contains "done" or "started", no errors  
**Timeout**: 120s

#### `make health`
**Expected Output**:
```
Checking system health...
✅ RAG Backend: Healthy
✅ ChromaDB: Healthy
✅ Ollama: Healthy
ℹ️  Reflex UI: Not running (start with: make start-ui)
```
**Success Criteria**: All services show "✅ ... Healthy"  
**Timeout**: 30s

#### `make logs`
**Expected Output**:
```
Attaching to local-rag-backend, local-rag-chromadb
local-rag-backend    | INFO:     Started server process [1]
local-rag-backend    | INFO:     Waiting for application startup.
local-rag-chromadb   | [2024-01-01 12:00:00] INFO: Starting ChromaDB server
...
```
**Success Criteria**: Shows container logs without errors  
**Timeout**: 10s  
**Continuous**: Yes (use Ctrl+C to exit)

---

## 4. API Commands

### Health Endpoints

#### `curl -s http://localhost:8000/health`
**Expected Output**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "ollama": "healthy"
  }
}
```
**Success Criteria**: Contains `"status": "healthy"`  
**HTTP Status**: 200  
**Timeout**: 10s

#### `curl -s http://localhost:8002/api/v2/heartbeat`
**Expected Output**:
```json
{"nanosecond heartbeat": 1704110400000000000}
```
**Success Criteria**: Contains "heartbeat" or numeric value  
**HTTP Status**: 200  
**Timeout**: 10s

### API Documentation

#### `curl -s http://localhost:8000/docs`
**Expected Output**: HTML content containing:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Local RAG System API - Swagger UI</title>
...
```
**Success Criteria**: Contains "swagger" or "openapi"  
**HTTP Status**: 200  
**Timeout**: 10s

### Query Endpoint

#### `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"Hello","max_chunks":1}'`
**Expected Output**:
```json
{
  "answer": "Hello! I'm a RAG system assistant...",
  "sources": [],
  "response_time": 2.34
}
```
**Success Criteria**: Contains "answer" key  
**HTTP Status**: 200  
**Timeout**: 15s

---

## 5. Testing Commands

### Unit Tests

#### `make test-quick`
**Expected Output**:
```
pytest tests/unit/test_essential_functionality.py -v
========================= test session starts =========================
tests/unit/test_essential_functionality.py::test_import_basic PASSED
tests/unit/test_essential_functionality.py::test_health_check PASSED
========================= 5 passed in 2.34s =========================
```
**Success Criteria**: Contains "passed" and no failures  
**Timeout**: 60s

#### `make test-all`
**Expected Output**:
```
pytest tests/ --cov=app --cov-report=html --cov-report=term
========================= test session starts =========================
...
========================= 45 passed in 23.45s =========================
Coverage report generated
```
**Success Criteria**: All tests pass, coverage report generated  
**Timeout**: 300s

### Python Import Tests

#### `python -c 'import reflex; print(reflex.__version__)'`
**Expected Output**:
```
0.8.4
```
**Success Criteria**: Version number displayed, no import errors  
**Timeout**: 10s

---

## 6. Monitoring Commands

### Container Status

#### `docker ps` or `podman ps`
**Expected Output**:
```
CONTAINER ID   IMAGE                    COMMAND                  STATUS         PORTS                    NAMES
abc123...      localhost/rag-backend    "python -m uvicorn ..."  Up 5 minutes   0.0.0.0:8000->8000/tcp   local-rag-backend
def456...      chromadb/chroma:latest   "/docker-entrypoint.sh" Up 5 minutes   0.0.0.0:8002->8000/tcp   local-rag-chromadb
```
**Success Criteria**: Containers show "Up" status  
**Timeout**: 10s

#### `docker stats --no-stream` or `podman stats --no-stream`
**Expected Output**:
```
CONTAINER ID   NAME                CPU %   MEM USAGE / LIMIT   MEM %   NET I/O     BLOCK I/O
abc123...      local-rag-backend   2.34%   234MB / 8GB        2.93%   1.2kB/890B  0B/0B
def456...      local-rag-chromadb  0.15%   45MB / 8GB         0.56%   890B/1.2kB  0B/0B
```
**Success Criteria**: Shows resource usage statistics  
**Timeout**: 10s

---

## 7. Troubleshooting Commands

### Port Management

#### `lsof -i :3000`
**Expected Output (process found)**:
```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
reflex    1234  user   5u   IPv4  12345      0t0  TCP *:3000 (LISTEN)
```
**Expected Output (no process)**: No output  
**Success Criteria**: Shows process or empty (depending on context)

#### `lsof -ti:3000 | xargs kill -9`
**Expected Output**: No output (successful termination)  
**Success Criteria**: Exit code 0, processes terminated  
**Side Effect**: Port 3000 becomes available

### Service Management

#### `make clean`
**Expected Output**:
```
podman-compose -f docker-compose.backend.yml down
Stopping local-rag-backend  ... done
Stopping local-rag-chromadb ... done
Removing local-rag-backend  ... done
Removing local-rag-chromadb ... done
```
**Success Criteria**: All containers stopped and removed  
**Timeout**: 60s

#### `make restart`
**Expected Output**: Combination of clean + build + start outputs  
**Success Criteria**: Services restart successfully  
**Timeout**: 480s (8 minutes)

---

## 8. Error Conditions

### Common Failure Patterns

#### Port Already in Use
**Command**: `make start`  
**Error Output**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```
**Root Cause**: Another process using port 8000  
**Resolution**: `lsof -ti:8000 | xargs kill -9`

#### Ollama Not Running
**Command**: `make check-ollama`  
**Error Output**:
```
❌ Ollama not running. Run: ollama serve
```
**Root Cause**: Ollama service not started  
**Resolution**: `ollama serve`

#### Python Module Not Found
**Command**: `python -c 'import reflex'`  
**Error Output**:
```
ModuleNotFoundError: No module named 'reflex'
```
**Root Cause**: Missing Python dependencies  
**Resolution**: `pip install -r requirements.reflex.txt`

#### Container Build Failure
**Command**: `make build`  
**Error Output**:
```
Error response from daemon: dockerfile parse error line 15: unknown instruction: RUN
```
**Root Cause**: Dockerfile syntax error or missing dependencies  
**Resolution**: Check Dockerfile, verify base image availability

#### Insufficient Memory
**Command**: `ollama pull llama3.2:8b`  
**Error Output**:
```
Error: insufficient memory to load model
```
**Root Cause**: Not enough RAM for model  
**Resolution**: Use smaller model (`llama3.2:3b`) or increase system memory

### Health Check Failures

#### Backend Unhealthy
**Command**: `make health`  
**Error Output**:
```
❌ RAG Backend: Unhealthy
```
**Diagnosis Commands**:
- `curl -v http://localhost:8000/health`
- `make logs`
- `docker ps`

#### Database Connection Failed
**Command**: `curl http://localhost:8000/health`  
**Error Response**:
```json
{
  "status": "unhealthy",
  "error": "Database connection failed",
  "services": {
    "database": "failed"
  }
}
```
**Root Cause**: ChromaDB not accessible  
**Resolution**: Check ChromaDB container status

### Performance Issues

#### Slow Response Times
**Command**: `curl http://localhost:8000/query`  
**Symptom**: Response time > 30s  
**Possible Causes**:
- Large model size
- Insufficient CPU/RAM
- Too many chunks requested
- Cold start (first request)

#### High Memory Usage
**Command**: `docker stats`  
**Symptom**: Memory usage > 90%  
**Resolution**:
- Use smaller model
- Restart containers
- Increase system RAM

---

## Performance Benchmarks

| Operation | Expected Time | Warning Threshold | Critical Threshold |
|-----------|---------------|-------------------|-------------------|
| `make check-ollama` | 2-5s | >10s | >15s |
| `make build` | 60-180s | >300s | >600s |
| `make start` | 30-60s | >120s | >300s |
| `make health` | 5-15s | >30s | >60s |
| Model download (3B) | 120-300s | >600s | >1200s |
| API query response | 1-5s | >10s | >30s |
| Document upload (1MB) | 2-10s | >30s | >60s |

---

## Success Rate Thresholds

| Phase | Expected Success Rate | Action Required |
|-------|----------------------|-----------------|
| Prerequisites | 100% | Block testing if failed |
| Foundation | 95% | Fix critical issues |
| Core Operations | 90% | Investigate failures |
| Integration | 85% | Document known issues |
| Edge Cases | 80% | Improve error handling |

---

## Monitoring Alerts

### Critical Alerts (Immediate Action Required)
- Any prerequisite check fails
- Ollama service down
- Container build failures
- Health check returns error status
- API endpoints return 5xx errors

### Warning Alerts (Monitor Closely)
- Response times exceed warning thresholds
- Memory usage > 80%
- Disk usage > 85%
- Test success rate < expected threshold

### Info Alerts (Awareness)
- New model downloaded
- Services restarted
- Configuration changes
- Scheduled maintenance completed

---

This document serves as the definitive reference for expected command outputs and success criteria. Update this document whenever commands change or new ones are added to the system.