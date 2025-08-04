#!/bin/bash

# RAG System Restore Script
# Restores system from backup archives

set -euo pipefail

# Configuration
BACKUP_DIR="/backup/output"
RESTORE_TARGET="${1:-latest}"

# Logging
LOG_FILE="/var/log/restore.log"
exec 1> >(tee -a "${LOG_FILE}")
exec 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

usage() {
    echo "Usage: $0 [backup-name|latest]"
    echo ""
    echo "Examples:"
    echo "  $0 latest                           # Restore from latest backup"
    echo "  $0 rag-system-backup-20240101_1200 # Restore from specific backup"
    echo ""
    echo "Available backups:"
    find "${BACKUP_DIR}" -name "rag-system-backup-*.tar.gz" -printf "  %f\n" | sort -r | head -10
    exit 1
}

# Determine backup file to restore
if [ "${RESTORE_TARGET}" = "latest" ]; then
    BACKUP_FILE=$(find "${BACKUP_DIR}" -name "rag-system-backup-*.tar.gz" -printf "%T@ %f\n" | sort -nr | head -1 | cut -d' ' -f2)
    if [ -z "${BACKUP_FILE}" ]; then
        log "ERROR: No backup files found in ${BACKUP_DIR}"
        exit 1
    fi
else
    BACKUP_FILE="${RESTORE_TARGET}"
    if [[ ! "${BACKUP_FILE}" == *.tar.gz ]]; then
        BACKUP_FILE="${BACKUP_FILE}.tar.gz"
    fi
fi

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Verify backup file exists
if [ ! -f "${BACKUP_PATH}" ]; then
    log "ERROR: Backup file not found: ${BACKUP_PATH}"
    usage
fi

log "Starting restore from backup: ${BACKUP_FILE}"

# Verify backup integrity
log "Verifying backup integrity..."
if ! tar -tzf "${BACKUP_PATH}" >/dev/null 2>&1; then
    log "ERROR: Backup file is corrupted or invalid"
    exit 1
fi
log "Backup integrity check passed"

# Create temporary restore directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Extract backup
log "Extracting backup..."
cd "${TEMP_DIR}"
tar -xzf "${BACKUP_PATH}"

# Find the backup directory
BACKUP_EXTRACT_DIR=$(find . -name "rag-system-backup-*" -type d | head -1)
if [ -z "${BACKUP_EXTRACT_DIR}" ]; then
    log "ERROR: Could not find extracted backup directory"
    exit 1
fi

cd "${BACKUP_EXTRACT_DIR}"

# Display backup metadata
if [ -f "metadata.json" ]; then
    log "Backup metadata:"
    cat metadata.json | jq '.' 2>/dev/null || cat metadata.json
fi

# Confirmation prompt
read -p "Are you sure you want to restore from this backup? This will overwrite existing data. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Restore cancelled by user"
    exit 0
fi

# Stop services before restore
log "Stopping services..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f /app/docker-compose.production.yml down
elif command -v docker >/dev/null 2>&1; then
    docker stop rag-backend-prod rag-reflex-prod rag-chromadb-prod rag-redis-prod 2>/dev/null || true
fi

# Restore ChromaDB data
if [ -f "chromadb.tar.gz" ]; then
    log "Restoring ChromaDB data..."
    rm -rf /backup/chromadb/* 2>/dev/null || true
    tar -xzf chromadb.tar.gz -C /backup/
    log "ChromaDB data restored"
else
    log "WARNING: ChromaDB backup not found in archive"
fi

# Restore Redis data  
if [ -f "redis.tar.gz" ]; then
    log "Restoring Redis data..."
    rm -rf /backup/redis/* 2>/dev/null || true
    tar -xzf redis.tar.gz -C /backup/
    log "Redis data restored"
else
    log "WARNING: Redis backup not found in archive"
fi

# Restore document files
if [ -f "documents.tar.gz" ]; then
    log "Restoring document files..."
    rm -rf /backup/documents/* 2>/dev/null || true
    tar -xzf documents.tar.gz -C /backup/
    log "Document files restored"
else
    log "WARNING: Documents backup not found in archive"
fi

# Set proper permissions
log "Setting file permissions..."
chown -R 1000:1000 /backup/chromadb /backup/redis /backup/documents 2>/dev/null || true
chmod -R 755 /backup/chromadb /backup/redis /backup/documents 2>/dev/null || true

# Start services
log "Starting services..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f /app/docker-compose.production.yml up -d
elif command -v docker >/dev/null 2>&1; then
    docker start rag-chromadb-prod rag-redis-prod rag-backend-prod rag-reflex-prod 2>/dev/null || true
fi

# Wait for services to start
log "Waiting for services to start..."
sleep 30

# Health check
log "Performing health check..."
HEALTH_OK=true

# Check RAG backend
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
    log "WARNING: RAG backend health check failed"
    HEALTH_OK=false
fi

# Check Reflex frontend
if ! curl -f http://localhost:3000/_health >/dev/null 2>&1; then
    log "WARNING: Reflex frontend health check failed"
    HEALTH_OK=false
fi

# Check ChromaDB
if ! curl -f http://localhost:8002/api/v1/heartbeat >/dev/null 2>&1; then
    log "WARNING: ChromaDB health check failed"
    HEALTH_OK=false
fi

if [ "$HEALTH_OK" = true ]; then
    log "Health checks passed - restore completed successfully"
else
    log "WARNING: Some health checks failed - please verify system status"
fi

# Send completion notification
if [ -n "${ALERT_EMAIL_TO:-}" ]; then
    SUBJECT="RAG System Restore Completed - $(date)"
    BODY="System restore from backup ${BACKUP_FILE} completed.
Health Status: $([ "$HEALTH_OK" = true ] && echo "OK" || echo "WARNING - Check logs")
Restore Time: $(date)
Components Restored:
- ChromaDB: $([ -f "chromadb.tar.gz" ] && echo "Yes" || echo "No")
- Redis: $([ -f "redis.tar.gz" ] && echo "Yes" || echo "No")  
- Documents: $([ -f "documents.tar.gz" ] && echo "Yes" || echo "No")"
    
    if command -v mail >/dev/null 2>&1; then
        echo "${BODY}" | mail -s "${SUBJECT}" "${ALERT_EMAIL_TO}"
        log "Notification email sent to ${ALERT_EMAIL_TO}"
    fi
fi

log "Restore completed from backup: ${BACKUP_FILE}"
log "Please verify system functionality and data integrity"