#!/bin/bash

# RAG System Backup Script
# Performs daily backups of ChromaDB, Redis, and document data

set -euo pipefail

# Configuration
BACKUP_DIR="/backup/output"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="rag-system-backup-${TIMESTAMP}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# S3 Configuration (optional)
S3_ENABLED="${BACKUP_S3_ENABLED:-false}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"

# Logging
LOG_FILE="/var/log/backup.log"
exec 1> >(tee -a "${LOG_FILE}")
exec 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

log "Starting RAG system backup: ${BACKUP_NAME}"

# Backup ChromaDB data
log "Backing up ChromaDB data..."
if [ -d "/backup/chromadb" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/chromadb.tar.gz" -C /backup chromadb/
    log "ChromaDB backup completed: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}/chromadb.tar.gz" | cut -f1)"
else
    log "WARNING: ChromaDB data directory not found"
fi

# Backup Redis data
log "Backing up Redis data..."
if [ -d "/backup/redis" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/redis.tar.gz" -C /backup redis/
    log "Redis backup completed: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}/redis.tar.gz" | cut -f1)"
else
    log "WARNING: Redis data directory not found"
fi

# Backup document uploads
log "Backing up document files..."
if [ -d "/backup/documents" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/documents.tar.gz" -C /backup documents/
    log "Documents backup completed: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}/documents.tar.gz" | cut -f1)"
else
    log "WARNING: Documents directory not found"
fi

# Create metadata file
cat > "${BACKUP_DIR}/${BACKUP_NAME}/metadata.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "1.0",
  "system": "rag-system",
  "components": {
    "chromadb": $([ -f "${BACKUP_DIR}/${BACKUP_NAME}/chromadb.tar.gz" ] && echo "true" || echo "false"),
    "redis": $([ -f "${BACKUP_DIR}/${BACKUP_NAME}/redis.tar.gz" ] && echo "true" || echo "false"),
    "documents": $([ -f "${BACKUP_DIR}/${BACKUP_NAME}/documents.tar.gz" ] && echo "true" || echo "false")
  },
  "backup_size_bytes": $(du -sb "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1),
  "retention_days": ${RETENTION_DAYS}
}
EOF

# Create final compressed backup
log "Creating final backup archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
rm -rf "${BACKUP_NAME}/"

BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
log "Backup archive created: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"

# Upload to S3 if configured
if [ "${S3_ENABLED}" = "true" ] && [ -n "${S3_BUCKET}" ]; then
    log "Uploading backup to S3..."
    if command -v aws >/dev/null 2>&1; then
        aws s3 cp "${BACKUP_NAME}.tar.gz" "s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz"
        log "Backup uploaded to S3: s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz"
    else
        log "ERROR: AWS CLI not found, skipping S3 upload"
    fi
fi

# Cleanup old backups
log "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "rag-system-backup-*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "rag-system-backup-*.tar.gz" -type f | wc -l)
log "Cleanup completed. Remaining backups: ${REMAINING_BACKUPS}"

# Cleanup old S3 backups if configured
if [ "${S3_ENABLED}" = "true" ] && [ -n "${S3_BUCKET}" ] && command -v aws >/dev/null 2>&1; then
    log "Cleaning up old S3 backups..."
    CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%Y%m%d)
    aws s3 ls "s3://${S3_BUCKET}/" | grep "rag-system-backup-" | while read -r line; do
        BACKUP_FILE=$(echo "$line" | awk '{print $4}')
        BACKUP_DATE=$(echo "$BACKUP_FILE" | grep -oP 'rag-system-backup-\K\d{8}')
        if [ "${BACKUP_DATE}" -lt "${CUTOFF_DATE}" ]; then
            aws s3 rm "s3://${S3_BUCKET}/${BACKUP_FILE}"
            log "Deleted old S3 backup: ${BACKUP_FILE}"
        fi
    done
fi

# Health check - verify backup integrity
log "Verifying backup integrity..."
if tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" >/dev/null 2>&1; then
    log "Backup integrity check passed"
else
    log "ERROR: Backup integrity check failed!"
    exit 1
fi

# Send completion notification (if configured)
if [ -n "${ALERT_EMAIL_TO:-}" ]; then
    SUBJECT="RAG System Backup Completed - ${TIMESTAMP}"
    BODY="Backup ${BACKUP_NAME}.tar.gz completed successfully.
Size: ${BACKUP_SIZE}
Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz
S3 Upload: $([ "${S3_ENABLED}" = "true" ] && echo "Enabled" || echo "Disabled")
Retention: ${RETENTION_DAYS} days"
    
    # Simple email notification (requires mail command)
    if command -v mail >/dev/null 2>&1; then
        echo "${BODY}" | mail -s "${SUBJECT}" "${ALERT_EMAIL_TO}"
        log "Notification email sent to ${ALERT_EMAIL_TO}"
    fi
fi

log "Backup completed successfully: ${BACKUP_NAME}.tar.gz"