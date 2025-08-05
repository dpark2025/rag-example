# RAG System Troubleshooting FAQ

**Authored by: Harry Lewis (louie) - Technical Writer**  
**Date: 2025-08-04**

Comprehensive troubleshooting guide covering common issues, performance optimization, and error explanations for the RAG system.

## Table of Contents

1. [System Startup Issues](#system-startup-issues)
2. [Document Upload Problems](#document-upload-problems)
3. [Chat and Query Issues](#chat-and-query-issues)
4. [Performance Problems](#performance-problems)
5. [Connection and Network Issues](#connection-and-network-issues)
6. [Error Messages Explained](#error-messages-explained)
7. [Performance Optimization](#performance-optimization)
8. [System Maintenance](#system-maintenance)

---

## System Startup Issues

### 🚨 System Won't Start

**Problem:** RAG system components fail to start or show errors during startup.

**Quick Diagnosis:**
```bash
# Check all system components
make health

# Check individual services
curl http://localhost:8000/health    # RAG Backend
curl http://localhost:11434/api/tags # Ollama
curl http://localhost:8002/api/v1/heartbeat # ChromaDB
```

**Common Solutions:**

**1. Port Already in Use**
```bash
# Kill existing processes
lsof -ti:3000 | xargs kill -9  # Reflex UI
lsof -ti:8000 | xargs kill -9  # RAG Backend
lsof -ti:8001 | xargs kill -9  # Reflex Backend
lsof -ti:11434 | xargs kill -9 # Ollama

# Clean restart
make restart
```

**2. Missing Dependencies**
```bash
# Install all required packages
pip install -r requirements.reflex.txt
pip install -r app/requirements.txt

# Verify installation
python -c "import reflex; print('✅ Reflex OK')"
python -c "import fastapi; print('✅ FastAPI OK')"
```

**3. Ollama Not Running**
```bash
# Start Ollama
ollama serve

# Verify model is available
ollama list
# If no models: ollama pull llama3.2:3b
```

### 🔄 Services Start But System Shows Offline

**Problem:** Individual services start but system health checks fail.

**Diagnosis Steps:**
1. **Check service connectivity:**
   ```bash
   curl -s http://localhost:8000/health | jq
   curl -s http://localhost:11434/api/tags
   curl -s http://localhost:8002/api/v1/heartbeat
   ```

2. **Verify container status (if using containers):**
   ```bash
   docker ps  # or podman ps
   docker logs rag-backend  # Check for errors
   ```

**Solutions:**
- **Service Discovery Issues:** Restart all services in order (Ollama → Backend → UI)
- **Container Network Issues:** Rebuild containers with `make clean && make setup`
- **Firewall/Security Software:** Ensure localhost ports 3000, 8000, 8001, 8002, 11434 are allowed

---

## Document Upload Problems

### 📄 Upload Fails or Stalls

**Problem:** Documents fail to upload or get stuck in processing.

**Common Causes & Solutions:**

**1. File Size Too Large**
- **Symptom:** Upload progress bar stalls or fails
- **Solution:** Keep files under 50MB; break large documents into sections
- **Check current limits:** Visit http://localhost:8000/docs for API limits

**2. Unsupported File Format**
- **Supported:** PDF, TXT, MD, DOCX, RTF
- **Not Supported:** Images (PNG, JPG), compressed files (ZIP, RAR), encrypted files
- **Solution:** Convert to supported format or extract text first

**3. Corrupted or Invalid Files**
- **Symptom:** Upload completes but processing fails with error status
- **Diagnosis:** Check document status in Documents page
- **Solution:** Re-download/recreate the file, verify it opens normally in other applications

**4. Password-Protected Files**
- **Symptom:** Processing fails with "Cannot extract text" error
- **Solution:** Remove password protection before uploading

**5. PDF with No Extractable Text (Image-Only PDFs)**
- **Symptom:** Upload succeeds but no content available for queries
- **Solution:** Use OCR software to convert to text-searchable PDF first

### 🔄 Processing Stuck or Very Slow

**Problem:** Documents remain in "Processing" status for extended periods.

**Immediate Actions:**
```bash
# Check processing queue status
curl http://localhost:8000/processing/status

# Check system resources
docker stats  # or podman stats
# Look for high CPU/memory usage
```

**Solutions:**
1. **High System Load:** Wait for other uploads to complete, or restart backend
2. **Large File Processing:** Be patient - large files can take several minutes
3. **Memory Issues:** Restart services if available memory is low
4. **Stuck Queue:** Restart RAG backend: `docker restart rag-backend`

### 🗑️ Cannot Delete Documents

**Problem:** Documents won't delete or show errors during deletion.

**Diagnosis:**
```bash
# Check document status
curl http://localhost:8000/api/v1/documents

# Try API deletion directly
curl -X DELETE http://localhost:8000/api/v1/documents/{doc_id}
```

**Solutions:**
- **File in Use:** Ensure no queries are actively using the document
- **Database Lock:** Restart ChromaDB container: `docker restart chromadb`
- **Permission Issues:** Check file system permissions on data directory

---

## Chat and Query Issues

### 💬 No Response to Questions

**Problem:** Chat interface accepts questions but provides no response or shows errors.

**Diagnosis Checklist:**
- [ ] At least one document shows "Complete" status in Documents page
- [ ] System status indicators show green (online)
- [ ] Question is in a language supported by your model
- [ ] Similarity threshold isn't set too high (try 0.5-0.7)

**Step-by-Step Solutions:**

**1. Verify Document Availability**
```bash
# Check if documents are indexed
curl http://localhost:8000/api/v1/documents
# Look for "status": "complete" documents
```

**2. Test with Simple Query**
- Try: "What documents do I have?" 
- This should work even with minimal content

**3. Check Model Connectivity**
```bash
# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Hello, are you working?",
  "stream": false
}'
```

**4. Adjust Query Settings**
- Lower similarity threshold to 0.4-0.6
- Increase max chunks to 5-7
- Try shorter, more specific questions

### 🐌 Very Slow Responses

**Problem:** Queries take excessive time to complete (>30 seconds).

**Performance Diagnosis:**
```bash
# Check system resources
top -p $(pgrep -d',' -f 'ollama|python|reflex')

# Monitor response times
curl -w "Time: %{time_total}s\n" -o /dev/null -s http://localhost:8000/health
```

**Optimization Solutions:**

**1. Reduce Query Complexity**
- Lower max chunks from 10 to 3-5
- Use shorter, more focused questions
- Avoid very broad queries across many documents

**2. System Resource Issues**
- Close unnecessary browser tabs
- Free up system memory (close other applications)
- Consider smaller language model if using 8B+ models

**3. Database Optimization**
```bash
# Restart ChromaDB to clear caches
docker restart chromadb

# Clean up old processing tasks
curl -X POST http://localhost:8000/api/v1/upload/cleanup
```

### ❓ Poor Quality or Irrelevant Answers

**Problem:** System provides answers but they're not helpful or relevant.

**Immediate Improvements:**

**1. Adjust Query Settings**
- **Increase similarity threshold** to 0.7-0.8 for more precise results
- **Reduce max chunks** to 2-3 for focused answers
- **Rephrase questions** to be more specific

**2. Improve Question Quality**
- ❌ "Tell me about the project"
- ✅ "What are the project milestones and deadlines mentioned in the Q3 report?"

**3. Document Quality Check**
- Ensure uploaded documents actually contain the information you're seeking
- Verify documents processed correctly (check processing status)
- Consider adding more relevant documents to your knowledge base

---

## Performance Problems

### 🐌 System Running Slowly

**Problem:** Overall system performance is sluggish with slow page loads and interactions.

**Resource Monitoring:**
```bash
# Check system resources
htop  # or top on older systems

# Check container resources
docker stats

# Check disk space
df -h
```

**Performance Solutions:**

**1. Memory Management**
```bash
# Check memory usage
free -h

# If low memory, restart services
make restart

# Or restart individual components
docker restart rag-backend chromadb
```

**2. Disk Space Issues**
```bash
# Check available space
df -h

# Clean up old logs and caches
docker system prune -f
# Remove unused document uploads
rm -rf /tmp/upload_*
```

**3. Browser Performance**
- Close unnecessary browser tabs
- Clear browser cache and cookies for localhost
- Try a different browser (Chrome/Firefox/Safari)
- Disable browser extensions that might interfere

### 📈 High Resource Usage

**Problem:** System consuming excessive CPU, memory, or disk space.

**Diagnosis:**
```bash
# Identify resource-heavy processes
ps aux --sort=-%cpu | head
ps aux --sort=-%mem | head

# Check container resource usage
docker stats --no-stream
```

**Solutions:**

**1. CPU Usage High**
- **Ollama Model:** Consider switching to smaller model (3B instead of 8B)
- **Batch Processing:** Avoid uploading many documents simultaneously
- **Query Optimization:** Reduce max chunks, increase similarity threshold

**2. Memory Usage High**
```bash
# Restart memory-intensive services
docker restart rag-backend
ollama stop && ollama serve
```

**3. Disk Usage High**
```bash
# Check largest directories
du -sh ~/.ollama/models/*
du -sh ./data/*

# Clean up if needed
docker system prune -a
# Remove unused Ollama models: ollama rm <model-name>
```

---

## Connection and Network Issues

### 🌐 Cannot Access Web Interface

**Problem:** Browser shows "connection refused" or "site can't be reached" for localhost:3000.

**Diagnosis Steps:**
```bash
# Check if Reflex is running
ps aux | grep reflex
netstat -tlnp | grep 3000

# Check Reflex logs
cd app/reflex_app && reflex run --loglevel debug
```

**Solutions:**

**1. Reflex Not Started**
```bash
cd app/reflex_app
export PYTHONPATH="/path/to/your/project/app/reflex_app"
reflex run
```

**2. Port Conflict**
```bash
# Kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
reflex run --port 3001
```

**3. Firewall/Security Issues**
- Ensure localhost connections are allowed
- Try accessing via 127.0.0.1:3000 instead of localhost:3000
- Disable VPN if using one

### 🔌 Backend API Unreachable

**Problem:** Frontend loads but cannot connect to backend services.

**Quick Tests:**
```bash
# Test each backend service
curl http://localhost:8000/health
curl http://localhost:8001/ping  # Reflex backend
curl http://localhost:11434/api/tags
curl http://localhost:8002/api/v1/heartbeat
```

**Solutions:**

**1. Service Not Running**
```bash
# Start missing services
make setup  # Starts all backend services

# Or individually:
cd app && python main.py  # RAG backend
ollama serve              # Ollama
```

**2. Container Issues (if using containers)**
```bash
# Check container status
docker ps -a

# Restart problematic containers
docker restart rag-backend chromadb

# Clean restart all containers
make clean && make setup
```

---

## Error Messages Explained

### 🚨 Common Error Messages and Solutions

#### "Connection to ChromaDB failed"
**Cause:** Vector database is not running or unreachable  
**Solution:**
```bash
# Check ChromaDB status
curl http://localhost:8002/api/v1/heartbeat

# Restart if needed
docker restart chromadb
```

#### "Ollama model not found"
**Cause:** Required language model not installed  
**Solution:**
```bash
# List available models
ollama list

# Install required model
ollama pull llama3.2:3b
```

#### "Document processing failed: No text extracted"
**Cause:** PDF contains only images or is corrupted  
**Solution:** 
- Use OCR software to create searchable PDF
- Try different PDF file
- Convert to text format first

#### "Rate limit exceeded"
**Cause:** Too many requests sent too quickly  
**Solution:**
- Wait 1-2 minutes before retrying
- Reduce frequency of requests
- Check for stuck processing loops

#### "Insufficient memory to process request"
**Cause:** System running low on available memory  
**Solution:**
```bash
# Free up memory
docker restart rag-backend
# Close unnecessary applications
# Consider using smaller language model
```

#### "Invalid similarity threshold"
**Cause:** Similarity setting outside valid range (0.0-1.0)  
**Solution:** Reset similarity threshold to default value (0.7)

#### "WebSocket connection failed"
**Cause:** Real-time updates cannot connect between frontend and backend  
**Solution:**
```bash
# Restart Reflex backend
pkill -f "reflex"
cd app/reflex_app && reflex run
```

---

## Performance Optimization

### 🚀 Speed Optimization Tips

#### System-Level Optimizations

**1. Resource Allocation**
```bash
# For containers, limit memory usage
# Add to docker-compose.yml:
services:
  rag-backend:
    mem_limit: 4g
    cpus: 2.0
```

**2. Model Selection**
- **Faster:** llama3.2:3b (3GB VRAM, ~1-2s response time)
- **Balanced:** llama3.1:8b (8GB VRAM, ~3-5s response time)
- **Quality:** llama3.1:70b (40GB+ VRAM, ~10-30s response time)

**3. Query Optimization**
- **Similarity Threshold:** 0.7-0.8 for precision, 0.4-0.6 for recall
- **Max Chunks:** 2-3 for speed, 5-7 for comprehensiveness
- **Question Length:** Shorter questions generally process faster

#### Document Processing Optimization

**1. Batch Upload Strategy**
```bash
# Process documents during off-peak hours
# Upload 5-10 documents at a time rather than 50+
# Monitor system resources during batch operations
```

**2. Document Preparation**
- Use text formats (TXT, MD) for fastest processing
- Ensure PDFs are text-searchable, not image-based  
- Break large documents (>50 pages) into chapters/sections
- Use consistent formatting and structure

**3. Storage Optimization**
```bash
# Clean up processed upload tasks
curl -X POST http://localhost:8000/api/v1/upload/cleanup

# Monitor storage usage
curl http://localhost:8000/api/v1/documents/stats
```

### 💾 Memory Management

#### System Memory Optimization

**1. Container Memory Limits**
```yaml
# docker-compose.yml
services:
  rag-backend:
    mem_limit: 4g
  chromadb:
    mem_limit: 2g
```

**2. Browser Memory Management**
- Close unused tabs when using RAG system
- Refresh page if experiencing slowdowns
- Use Chrome's Task Manager to monitor memory usage

**3. System-Wide Memory**
```bash
# Check memory usage
free -h

# Clear system caches (Linux)
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# macOS: Restart services instead of clearing caches
make restart
```

---

## System Maintenance

### 🧹 Regular Maintenance Tasks

#### Daily Maintenance
- [ ] Check system health indicators in UI
- [ ] Monitor storage usage if uploading many documents
- [ ] Review any error messages in chat interface

#### Weekly Maintenance
```bash
# Clean up completed upload tasks
curl -X POST http://localhost:8000/api/v1/upload/cleanup

# Check system health comprehensively
make health

# Review performance metrics
curl http://localhost:8000/health/metrics
```

#### Monthly Maintenance
```bash
# Clean up Docker/Podman resources
docker system prune -f

# Update system components (when updates available)
pip install -r requirements.reflex.txt --upgrade
pip install -r app/requirements.txt --upgrade

# Backup important documents and conversations
# (Manual backup of data directory)
```

### 🔄 System Recovery Procedures

#### Soft Reset (Preserve Data)
```bash
# Restart all services without losing documents
make restart

# Or restart individual components
docker restart rag-backend chromadb
pkill -f reflex && cd app/reflex_app && reflex run
```

#### Hard Reset (Clean Start)
```bash
# Stop all services
make stop

# Clean up containers and caches
make clean

# Fresh start
make setup
cd app/reflex_app && reflex run
```

#### Emergency Recovery
```bash
# If system is completely unresponsive
pkill -f "ollama|python|reflex"
docker stop $(docker ps -q)

# Wait 30 seconds, then restart
sleep 30
make setup
cd app/reflex_app && reflex run
```

### 📊 Health Monitoring

#### Regular Health Checks
```bash
# Automated health check script
#!/bin/bash
echo "🔍 Checking RAG System Health..."

# Check each service
curl -s http://localhost:8000/health > /dev/null && echo "✅ RAG Backend OK" || echo "❌ RAG Backend DOWN"
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama OK" || echo "❌ Ollama DOWN"  
curl -s http://localhost:8002/api/v1/heartbeat > /dev/null && echo "✅ ChromaDB OK" || echo "❌ ChromaDB DOWN"
curl -s http://localhost:3000 > /dev/null && echo "✅ Reflex UI OK" || echo "❌ Reflex UI DOWN"

echo "🏁 Health check complete"
```

#### Performance Monitoring
```bash
# Monitor response times
time curl -s http://localhost:8000/health > /dev/null

# Check resource usage trends
docker stats --no-stream

# Monitor disk usage growth
du -sh ./data && df -h
```

---

## Getting Additional Help

### 📞 When to Seek Help

**Seek additional support when:**
- System completely fails to start after following all troubleshooting steps
- Data loss or corruption occurs
- Performance issues persist despite optimization
- Security concerns arise
- New error messages not covered in this FAQ

### 📋 Information to Gather Before Seeking Help

**System Information:**
```bash
# Operating system and version
uname -a

# Python version
python --version

# Container runtime version
docker --version  # or podman --version

# Service status
make health
```

**Error Information:**
- Exact error messages (copy and paste)
- Steps that led to the error
- Screenshots of error screens
- Log files from relevant services

**System Logs:**
```bash
# Backend logs
docker logs rag-backend

# Reflex logs
cd app/reflex_app && reflex run --loglevel debug
```

### 🔗 Additional Resources

- **[User Manual](user_manual.md)** - Comprehensive usage guide
- **[Quick Start Tutorial](quick_start_tutorial.md)** - Getting started guide
- **[Feature Overview](feature_overview.md)** - Complete feature documentation
- **System Documentation** - Technical implementation details in `/docs/`

---

**💡 Remember:** Most issues can be resolved by restarting services or checking basic connectivity. When in doubt, try `make restart` first!

---

**Last Updated:** August 4, 2025  
**Version:** 1.0  
**Support Level:** Community FAQ