# Rika Core Restore Script for Windows
# Run this in PowerShell to restore from backup

param(
    [string]$BackupId = "",
    [switch]$ListOnly
)

$BackupDir = ".\backups"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     Rika Core Restore (Windows)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# List available backups
if ($ListOnly -or [string]::IsNullOrEmpty($BackupId)) {
    Write-Host "`nAvailable backups:" -ForegroundColor Yellow
    $backups = Get-ChildItem "$BackupDir\*-manifest.json" | Sort-Object CreationTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "No backups found in $BackupDir" -ForegroundColor Red
        exit
    }
    
    foreach ($backup in $backups) {
        $manifest = Get-Content $backup.FullName | ConvertFrom-Json
        Write-Host "  - $($manifest.backup_id)" -ForegroundColor White
        Write-Host "    Date: $($manifest.timestamp)" -ForegroundColor Gray
        Write-Host "    Size: $($manifest.size_mb) MB" -ForegroundColor Gray
    }
    
    if ($ListOnly) { exit }
    
    Write-Host "`nEnter backup ID to restore (e.g., 20250108_120000): " -NoNewline -ForegroundColor Yellow
    $BackupId = Read-Host
}

if ([string]::IsNullOrEmpty($BackupId)) {
    Write-Host "No backup ID provided" -ForegroundColor Red
    exit
}

$BackupPrefix = "rika-backup-$BackupId"
$ManifestPath = "$BackupDir\$BackupPrefix-manifest.json"

# Check if backup exists
if (!(Test-Path $ManifestPath)) {
    Write-Host "Backup not found: $BackupPrefix" -ForegroundColor Red
    exit
}

$manifest = Get-Content $ManifestPath | ConvertFrom-Json
Write-Host "`nRestoring from backup: $($manifest.backup_id)" -ForegroundColor Green
Write-Host "Backup date: $($manifest.timestamp)" -ForegroundColor Gray

# Confirm restore
Write-Host "`nThis will overwrite existing data. Continue? (yes/no): " -NoNewline -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "yes") {
    Write-Host "Restore cancelled" -ForegroundColor Yellow
    exit
}

# Stop all containers
Write-Host "`nStopping all containers..." -ForegroundColor Yellow
docker-compose down

# Restore PostgreSQL
$pgBackup = "$BackupDir\$BackupPrefix-postgres.sql"
if (Test-Path $pgBackup) {
    Write-Host "Restoring PostgreSQL..." -ForegroundColor Green
    docker-compose up -d postgres
    Start-Sleep -Seconds 10
    Get-Content $pgBackup | docker exec -i rika-postgres psql -U rika_admin
    Write-Host "  PostgreSQL restored" -ForegroundColor Green
}

# Restore volume data
Write-Host "Restoring volume data..." -ForegroundColor Green
$volumes = @("postgres", "qdrant", "n8n", "keycloak", "nats", "minio")

foreach ($vol in $volumes) {
    $zipPath = "$BackupDir\$BackupPrefix-$vol.zip"
    if (Test-Path $zipPath) {
        Write-Host "  Restoring $vol..." -ForegroundColor Gray
        $dataPath = ".\data\$vol"
        
        # Backup current data
        if (Test-Path $dataPath) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            Rename-Item $dataPath "$dataPath.backup.$timestamp"
        }
        
        # Extract backup
        Expand-Archive -Path $zipPath -DestinationPath ".\data\" -Force
        Write-Host "    $vol restored" -ForegroundColor Green
    }
}

# Restore configuration
$configBackup = "$BackupDir\$BackupPrefix-configs.zip"
if (Test-Path $configBackup) {
    Write-Host "Restoring configuration..." -ForegroundColor Green
    
    # Backup current configs
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $configFiles = @("docker-compose.yml", ".env", "release.lock.json")
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Copy-Item $file "$file.backup.$timestamp"
        }
    }
    
    # Extract configs
    Expand-Archive -Path $configBackup -DestinationPath ".\" -Force
    Write-Host "  Configuration restored" -ForegroundColor Green
}

# Start all services
Write-Host "`nStarting all services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "     Restore Completed!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Restored from: $($manifest.backup_id)" -ForegroundColor White
Write-Host "`nVerify services with: docker-compose ps" -ForegroundColor Yellow