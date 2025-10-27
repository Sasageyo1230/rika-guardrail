#!/bin/bash
# ===========================================
# Rika Core Backup Script
# ===========================================
# This script backs up all critical data to both MinIO and local storage
# Run manually or via cron/scheduled task

set -e

# Configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="rika-backup-${BACKUP_DATE}"
LOCAL_BACKUP_DIR="/backups"
MINIO_BUCKET="rika-backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ===========================================
# Backup Functions
# ===========================================

backup_postgres() {
    log "Backing up PostgreSQL databases..."
    
    # Dump all databases
    docker exec rika-postgres pg_dumpall -U ${POSTGRES_USER:-rika_admin} > "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql"
    
    # Compress the dump
    gzip "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql"
    
    # Upload to MinIO
    mc cp "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql.gz" "minio/${MINIO_BUCKET}/postgres/"
    
    log "PostgreSQL backup completed"
}

backup_qdrant() {
    log "Backing up Qdrant vector database..."
    
    # Create snapshot via API
    curl -X POST "http://localhost:6333/snapshots" \
         -H "Content-Type: application/json" \
         -d '{"wait": true}' > /tmp/qdrant_snapshot.json
    
    # Get snapshot name
    SNAPSHOT_NAME=$(cat /tmp/qdrant_snapshot.json | grep -o '"name":"[^"]*' | sed 's/"name":"//')
    
    if [ ! -z "$SNAPSHOT_NAME" ]; then
        # Copy snapshot to backup directory
        docker cp "rika-qdrant:/qdrant/storage/snapshots/${SNAPSHOT_NAME}" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-qdrant.snapshot"
        
        # Upload to MinIO
        mc cp "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-qdrant.snapshot" "minio/${MINIO_BUCKET}/qdrant/"
        
        log "Qdrant backup completed"
    else
        warning "Qdrant snapshot creation failed"
    fi
}

backup_volumes() {
    log "Backing up Docker volumes..."
    
    # List of volumes to backup
    VOLUMES=("n8n" "keycloak" "nats" "minio")
    
    for volume in "${VOLUMES[@]}"; do
        log "  Backing up ${volume} data..."
        
        # Create tar archive of volume data
        tar -czf "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-${volume}.tar.gz" -C /data "${volume}/" 2>/dev/null || true
        
        # Upload to MinIO
        mc cp "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-${volume}.tar.gz" "minio/${MINIO_BUCKET}/volumes/" 2>/dev/null || true
    done
    
    log "Volume backups completed"
}

backup_configs() {
    log "Backing up configuration files..."
    
    # Create configs archive
    tar -czf "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-configs.tar.gz" \
        -C / \
        configs/ \
        docker-compose.yml \
        .env \
        release.lock.json 2>/dev/null || true
    
    # Upload to MinIO
    mc cp "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-configs.tar.gz" "minio/${MINIO_BUCKET}/configs/"
    
    log "Configuration backup completed"
}

cleanup_old_backups() {
    log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
    
    # Clean local backups
    find ${LOCAL_BACKUP_DIR} -name "rika-backup-*" -type f -mtime +${RETENTION_DAYS} -delete
    
    # Clean MinIO backups
    mc rm --recursive --force --older-than ${RETENTION_DAYS}d "minio/${MINIO_BUCKET}/"
    
    log "Cleanup completed"
}

create_backup_manifest() {
    log "Creating backup manifest..."
    
    cat > "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-manifest.json" <<EOF
{
    "backup_id": "${BACKUP_PREFIX}",
    "timestamp": "$(date -Iseconds)",
    "version": "$(cat /release.lock.json | grep '"version"' | head -1 | sed 's/.*: "\(.*\)".*/\1/')",
    "components": {
        "postgres": "${BACKUP_PREFIX}-postgres.sql.gz",
        "qdrant": "${BACKUP_PREFIX}-qdrant.snapshot",
        "volumes": {
            "n8n": "${BACKUP_PREFIX}-n8n.tar.gz",
            "keycloak": "${BACKUP_PREFIX}-keycloak.tar.gz",
            "nats": "${BACKUP_PREFIX}-nats.tar.gz",
            "minio": "${BACKUP_PREFIX}-minio.tar.gz"
        },
        "configs": "${BACKUP_PREFIX}-configs.tar.gz"
    },
    "status": "complete",
    "retention_days": ${RETENTION_DAYS}
}
EOF
    
    # Upload manifest to MinIO
    mc cp "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-manifest.json" "minio/${MINIO_BUCKET}/"
    
    log "Manifest created"
}

# ===========================================
# Main Execution
# ===========================================

main() {
    log "========================================="
    log "Starting Rika Core backup process"
    log "Backup ID: ${BACKUP_PREFIX}"
    log "========================================="
    
    # Ensure backup directory exists
    mkdir -p ${LOCAL_BACKUP_DIR}
    
    # Check MinIO connectivity
    if ! mc ls "minio/${MINIO_BUCKET}" >/dev/null 2>&1; then
        warning "MinIO not accessible, backing up locally only"
    fi
    
    # Perform backups
    backup_postgres
    backup_qdrant
    backup_volumes
    backup_configs
    create_backup_manifest
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Calculate backup size
    BACKUP_SIZE=$(du -sh ${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}* | awk '{sum+=$1} END {print sum}')
    
    log "========================================="
    log "Backup completed successfully!"
    log "Backup ID: ${BACKUP_PREFIX}"
    log "Location: ${LOCAL_BACKUP_DIR}"
    log "MinIO Bucket: ${MINIO_BUCKET}"
    log "Total Size: ~${BACKUP_SIZE}MB"
    log "========================================="
}

# Handle errors
trap 'error "Backup failed at line $LINENO"' ERR

# Run main function
main "$@"