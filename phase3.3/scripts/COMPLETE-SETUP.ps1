# Rika Phase 3.3 - Complete Working Setup Script
# This installs dependencies, starts services, and validates everything works

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[RIKA] Phase 3.3 Complete Setup & Start" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Activate virtual environment if not active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
    $venvPath = Join-Path (Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent) -ChildPath ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        & $venvPath
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Virtual environment not found" -ForegroundColor Red
        exit 1
    }
}

# Install Python dependencies
Write-Host "`n[INFO] Installing Python dependencies..." -ForegroundColor Yellow
try {
    $pipOutput = python -m pip install fastapi uvicorn --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Some pip warnings, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

# Start Core API
Write-Host "`n[INFO] Starting Core API on port 5317..." -ForegroundColor Yellow
$coreDir = Join-Path (Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent) -ChildPath "core"
$apiProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5317", "--reload" -WorkingDirectory $coreDir -PassThru
Write-Host "[OK] Core API started (PID: $($apiProcess.Id))" -ForegroundColor Green

# Start Atlas UI
Write-Host "[INFO] Starting Atlas UI on port 5173..." -ForegroundColor Yellow
$uiDir = Join-Path (Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent) -ChildPath "ui"
$uiProcess = Start-Process -FilePath "python" -ArgumentList "serve.py" -WorkingDirectory $uiDir -PassThru
Write-Host "[OK] Atlas UI started (PID: $($uiProcess.Id))" -ForegroundColor Green

# Wait for services to start
Write-Host "`n[INFO] Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test services
Write-Host "`n[INFO] Testing services..." -ForegroundColor Yellow

$services = @(
    @{ Name = "Core API"; Url = "http://localhost:5317/health" },
    @{ Name = "Core API Docs"; Url = "http://localhost:5317/docs" },
    @{ Name = "Atlas UI"; Url = "http://localhost:5173/" }
)

$allPassed = $true
foreach ($service in $services) {
    Write-Host "  Testing $($service.Name)..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [FAIL]" -ForegroundColor Red
        $allPassed = $false
    }
}

# Results
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "[SUCCESS] Rika Phase 3.3 is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available Services:" -ForegroundColor White
    Write-Host "  * Atlas UI:     http://localhost:5173" -ForegroundColor Cyan
    Write-Host "  * Core API:     http://localhost:5317" -ForegroundColor Cyan  
    Write-Host "  * API Docs:     http://localhost:5317/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening Atlas UI in browser..." -ForegroundColor Yellow
    Start-Process "http://localhost:5173"
    
    Write-Host ""
    Write-Host "To stop services:" -ForegroundColor Yellow
    Write-Host "  Get-Process python | Where-Object {`$_.MainWindowTitle -like '*uvicorn*' -or `$_.MainWindowTitle -like '*serve*'} | Stop-Process" -ForegroundColor White
} else {
    Write-Host "[ERROR] Some services failed to start" -ForegroundColor Red
    Write-Host "Check that ports 5173 and 5317 are available" -ForegroundColor Yellow
}
Write-Host "======================================================================" -ForegroundColor Cyan