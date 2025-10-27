# phase2.5/core/start-core.ps1
# Start Rika Core API on port 5317

Write-Host "Starting Rika Core API on port 5317..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from python.org or Microsoft Store" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if port 5317 is already in use
$portInUse = Get-NetTCPConnection -LocalPort 5317 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port 5317 is already in use!" -ForegroundColor Yellow
    $process = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Process using port: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
    }
    Write-Host "Do you want to:" -ForegroundColor Yellow
    Write-Host "  1. Kill the existing process and start Core API" -ForegroundColor White
    Write-Host "  2. Use a different port (5318)" -ForegroundColor White
    Write-Host "  3. Exit" -ForegroundColor White
    
    $choice = Read-Host "Enter choice (1-3)"
    
    switch ($choice) {
        "1" {
            Stop-Process -Id $portInUse.OwningProcess -Force
            Write-Host "Process killed. Starting Core API..." -ForegroundColor Green
        }
        "2" {
            Write-Host "Starting Core API on port 5318 instead..." -ForegroundColor Yellow
            python -m uvicorn api:app --host 0.0.0.0 --port 5318 --reload
            exit
        }
        default {
            Write-Host "Exiting..." -ForegroundColor Red
            exit
        }
    }
}

# Set environment variables
$env:DATABASE_URL = "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core"
$env:NATS_URL = "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222"

# Load .env file if it exists
if (Test-Path "../.env") {
    Write-Host "Loading environment from .env file..." -ForegroundColor Gray
    Get-Content "../.env" | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
}

Write-Host ""
Write-Host "Starting Core API with:" -ForegroundColor Cyan
Write-Host "  Host: 0.0.0.0" -ForegroundColor White
Write-Host "  Port: 5317" -ForegroundColor White
Write-Host "  Auto-reload: Enabled" -ForegroundColor White
Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Green
Write-Host "  http://localhost:5317" -ForegroundColor White
Write-Host "  http://localhost:5317/docs (Swagger UI)" -ForegroundColor White
Write-Host "  http://localhost:5317/health" -ForegroundColor White
Write-Host "  http://localhost:5317/selfcheck" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the API
python -m uvicorn api:app --host 0.0.0.0 --port 5317 --reload