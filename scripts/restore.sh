#!/bin/bash
# ===========================================
# Rika Core Restore Script
# ===========================================
# Restores data from backup created by backup.sh

set -e

# Configuration
LOCAL_BACKUP_DIR="/backups"
MINIO_BUCKET="rika-backups"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ===========================================
# Restore Functions
# ===========================================

list_backups() {
    log "Available backups:"
    echo "-------------------"
    
    # List local backups
    if [ -d "${LOCAL_BACKUP_DIR}" ]; then
        echo "Local backups:"
        ls -la ${LOCAL_BACKUP_DIR}/*-manifest.json 2>/dev/null | awk '{print $9}' | sed 's/.*rika-backup-/  - /' | sed 's/-manifest.json//'
    fi
    
    # List MinIO backups
    echo ""
    echo "MinIO backups:"
    mc ls "minio/${MINIO_BUCKET}/" | grep manifest.json | awk '{print $5}' | sed 's/rika-backup-/  - /' | sed 's/-manifest.json//'
}

restore_postgres() {
    local backup_file=$1
    log "Restoring PostgreSQL from ${backup_file}..."
    
    # Stop dependent services
    docker-compose stop n8n keycloak
    
    # Decompress if needed
    if [[ $backup_file == *.gz ]]; then
        gunzip -c "$backup_file" > /tmp/postgres_restore.sql
        backup_file="/tmp/postgres_restore.sql"
    fi
    
    # Restore database
    docker exec -i rika-postgres psql -U ${POSTGRES_USER:-rika_admin} < "$backup_file"
    
    # Restart dependent services
    docker-compose start n8n keycloak
    
    log "PostgreSQL restore completed"
}

restore_qdrant() {
    local backup_file=$1
    log "Restoring Qdrant from ${backup_file}..."
    
    # Stop Qdrant
    docker-compose stop qdrant
    
    # Clear existing data
    rm -rf /data/qdrant/*
    
    # Copy snapshot to container
    docker cp "$backup_file" rika-qdrant:/qdrant/storage/snapshots/
    
    # Start Qdrant
    docker-compose start qdrant
    
    # Trigger restore via API
    SNAPSHOT_NAME=$(basename "$backup_file")
    curl -X PUT "http://localhost:6333/collections/restore" \
         -H "Content-Type: application/json" \
         -d "{\"location\": \"/qdrant/storage/snapshots/${SNAPSHOT_NAME}\"}"
    
    log "Qdrant restore completed"
}

restore_volume() {
    local volume_name=$1
    local backup_file=$2
    
    log "Restoring ${volume_name} from ${backup_file}..."
    
    # Stop the related service
    docker-compose stop ${volume_name}
    
    # Extract backup
    tar -xzf "$backup_file" -C /data/
    
    # Start the service
    docker-compose start ${volume_name}
    
    log "${volume_name} restore completed"
}

restore_configs() {
    local backup_file=$1
    log "Restoring configurations from ${backup_file}..."
    
    # Create backup of current configs
    tar -czf "${LOCAL_BACKUP_DIR}/configs-before-restore-$(date +%Y%m%d_%H%M%S).tar.gz" \
        configs/ docker-compose.yml .env release.lock.json 2>/dev/null || true
    
    # Extract new configs
    tar -xzf "$backup_file" -C /
    
    log "Configuration restore completed"
}

download_from_minio() {
    local backup_id=$1
    log "Downloading backup ${backup_id} from MinIO..."
    
    mkdir -p "${LOCAL_BACKUP_DIR}/restore-${backup_id}"
    mc cp --recursive "minio/${MINIO_BUCKET}/${backup_id}*" "${LOCAL_BACKUP_DIR}/restore-${backup_id}/"
    
    log "Download completed"
}

# ===========================================
# Interactive Restore
# ===========================================

interactive_restore() {
    echo "========================================="
    echo "     Rika Core Interactive Restore"
    echo "========================================="
    
    # List available backups
    list_backups
    
    echo ""
    read -p "Enter backup ID to restore (e.g., 20250108_120000): " BACKUP_ID
    
    if [ -z "$BACKUP_ID" ]; then
        error "No backup ID provided"
    fi
    
    BACKUP_PREFIX="rika-backup-${BACKUP_ID}"
    
    # Check if backup exists locally
    if [ ! -f "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-manifest.json" ]; then
        info "Backup not found locally, checking MinIO..."
        download_from_minio "${BACKUP_PREFIX}"
        LOCAL_BACKUP_DIR="${LOCAL_BACKUP_DIR}/restore-${BACKUP_PREFIX}"
    fi
    
    # Read manifest
    if [ ! -f "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-manifest.json" ]; then
        error "Backup manifest not found"
    fi
    
    log "Found backup: ${BACKUP_PREFIX}"
    cat "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-manifest.json" | python -m json.tool
    
    echo ""
    echo "Select components to restore:"
    echo "  1) All components"
    echo "  2) PostgreSQL only"
    echo "  3) Qdrant only"
    echo "  4) Volumes only"
    echo "  5) Configurations only"
    echo "  6) Custom selection"
    echo ""
    read -p "Enter your choice (1-6): " CHOICE
    
    case $CHOICE in
        1)
            restore_all
            ;;
        2)
            restore_postgres "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql.gz"
            ;;
        3)
            restore_qdrant "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-qdrant.snapshot"
            ;;
        4)
            restore_all_volumes
            ;;
        5)
            restore_configs "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-configs.tar.gz"
            ;;
        6)
            custom_restore
            ;;
        *)
            error "Invalid choice"
            ;;
    esac
}

restore_all() {
    log "Starting full restore..."
    
    warning "This will overwrite ALL existing data. Continue? (yes/no)"
    read -p "> " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
    
    # Stop all services
    log "Stopping all services..."
    docker-compose down
    
    # Restore components
    restore_configs "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-configs.tar.gz"
    
    # Start core services
    docker-compose up -d postgres minio
    sleep 10
    
    restore_postgres "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql.gz"
    restore_qdrant "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-qdrant.snapshot"
    
    # Restore volumes
    restore_all_volumes
    
    # Start all services
    log "Starting all services..."
    docker-compose up -d
    
    log "Full restore completed!"
}

restore_all_volumes() {
    VOLUMES=("n8n" "keycloak" "nats" "minio")
    
    for volume in "${VOLUMES[@]}"; do
        if [ -f "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-${volume}.tar.gz" ]; then
            restore_volume "$volume" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-${volume}.tar.gz"
        else
            warning "Backup for ${volume} not found, skipping..."
        fi
    done
}

custom_restore() {
    log "Custom restore - select components:"
    
    echo "PostgreSQL? (y/n)"
    read -p "> " RESTORE_PG
    
    echo "Qdrant? (y/n)"
    read -p "> " RESTORE_QDRANT
    
    echo "n8n? (y/n)"
    read -p "> " RESTORE_N8N
    
    echo "Keycloak? (y/n)"
    read -p "> " RESTORE_KEYCLOAK
    
    echo "NATS? (y/n)"
    read -p "> " RESTORE_NATS
    
    echo "MinIO data? (y/n)"
    read -p "> " RESTORE_MINIO
    
    echo "Configurations? (y/n)"
    read -p "> " RESTORE_CONFIGS
    
    # Perform selected restores
    [[ "$RESTORE_PG" == "y" ]] && restore_postgres "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-postgres.sql.gz"
    [[ "$RESTORE_QDRANT" == "y" ]] && restore_qdrant "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-qdrant.snapshot"
    [[ "$RESTORE_N8N" == "y" ]] && restore_volume "n8n" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-n8n.tar.gz"
    [[ "$RESTORE_KEYCLOAK" == "y" ]] && restore_volume "keycloak" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-keycloak.tar.gz"
    [[ "$RESTORE_NATS" == "y" ]] && restore_volume "nats" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-nats.tar.gz"
    [[ "$RESTORE_MINIO" == "y" ]] && restore_volume "minio" "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-minio.tar.gz"
    [[ "$RESTORE_CONFIGS" == "y" ]] && restore_configs "${LOCAL_BACKUP_DIR}/${BACKUP_PREFIX}-configs.tar.gz"
    
    log "Custom restore completed!"
}

# ===========================================
# Main Execution
# ===========================================

main() {
    # Check if running inside container or host
    if [ -f /.dockerenv ]; then
        error "This script should be run from the host, not inside a container"
    fi
    
    # Check for required tools
    command -v docker >/dev/null 2>&1 || error "Docker is not installed"
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed"
    
    # Parse arguments
    if [ "$1" == "--list" ]; then
        list_backups
        exit 0
    elif [ "$1" == "--help" ]; then
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --list    List available backups"
        echo "  --help    Show this help message"
        echo ""
        echo "Without options, starts interactive restore"
        exit 0
    fi
    
    # Start interactive restore
    interactive_restore
}

# Handle errors
trap 'error "Restore failed at line $LINENO"' ERR

# Run main function
main "$@"