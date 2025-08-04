# RAG System Deployment Runbook

## Overview
This runbook covers the deployment procedures for the RAG System in production environments using Docker Compose and Kubernetes.

## Prerequisites

### System Requirements
- **Minimum**: 8GB RAM, 4 CPU cores, 100GB storage
- **Recommended**: 16GB RAM, 8 CPU cores, 500GB SSD storage
- **Network**: Internet access for initial model downloads
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements
- Docker 24.0+ and Docker Compose 2.0+
- Kubernetes 1.25+ (for K8s deployment)
- kubectl configured with cluster access
- Git for repository access

### External Dependencies
- **Ollama**: Must be running on host system (port 11434)
- **SSL Certificates**: For HTTPS in production
- **SMTP Server**: For alert notifications

## Docker Compose Deployment

### 1. Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd rag-example

# Create environment file
cp .env.example .env
# Edit .env with production values

# Create required directories
mkdir -p data/{chroma,documents} logs ssl
```

### 2. Environment Configuration

**Critical Environment Variables:**
```bash
# Security
SECRET_KEY=<64-char-random-string>
API_SECRET_KEY=<64-char-random-string>
JWT_SECRET=<64-char-random-string>
REDIS_PASSWORD=<secure-password>
GRAFANA_PASSWORD=<secure-password>

# Database
CHROMA_HOST=chromadb-service
REDIS_HOST=redis-service

# SSL/TLS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/rag-system.crt
SSL_KEY_PATH=/etc/ssl/rag-system.key
```

### 3. SSL Certificate Setup

```bash
# For production, use real certificates
# For testing, generate self-signed:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/rag-system.key \
  -out ssl/rag-system.crt \
  -subj "/CN=yourdomain.com"
```

### 4. Deploy Services

```bash
# Start monitoring stack first
docker-compose -f docker-compose.monitoring.yml up -d

# Start main application
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
```

### 5. Health Verification

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:3000/_health
curl http://localhost:8002/api/v1/heartbeat

# Check monitoring
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health # Grafana
```

## Kubernetes Deployment

### 1. Cluster Preparation

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Apply secrets (update with real values first)
kubectl apply -f k8s/base/secrets.yaml

# Apply configuration
kubectl apply -f k8s/base/configmap.yaml
```

### 2. Storage Setup

```bash
# Ensure storage classes exist
kubectl get storageclass

# Apply PVCs
kubectl apply -f k8s/base/chromadb.yaml
kubectl apply -f k8s/base/redis.yaml
```

### 3. Deploy Database Layer

```bash
# Deploy ChromaDB
kubectl apply -f k8s/base/chromadb.yaml

# Deploy Redis
kubectl apply -f k8s/base/redis.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=chromadb -n rag-system --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n rag-system --timeout=300s
```

### 4. Deploy Application Layer

```bash
# Deploy RAG Backend
kubectl apply -f k8s/base/rag-backend.yaml

# Deploy Reflex Frontend
kubectl apply -f k8s/base/reflex-frontend.yaml

# Deploy Nginx Proxy
kubectl apply -f k8s/base/nginx.yaml

# Wait for applications
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=rag-backend -n rag-system --timeout=300s
```

### 5. Production Overlay

```bash
# Apply production configuration
kubectl apply -k k8s/overlays/production/

# Verify deployment
kubectl get pods -n rag-system
kubectl get services -n rag-system
kubectl get ingress -n rag-system
```

## Post-Deployment Verification

### 1. Functional Testing

```bash
# Test document upload
curl -X POST -F "files=@test-document.txt" \
  http://your-domain.com/api/v1/documents/upload

# Test query functionality
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What documents are available?"}' \
  http://your-domain.com/api/query

# Test health endpoints
curl http://your-domain.com/health
curl http://your-domain.com/api/v1/documents/stats
```

### 2. Performance Verification

```bash
# Load testing (using Apache Bench)
ab -n 100 -c 10 http://your-domain.com/health

# Memory and CPU usage
docker stats  # For Docker Compose
kubectl top pods -n rag-system  # For Kubernetes
```

### 3. Monitoring Setup

```bash
# Access Grafana
http://your-domain.com/grafana/
# Username: admin, Password: <GRAFANA_PASSWORD>

# Import dashboards and verify metrics
# Check AlertManager for alert rules
http://your-domain.com/prometheus/alerts
```

## Rollback Procedures

### Docker Compose Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.production.yml down

# Restore from backup
./backup-scripts/restore.sh latest

# Start previous version
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes Rollback

```bash
# Check deployment history
kubectl rollout history deployment/rag-backend -n rag-system

# Rollback to previous version
kubectl rollout undo deployment/rag-backend -n rag-system
kubectl rollout undo deployment/reflex-frontend -n rag-system

# Verify rollback
kubectl rollout status deployment/rag-backend -n rag-system
```

## Troubleshooting Common Issues

### Service Won't Start

1. **Check logs**: `docker logs <container>` or `kubectl logs -f <pod>`
2. **Verify environment**: Check .env file and secrets
3. **Network connectivity**: Test inter-service communication
4. **Resource limits**: Check memory/CPU availability

### Performance Issues

1. **Monitor metrics**: Check Grafana dashboards
2. **Scale services**: Increase replicas for bottlenecked services
3. **Resource allocation**: Adjust memory/CPU limits
4. **Database optimization**: Check ChromaDB and Redis performance

### SSL/Certificate Issues

1. **Certificate validation**: Check cert expiry and chain
2. **Port accessibility**: Verify 443 is open and accessible
3. **DNS resolution**: Confirm domain resolves correctly
4. **Proxy configuration**: Verify Nginx SSL configuration

## Maintenance Windows

### Scheduled Maintenance

```bash
# 1. Notify users (if applicable)
# 2. Scale down non-essential services
kubectl scale deployment reflex-frontend --replicas=1 -n rag-system

# 3. Perform maintenance tasks
# 4. Verify system health
# 5. Scale services back up
kubectl scale deployment reflex-frontend --replicas=3 -n rag-system
```

### Database Maintenance

```bash
# ChromaDB maintenance
kubectl exec -it deployment/chromadb -n rag-system -- chroma-admin optimize

# Redis maintenance
kubectl exec -it deployment/redis -n rag-system -- redis-cli BGREWRITEAOF
```

## Contact Information

- **On-call Engineer**: oncall@company.com
- **DevOps Team**: devops@company.com
- **Application Team**: rag-team@company.com
- **Emergency Escalation**: +1-555-EMERGENCY

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial deployment runbook | DevOps Team |