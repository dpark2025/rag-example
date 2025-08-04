# RAG System Troubleshooting Guide

## Overview
This guide provides systematic troubleshooting procedures for common issues in the RAG System production environment.

## Quick Diagnostics

### System Health Check Script
```bash
#!/bin/bash
# Quick health check for RAG system

echo "=== RAG System Health Check ==="
echo "Timestamp: $(date)"
echo

# Service availability
echo "=== Service Health ==="
services=("8000:RAG-Backend" "3000:Reflex-Frontend" "8002:ChromaDB" "6379:Redis")
for service in "${services[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    if nc -z localhost $port; then
        echo "✓ $name (port $port) - UP"
    else
        echo "✗ $name (port $port) - DOWN"
    fi
done

# Resource usage
echo
echo "=== Resource Usage ==="
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "CPU: $(top -bn1 | grep load | awk '{printf "%.2f\n", $(NF-2)}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $5 " used"}')"

# Container status (if using Docker)
echo
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep rag
```

## Issue Categories

## 1. Service Startup Failures

### Symptoms
- Container/pod fails to start
- Service health checks failing
- Application logs show initialization errors

### Diagnostic Steps

#### Check Container/Pod Status
```bash
# Docker Compose
docker-compose -f docker-compose.production.yml ps
docker logs <container-name>

# Kubernetes
kubectl get pods -n rag-system
kubectl describe pod <pod-name> -n rag-system
kubectl logs <pod-name> -n rag-system
```

#### Common Causes & Solutions

**Environment Variable Issues**
```bash
# Check environment variables
docker exec <container> env | grep -E "(SECRET_KEY|CHROMA_HOST|REDIS)"

# Kubernetes
kubectl exec <pod> -n rag-system -- env | grep -E "(SECRET_KEY|CHROMA_HOST|REDIS)"
```

**Port Conflicts**
```bash
# Check port usage
netstat -tlnp | grep -E "(8000|3000|8002|6379)"
lsof -i :8000  # Check specific port
```

**Dependency Services Not Ready**
```bash
# Test service connectivity
curl -f http://localhost:8002/api/v1/heartbeat  # ChromaDB
redis-cli -h localhost -p 6379 -a <password> ping  # Redis
```

### Resolution Actions

1. **Fix Configuration**
   ```bash
   # Update environment variables
   vim .env  # Docker Compose
   kubectl edit configmap rag-system-config -n rag-system  # K8s
   ```

2. **Restart Dependencies**
   ```bash
   # Docker Compose
   docker-compose restart chromadb redis
   
   # Kubernetes
   kubectl rollout restart deployment/chromadb -n rag-system
   ```

3. **Clear Corrupt Data**
   ```bash
   # Remove corrupt ChromaDB data
   docker-compose down
   rm -rf data/chroma/*
   ./backup-scripts/restore.sh latest
   ```

## 2. Performance Issues

### Symptoms
- High response times (>2s)
- High CPU/memory usage
- Request timeouts
- Queue backlog

### Diagnostic Steps

#### Monitor Resource Usage
```bash
# System resources
htop
iostat -x 1
vmstat 1

# Container resources
docker stats
kubectl top pods -n rag-system
```

#### Check Application Metrics
```bash
# RAG Backend metrics
curl http://localhost:8000/health/metrics

# Query performance
curl -w "@curl-format.txt" -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}' \
  http://localhost:8000/query
```

#### Analyze Logs
```bash
# High response time requests
grep "slow" /var/log/rag-system/*.log
journalctl -u docker -f | grep "response_time"

# Error patterns
grep -E "(ERROR|CRITICAL)" /var/log/rag-system/*.log | tail -50
```

### Resolution Actions

1. **Scale Services**
   ```bash
   # Docker Compose (increase resources)
   docker-compose -f docker-compose.production.yml up -d --scale rag-backend=3
   
   # Kubernetes
   kubectl scale deployment rag-backend --replicas=5 -n rag-system
   ```

2. **Optimize Database**
   ```bash
   # ChromaDB optimization
   docker exec chromadb-container chroma-admin optimize
   
   # Redis memory cleanup
   docker exec redis-container redis-cli FLUSHDB
   ```

3. **Adjust Resource Limits**
   ```yaml
   # Kubernetes resource adjustment
   resources:
     requests:
       memory: "4Gi"
       cpu: "2000m"
     limits:
       memory: "8Gi"
       cpu: "4000m"
   ```

## 3. Database Connection Issues

### Symptoms
- "Connection refused" errors
- Database timeout errors
- Authentication failures

### Diagnostic Steps

#### Test Database Connectivity
```bash
# ChromaDB
curl -f http://localhost:8002/api/v1/heartbeat
curl -f http://chromadb-service:8000/api/v1/heartbeat  # K8s

# Redis
redis-cli -h localhost -p 6379 -a <password> ping
redis-cli -h redis-service -p 6379 -a <password> ping  # K8s
```

#### Check Network Configuration
```bash
# Docker network
docker network ls
docker network inspect <network-name>

# Kubernetes network
kubectl get networkpolicies -n rag-system
kubectl describe networkpolicy <policy-name> -n rag-system
```

### Resolution Actions

1. **Restart Database Services**
   ```bash
   # Docker Compose
   docker-compose restart chromadb redis
   
   # Kubernetes
   kubectl rollout restart deployment/chromadb -n rag-system
   kubectl rollout restart deployment/redis -n rag-system
   ```

2. **Fix Network Policies**
   ```bash
   # Temporarily disable network policies for debugging
   kubectl delete networkpolicy --all -n rag-system
   
   # Test connectivity, then re-apply policies
   kubectl apply -f k8s/overlays/production/network-policies.yaml
   ```

3. **Update Connection Strings**
   ```bash
   # Verify service discovery
   nslookup chromadb-service  # K8s
   docker exec <container> nslookup chromadb  # Docker
   ```

## 4. Document Processing Failures

### Symptoms
- Upload timeouts
- Processing queue backlog
- PDF extraction errors
- Embedding generation failures

### Diagnostic Steps

#### Check Upload Handler Status
```bash
# Processing queue status
curl http://localhost:8000/api/v1/upload/tasks

# Storage statistics
curl http://localhost:8000/api/v1/documents/stats
```

#### Monitor Processing Logs
```bash
# Document processing logs
grep -E "(upload|processing|pdf)" /var/log/rag-backend/*.log | tail -50

# Error analysis
grep -E "(failed|error|timeout)" /var/log/rag-backend/*.log | grep -i document
```

### Resolution Actions

1. **Clear Processing Queue**
   ```bash
   # Clean up failed tasks
   curl -X POST http://localhost:8000/api/v1/upload/cleanup
   
   # Restart processing services
   docker-compose restart rag-backend
   ```

2. **Increase Processing Resources**
   ```bash
   # Increase timeout values
   export UPLOAD_TIMEOUT=600
   export QUERY_TIMEOUT=120
   
   # Restart with new limits
   docker-compose restart rag-backend
   ```

3. **Fix Storage Issues**
   ```bash
   # Check disk space
   df -h
   
   # Clean up old documents
   find data/documents -mtime +30 -delete
   ```

## 5. Monitoring and Alerting Issues

### Symptoms
- Missing metrics in Grafana
- Prometheus targets down
- Alert notification failures
- Log ingestion stopped

### Diagnostic Steps

#### Check Monitoring Stack
```bash
# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Grafana health
curl http://localhost:3001/api/health

# AlertManager status
curl http://localhost:9093/api/v1/status
```

#### Verify Log Collection
```bash
# Loki status
curl http://localhost:3100/ready

# Promtail status
docker logs promtail-container
```

### Resolution Actions

1. **Restart Monitoring Stack**
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart
   ```

2. **Fix Prometheus Configuration**
   ```bash
   # Validate configuration
   docker exec prometheus-container promtool check config /etc/prometheus/prometheus.yml
   
   # Reload configuration
   curl -X POST http://localhost:9090/-/reload
   ```

3. **Reset Grafana Dashboard**
   ```bash
   # Re-import dashboards
   docker exec grafana-container grafana-cli admin reset-admin-password admin
   ```

## 6. SSL/TLS Certificate Issues

### Symptoms
- HTTPS connection errors
- Certificate warnings in browser
- SSL handshake failures

### Diagnostic Steps

#### Check Certificate Status
```bash
# Certificate expiry
openssl x509 -in ssl/rag-system.crt -text -noout | grep -A2 "Validity"

# Certificate chain
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

#### Test SSL Configuration
```bash
# SSL Labs test (external)
curl -s "https://api.ssllabs.com/api/v3/analyze?host=your-domain.com"

# Local SSL test
openssl s_client -connect localhost:443 -servername localhost
```

### Resolution Actions

1. **Renew Certificates**
   ```bash
   # Let's Encrypt renewal
   certbot renew --nginx
   
   # Update Kubernetes secret
   kubectl create secret tls rag-system-tls \
     --cert=new-cert.crt --key=new-key.key \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

2. **Fix Nginx Configuration**
   ```bash
   # Test Nginx config
   nginx -t
   
   # Reload configuration
   nginx -s reload
   ```

## Emergency Procedures

### Complete System Failure

1. **Immediate Response**
   ```bash
   # Check if it's a partial outage
   ./scripts/health-check.sh
   
   # Enable maintenance mode
   kubectl apply -f k8s/maintenance-mode.yaml
   ```

2. **Emergency Rollback**
   ```bash
   # Rollback to last known good state
   ./backup-scripts/restore.sh latest
   docker-compose -f docker-compose.production.yml up -d
   ```

3. **Escalation**
   - Contact on-call engineer: +1-555-ONCALL
   - Create incident ticket: incident-system.company.com
   - Notify stakeholders via status page

### Data Corruption

1. **Stop all services immediately**
2. **Assess damage scope**
3. **Restore from backup**
4. **Verify data integrity**
5. **Gradual service restart**

## Tools and Utilities

### Diagnostic Scripts Location
- `/scripts/health-check.sh` - System health verification
- `/scripts/performance-test.sh` - Load testing
- `/scripts/log-analyzer.sh` - Log analysis automation

### Useful Commands
```bash
# Quick service restart
alias restart-rag="docker-compose -f docker-compose.production.yml restart"

# Log monitoring
alias logs-backend="docker logs -f rag-backend-prod"
alias logs-all="docker-compose -f docker-compose.production.yml logs -f"

# Resource monitoring
alias rag-stats="docker stats --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'"
```

## Documentation Links

- [Deployment Runbook](deployment.md)
- [Monitoring Guide](../procedures/monitoring.md)
- [Backup/Recovery Procedures](../procedures/backup-recovery.md)
- [Performance Tuning Guide](../procedures/performance-tuning.md)

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial troubleshooting guide | DevOps Team |