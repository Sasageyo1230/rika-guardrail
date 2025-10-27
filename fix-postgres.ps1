Write-Host "=== Fixing PostgreSQL Setup ===" -ForegroundColor Green

# Stop and remove PostgreSQL container
Write-Host "Stopping PostgreSQL..." -ForegroundColor Yellow
docker-compose stop postgres
docker-compose rm -f postgres

# Remove old PostgreSQL data
Write-Host "Removing old PostgreSQL 16 data..." -ForegroundColor Yellow
if (Test-Path ".\data\postgres") {
    Remove-Item -Path ".\data\postgres" -Recurse -Force
    Write-Host "Old data removed" -ForegroundColor Green
}

# Temporarily disable init script
Write-Host "Disabling init script temporarily..." -ForegroundColor Yellow
if (Test-Path ".\scripts\init\init-postgres.sql") {
    Rename-Item ".\scripts\init\init-postgres.sql" "init-postgres.sql.disabled"
}

# Comment out the init script line in docker-compose
Write-Host "Updating docker-compose.yml..." -ForegroundColor Yellow
$compose = Get-Content ".\docker-compose.yml"
$compose = $compose -replace '- ./scripts/init/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql:ro', '#- ./scripts/init/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql:ro'
$compose | Set-Content ".\docker-compose.yml"

# Start fresh PostgreSQL
Write-Host "Starting fresh PostgreSQL 17..." -ForegroundColor Yellow
docker-compose up -d postgres

# Wait for initialization
Write-Host "Waiting for PostgreSQL to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check status
Write-Host "`nChecking PostgreSQL status..." -ForegroundColor Yellow
docker-compose ps postgres

# Test connection
Write-Host "`nTesting connection..." -ForegroundColor Yellow
docker exec -it rika-postgres psql -U rika_admin -d rika_core -c "SELECT version();"

# Create databases manually
Write-Host "`nCreating additional databases..." -ForegroundColor Yellow
docker exec -it rika-postgres psql -U rika_admin -d postgres -c "CREATE DATABASE n8n_db OWNER rika_admin;"
docker exec -it rika-postgres psql -U rika_admin -d postgres -c "CREATE DATABASE keycloak_db OWNER rika_admin;"

# Start pgAdmin
Write-Host "`nStarting pgAdmin..." -ForegroundColor Yellow
docker-compose up -d pgadmin

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "PostgreSQL 17 is running on port 5433" -ForegroundColor Cyan
Write-Host "pgAdmin is available at http://localhost:5050" -ForegroundColor Cyan
Write-Host "`nConnection details for n8n:" -ForegroundColor Cyan
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5433" -ForegroundColor White
Write-Host "  Database: rika_core" -ForegroundColor White
Write-Host "  User: rika_admin" -ForegroundColor White
Write-Host "  Password: RikaPostgres2025SecureDB" -ForegroundColor White