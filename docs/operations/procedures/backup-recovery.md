# Backup and Recovery Procedures

## Overview
This document outlines comprehensive backup and recovery procedures for the RAG System, ensuring data protection and business continuity.

## Backup Strategy

### Backup Components
1. **ChromaDB Data** - Vector embeddings and document metadata
2. **Redis Data** - Cache and session data
3. **Document Files** - Original uploaded documents
4. **Configuration** - Environment settings and secrets
5. **Application State** - Processing queues and system state

### Backup Schedule
- **Full Backup**: Daily at 2 AM UTC
- **Incremental Backup**: Every 6 hours
- **Configuration Backup**: After each deployment
- **Retention**: 30 days local, 90 days cloud storage

## Backup Procedures

### Automated Daily Backup

The system includes automated backup scripts that run via cron:

```bash
# Cron schedule (runs daily at 2 AM)
0 2 * * * /app/backup-scripts/backup.sh

# Manual backup execution
./backup-scripts/backup.sh
```

### Manual Backup Process

#### 1. Prepare Backup Environment
```bash
# Create backup directory
mkdir -p /backup/manual/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/manual/$(date +%Y%m%d_%H%M%S)"

# Stop application services (optional for hot backup)
docker-compose -f docker-compose.production.yml stop rag-backend reflex-app
```

#### 2. Backup Database Components

**ChromaDB Backup**
```bash
# Create ChromaDB backup
docker exec rag-chromadb-prod tar -czf - /chroma/chroma > "${BACKUP_DIR}/chromadb.tar.gz"

# Verify backup
tar -tzf "${BACKUP_DIR}/chromadb.tar.gz" | head -10
```

**Redis Backup**
```bash
# Force Redis to save current state
docker exec rag-redis-prod redis-cli -a ${REDIS_PASSWORD} BGSAVE

# Wait for background save to complete
while [ $(docker exec rag-redis-prod redis-cli -a ${REDIS_PASSWORD} LASTSAVE) = $(docker exec rag-redis-prod redis-cli -a ${REDIS_PASSWORD} LASTSAVE) ]; do
    sleep 1
done

# Backup Redis data
docker exec rag-redis-prod tar -czf - /data > "${BACKUP_DIR}/redis.tar.gz"
```

#### 3. Backup Document Storage
```bash
# Backup uploaded documents
tar -czf "${BACKUP_DIR}/documents.tar.gz" data/documents/

# Backup processing state
tar -czf "${BACKUP_DIR}/state.tar.gz" data/processing/
```

#### 4. Backup Configuration
```bash
# Backup environment configuration
cp .env "${BACKUP_DIR}/.env.backup"

# Backup Docker Compose configurations
tar -czf "${BACKUP_DIR}/config.tar.gz" docker-compose*.yml monitoring/

# Backup Kubernetes configurations (if applicable)
tar -czf "${BACKUP_DIR}/k8s.tar.gz" k8s/
```

#### 5. Create Backup Metadata
```bash
# Create backup manifest
cat > "${BACKUP_DIR}/manifest.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "1.0",
  "components": {
    "chromadb": "$([ -f "${BACKUP_DIR}/chromadb.tar.gz" ] && echo true || echo false)",
    "redis": "$([ -f "${BACKUP_DIR}/redis.tar.gz" ] && echo true || echo false)",
    "documents": "$([ -f "${BACKUP_DIR}/documents.tar.gz" ] && echo true || echo false)",
    "config": "$([ -f "${BACKUP_DIR}/config.tar.gz" ] && echo true || echo false)"
  },
  "size_bytes": $(du -sb "${BACKUP_DIR}" | cut -f1),
  "files": $(find "${BACKUP_DIR}" -type f | wc -l)
}
EOF
```

### Cloud Backup (S3)

#### Setup AWS CLI
```bash
# Configure AWS credentials
aws configure
# OR use environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

#### Upload to S3
```bash
# Sync backup to S3
aws s3 sync /backup/output/ s3://rag-system-backups/daily/ \
    --exclude "*" --include "rag-system-backup-*.tar.gz" \
    --storage-class STANDARD_IA

# Verify upload
aws s3 ls s3://rag-system-backups/daily/ --recursive
```

#### S3 Lifecycle Policy
```json
{
    "Rules": [
        {
            "ID": "RAGBackupLifecycle",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                },
                {
                    "Days": 90,
                    "StorageClass": "DEEP_ARCHIVE"
                }
            ],
            "Expiration": {
                "Days": 2555
            }
        }
    ]
}
```

## Recovery Procedures

### Pre-Recovery Assessment

#### 1. Assess Damage Scope
```bash
# Check what's affected
./scripts/health-check.sh

# Identify recovery requirements
echo "Data corruption assessment:"
echo "- ChromaDB accessible: $(curl -f http://localhost:8002/api/v1/heartbeat && echo YES || echo NO)"
echo "- Redis accessible: $(redis-cli -h localhost -p 6379 -a ${REDIS_PASSWORD} ping && echo YES || echo NO)"
echo "- Documents readable: $([ -r data/documents ] && echo YES || echo NO)"
```

#### 2. Choose Recovery Strategy

**Partial Recovery** - Single component failure
```bash
# Restore only affected component
./backup-scripts/restore.sh latest --component chromadb
./backup-scripts/restore.sh latest --component redis
./backup-scripts/restore.sh latest --component documents
```

**Full System Recovery** - Complete system failure
```bash
# Full system restore
./backup-scripts/restore.sh latest
```

### Recovery Execution

#### 1. Stop All Services
```bash
# Docker Compose
docker-compose -f docker-compose.production.yml down

# Kubernetes
kubectl scale deployment --all --replicas=0 -n rag-system
```

#### 2. Restore Data Components

**ChromaDB Recovery**
```bash
# Remove corrupted data
rm -rf data/chroma/*

# Extract backup
tar -xzf /backup/output/rag-system-backup-latest.tar.gz
cd rag-system-backup-*/
tar -xzf chromadb.tar.gz -C /

# Set permissions
chown -R 1000:1000 data/chroma/
```

**Redis Recovery**
```bash
# Stop Redis if running
docker stop rag-redis-prod

# Remove corrupted data
rm -rf data/redis/*

# Extract backup
tar -xzf redis.tar.gz -C /

# Set permissions
chown -R 999:999 data/redis/
```

**Document Recovery**
```bash
# Backup current documents (if partially corrupted)
mv data/documents data/documents.corrupted.$(date +%Y%m%d)

# Extract backup
tar -xzf documents.tar.gz

# Set permissions
chown -R 1000:1000 data/documents/
```

#### 3. Restore Configuration
```bash
# Restore environment file
cp .env.backup .env

# Restore Docker Compose configs
tar -xzf config.tar.gz

# Restore Kubernetes configs (if applicable)
tar -xzf k8s.tar.gz
```

#### 4. Start Services
```bash
# Start database services first
docker-compose -f docker-compose.production.yml up -d chromadb redis

# Wait for databases to be ready
sleep 30

# Start application services
docker-compose -f docker-compose.production.yml up -d rag-backend reflex-app nginx

# For Kubernetes
kubectl scale deployment chromadb --replicas=1 -n rag-system
kubectl scale deployment redis --replicas=1 -n rag-system
# Wait for database pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=chromadb -n rag-system --timeout=300s
kubectl scale deployment --all --replicas=2 -n rag-system
```

#### 5. Verify Recovery
```bash
# System health check
./scripts/health-check.sh

# Data integrity verification
curl http://localhost:8000/api/v1/documents/stats
curl http://localhost:8000/health

# Functional testing
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What documents are available?"}' \
  http://localhost:8000/query
```

### Point-in-Time Recovery

#### 1. List Available Backups
```bash
# Local backups
ls -la /backup/output/rag-system-backup-*.tar.gz

# S3 backups
aws s3 ls s3://rag-system-backups/daily/ --recursive --human-readable
```

#### 2. Restore Specific Backup
```bash
# Download specific backup from S3
aws s3 cp s3://rag-system-backups/daily/rag-system-backup-20240115_020000.tar.gz /backup/

# Restore specific backup
./backup-scripts/restore.sh rag-system-backup-20240115_020000
```

## Disaster Recovery

### Multi-Region Backup

#### Setup Cross-Region Replication
```bash
# Enable S3 cross-region replication
aws s3api put-bucket-replication \
  --bucket rag-system-backups \
  --replication-configuration file://replication-config.json
```

#### Disaster Recovery Site Setup
```bash
# Sync backups to DR site
aws s3 sync s3://rag-system-backups-primary/ s3://rag-system-backups-dr/

# Deploy infrastructure at DR site
kubectl apply -k k8s/overlays/disaster-recovery/
```

### RTO/RPO Targets

- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 4 hours
- **Maximum Tolerable Downtime**: 2 hours

### Disaster Recovery Testing

#### Monthly DR Test
```bash
#!/bin/bash
# DR test script - run monthly

# 1. Create test environment
kubectl create namespace rag-system-dr-test

# 2. Restore from backup in test environment
./backup-scripts/restore.sh latest --namespace rag-system-dr-test

# 3. Verify functionality
./scripts/functional-test.sh --namespace rag-system-dr-test

# 4. Document results
echo "DR Test Results: $(date)" >> dr-test-results.log

# 5. Cleanup
kubectl delete namespace rag-system-dr-test
```

## Monitoring and Alerting

### Backup Monitoring
```bash
# Check backup job status
systemctl status rag-backup.timer

# Monitor backup size trends
du -sh /backup/output/rag-system-backup-*.tar.gz | tail -7
```

### Backup Alerts
- Backup job failure
- Backup size deviation >20%
- Backup age >25 hours
- S3 upload failures
- Disk space <10% on backup volume

### Grafana Dashboard Metrics
- Backup job duration
- Backup file sizes
- Backup success rate
- Recovery test results
- Storage utilization

## Security Considerations

### Backup Encryption
```bash
# Encrypt backups before S3 upload
gpg --symmetric --cipher-algo AES256 backup.tar.gz

# Decrypt for recovery
gpg --decrypt backup.tar.gz.gpg > backup.tar.gz
```

### Access Controls
- Backup directories: 750 permissions
- Backup files: 640 permissions
- S3 bucket: Private with IAM restrictions
- Recovery scripts: Executable by ops team only

### Audit Trail
```bash
# Log all backup/recovery operations
logger -t rag-backup "Backup started by ${USER}"
logger -t rag-recovery "Recovery initiated: ${BACKUP_FILE}"
```

## Troubleshooting

### Common Backup Issues

**Disk Space Issues**
```bash
# Check available space
df -h /backup

# Clean old backups
find /backup -name "rag-system-backup-*.tar.gz" -mtime +30 -delete
```

**Permission Issues**
```bash
# Fix backup directory permissions
chown -R backup:backup /backup/output
chmod -R 755 /backup/output
```

**S3 Upload Failures**
```bash
# Test S3 connectivity
aws s3 ls s3://rag-system-backups/

# Retry failed uploads
aws s3 sync /backup/output/ s3://rag-system-backups/daily/ --only-show-errors
```

### Recovery Validation Checklist

- [ ] All services started successfully
- [ ] Health checks passing
- [ ] Document count matches expected
- [ ] Query functionality working
- [ ] User authentication working
- [ ] Monitoring data available
- [ ] No error logs present
- [ ] Performance within normal range

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial backup/recovery procedures | DevOps Team |