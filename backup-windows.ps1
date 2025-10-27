# Rika Core Backup Script for Windows
# Run this in PowerShell to backup your Docker volumes

$BackupDate = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPrefix = "rika-backup-$BackupDate"
$BackupDir = ".\backups"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     Rika Core Backup (Windows)" -ForegroundColor Cyan
Write-Host "     Backup ID: $BackupPrefix" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Host "Created backup directory" -ForegroundColor Green
}

# Function to check if service is running
function Test-Container {
    param($name)
    $result = docker ps --filter "name=$name" --format "{{.Names}}" 2>$null
    return $result -eq $name
}

Write-Host "`nChecking services..." -ForegroundColor Yellow

# Backup PostgreSQL if running
if (Test-Container "rika-postgres") {
    Write-Host "Backing up PostgreSQL..." -ForegroundColor Green
    docker exec rika-postgres pg_dumpall -U rika_admin > "$BackupDir\$BackupPrefix-postgres.sql" 2>$null
    if ($?) {
        Write-Host "  PostgreSQL backed up successfully" -ForegroundColor Green
    } else {
        Write-Host "  PostgreSQL backup failed (might not be running)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  PostgreSQL not running - skipping" -ForegroundColor Yellow
}

# Backup Qdrant if running
if (Test-Container "rika-qdrant") {
    Write-Host "Backing up Qdrant..." -ForegroundColor Green
    # Create snapshot via API
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:6333/snapshots" -Method POST -ContentType "application/json" -Body '{"wait": true}' -ErrorAction SilentlyContinue
        Write-Host "  Qdrant snapshot created" -ForegroundColor Green
    } catch {
        Write-Host "  Qdrant backup failed (might not be running)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Qdrant not running - skipping" -ForegroundColor Yellow
}

# Backup Docker volumes (simple file copy)
Write-Host "Backing up Docker volumes..." -ForegroundColor Green

$volumes = @("postgres", "qdrant", "n8n", "keycloak", "nats", "minio")
foreach ($vol in $volumes) {
    $sourcePath = ".\data\$vol"
    if (Test-Path $sourcePath) {
        Write-Host "  Backing up $vol data..." -ForegroundColor Gray
        $zipPath = "$BackupDir\$BackupPrefix-$vol.zip"
        Compress-Archive -Path $sourcePath -DestinationPath $zipPath -Force
        Write-Host "    Created $vol.zip" -ForegroundColor Green
    }
}

# Backup configuration files
Write-Host "Backing up configuration..." -ForegroundColor Green
$configFiles = @(
    "docker-compose.yml",
    ".env",
    "release.lock.json"
)

$configBackup = "$BackupDir\$BackupPrefix-configs.zip"
Compress-Archive -Path $configFiles -DestinationPath $configBackup -Force
Write-Host "  Configuration backed up" -ForegroundColor Green

# Create backup manifest
Write-Host "Creating backup manifest..." -ForegroundColor Green
$manifest = @{
    backup_id = $BackupPrefix
    timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    version = "0.1.0"
    files = Get-ChildItem "$BackupDir\$BackupPrefix-*" | Select-Object -ExpandProperty Name
    size_mb = [math]::Round((Get-ChildItem "$BackupDir\$BackupPrefix-*" | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
}

$manifest | ConvertTo-Json | Out-File "$BackupDir\$BackupPrefix-manifest.json"

# Summary
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "     Backup Completed!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Backup ID: $BackupPrefix" -ForegroundColor White
Write-Host "Location: $BackupDir" -ForegroundColor White
Write-Host "Total Size: $($manifest.size_mb) MB" -ForegroundColor White
Write-Host "Files created:" -ForegroundColor White
$manifest.files | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

# Cleanup old backups (older than 30 days)
Write-Host "`nCleaning up old backups..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-30)
Get-ChildItem "$BackupDir\rika-backup-*" | Where-Object { $_.CreationTime -lt $cutoffDate } | Remove-Item -Force
Write-Host "Cleanup complete" -ForegroundColor Green