# RAG System Production Infrastructure

## Overview

This document provides an overview of the production-ready infrastructure implementation for the RAG System, including deployment, monitoring, security, and operational procedures.

## Architecture Components

### Core Services
- **Reflex Frontend** (Port 3000): React-based UI with real-time updates
- **RAG Backend** (Port 8000): FastAPI service with document processing
- **ChromaDB** (Port 8002): Vector database for embeddings
- **Redis** (Port 6379): Caching and session storage
- **Nginx** (Ports 80/443): Reverse proxy with SSL termination

### Monitoring Stack
- **Prometheus** (Port 9090): Metrics collection and alerting
- **Grafana** (Port 3001): Visualization dashboards
- **AlertManager** (Port 9093): Alert notification management
- **Loki** (Port 3100): Log aggregation
- **Jaeger** (Port 16686): Distributed tracing

## Infrastructure Features

### ✅ Production-Ready Components

#### Security
- **Environment-based secrets management** with separate dev/staging/prod configs
- **SSL/TLS termination** with automated certificate management
- **Network policies** for service isolation in Kubernetes
- **Container security** with non-root users and capability restrictions
- **Rate limiting** and request validation
- **Authentication tokens** for inter-service communication

#### Monitoring & Observability
- **Comprehensive metrics** collection from all services
- **Pre-built Grafana dashboards** for system overview
- **Intelligent alerting rules** with escalation procedures
- **Centralized logging** with structured log analysis
- **Health checks** for all services with proper timeouts
- **Performance monitoring** with response time tracking

#### High Availability
- **Horizontal pod autoscaling** based on CPU/memory metrics
- **Pod disruption budgets** to ensure service availability during updates
- **Rolling deployments** with zero-downtime updates
- **Multi-replica deployments** for critical services
- **Load balancing** with health-aware routing

#### Backup & Recovery
- **Automated daily backups** of all persistent data
- **Point-in-time recovery** capabilities
- **Cross-region backup replication** for disaster recovery
- **Backup integrity verification** and testing procedures
- **Recovery time objective (RTO)**: 1 hour
- **Recovery point objective (RPO)**: 4 hours

#### Performance & Scaling
- **Resource quotas** and limits for predictable performance
- **Auto-scaling policies** that respond to actual load patterns
- **Caching strategies** at multiple layers (Redis, CDN, application)
- **Database optimization** with connection pooling
- **Performance budgets**: <500ms P95 response times

## Deployment Options

### 1. Docker Compose (Development/Small Production)

```bash
# Quick deployment
./scripts/deploy-production.sh docker-compose production

# With monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
docker-compose -f docker-compose.production.yml up -d
```

**Use Cases:**
- Development environments
- Small production deployments (<1000 users)
- Quick prototyping and testing

### 2. Kubernetes (Enterprise Production)

```bash
# Production deployment
./scripts/deploy-production.sh kubernetes production

# Manual deployment
kubectl apply -k k8s/overlays/production/
```

**Use Cases:**
- Large-scale production deployments
- Multi-environment management
- Enterprise compliance requirements
- High availability requirements

## Quick Start Guide

### Prerequisites
1. **System Requirements**: 16GB RAM, 8 CPU cores, 500GB SSD
2. **Software**: Docker 24.0+, kubectl (for K8s)
3. **External Services**: Ollama running on port 11434
4. **SSL Certificates**: For HTTPS in production

### Deployment Steps

1. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd rag-example
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Generate Secrets**
   ```bash
   # Generate secure random keys
   export SECRET_KEY=$(openssl rand -hex 32)
   export API_SECRET_KEY=$(openssl rand -hex 32)
   export JWT_SECRET=$(openssl rand -hex 64)
   export REDIS_PASSWORD=$(openssl rand -hex 16)
   ```

3. **Deploy Infrastructure**
   ```bash
   # For Docker Compose
   ./scripts/deploy-production.sh docker-compose production
   
   # For Kubernetes
   ./scripts/deploy-production.sh kubernetes production
   ```

4. **Verify Deployment**
   ```bash
   # Check service health
   curl http://localhost:8000/health
   curl http://localhost:3000/_health
   
   # Access monitoring
   open http://localhost:3001  # Grafana
   ```

## Monitoring & Alerting

### Grafana Dashboards
- **RAG System Overview**: Service health, performance metrics, resource usage
- **Infrastructure Monitoring**: System resources, container metrics
- **Application Performance**: Query response times, document processing rates

### Alert Rules
- **Critical**: Service down, high error rate (>5%), SSL certificate expiry
- **Warning**: High latency (>2s), resource usage (>80%), backup failures
- **Info**: Scaling events, deployment completions

### Access Monitoring
- **Grafana**: http://localhost:3001 (admin/password from .env)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## Security Configuration

### Environment Variables
```bash
# Required security settings
SECRET_KEY=<64-character-random-string>
API_SECRET_KEY=<64-character-random-string>
JWT_SECRET=<64-character-random-string>
REDIS_PASSWORD=<secure-password>

# SSL/TLS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/rag-system.crt
SSL_KEY_PATH=/etc/ssl/rag-system.key

# CORS policy
CORS_ORIGINS=https://yourdomain.com
```

### Network Security
- **Firewall rules**: Only necessary ports exposed
- **Service mesh**: mTLS between services (Kubernetes)
- **Network policies**: Traffic restrictions between pods
- **Rate limiting**: API endpoint protection

## Backup Strategy

### Automated Backups
- **Schedule**: Daily at 2 AM UTC
- **Components**: ChromaDB, Redis, documents, configuration
- **Retention**: 30 days local, 90 days cloud
- **Verification**: Automated integrity checks

### Manual Backup
```bash
# Create immediate backup
./backup-scripts/backup.sh

# Restore from backup
./backup-scripts/restore.sh latest
```

## Performance Targets

### Service Level Objectives (SLOs)
- **Availability**: 99.9% uptime (8.7 hours downtime/year max)
- **Response Time**: <500ms P95 for API calls
- **Throughput**: 500+ queries/minute sustained
- **Error Rate**: <0.1% for critical operations

### Resource Allocation
- **RAG Backend**: 2-8GB RAM, 1-4 CPU cores (auto-scaling)
- **ChromaDB**: 1-4GB RAM, 0.5-2 CPU cores
- **Redis**: 256MB-2GB RAM, 0.1-1 CPU cores
- **Frontend**: 512MB-2GB RAM, 0.3-1 CPU cores

## Troubleshooting

### Common Issues
1. **Service startup failures**: Check logs and environment variables
2. **Performance issues**: Monitor resource usage and scale services
3. **Database connection failures**: Verify network policies and credentials
4. **SSL certificate issues**: Check certificate validity and paths

### Debug Commands
```bash
# Check service status
docker-compose ps  # Docker Compose
kubectl get pods -n rag-system  # Kubernetes

# View logs
docker logs <container-name>
kubectl logs <pod-name> -n rag-system

# Test connectivity
curl http://localhost:8000/health
curl http://localhost:8002/api/v1/heartbeat
```

## Operational Procedures

### Deployment
- [Deployment Runbook](docs/operations/runbooks/deployment.md)
- [Troubleshooting Guide](docs/operations/troubleshooting/common-issues.md)

### Backup & Recovery
- [Backup Procedures](docs/operations/procedures/backup-recovery.md)
- [Disaster Recovery Plan](docs/operations/procedures/disaster-recovery.md)

### Monitoring
- [Monitoring Setup](docs/operations/procedures/monitoring.md)
- [Performance Tuning](docs/operations/procedures/performance-tuning.md)

## Support & Escalation

### Contact Information
- **DevOps Team**: devops@company.com
- **On-Call Engineer**: +1-555-ONCALL
- **Emergency Escalation**: +1-555-EMERGENCY

### Service Level Agreement
- **Response Time**: 30 minutes for critical issues
- **Resolution Time**: 4 hours for critical, 24 hours for high priority
- **Business Hours**: 24/7 for critical issues, business hours for others

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial production infrastructure | DevOps Team |

---

## Next Steps

1. **Review Configuration**: Update .env file with production values
2. **Deploy Infrastructure**: Choose deployment method and execute
3. **Configure Monitoring**: Set up alerts and dashboards
4. **Test Procedures**: Validate backup/recovery processes
5. **Security Review**: Complete security assessment
6. **Performance Testing**: Conduct load testing
7. **Documentation**: Update operational procedures
8. **Training**: Train operations team on procedures

For detailed procedures and troubleshooting, see the [operations documentation](docs/operations/).