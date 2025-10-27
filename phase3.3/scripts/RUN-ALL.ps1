# Rika Phase 3.3 - Complete Setup and Start Script
# This script runs everything in sequence

Write-Host "[INFO] Starting Rika Phase 3.3 Complete Setup..." -ForegroundColor Cyan

# Check if virtual environment is active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[WARNING] No virtual environment active. Attempting to activate..." -ForegroundColor Yellow
    $venvPath = Join-Path (Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent) -ChildPath ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        & $venvPath
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Virtual environment not found at $venvPath" -ForegroundColor Red
        Write-Host "[INFO] Please create a virtual environment first:" -ForegroundColor Yellow
        Write-Host "  python -m venv .venv" -ForegroundColor White
        exit 1
    }
}

# Run diagnostic
Write-Host "`n[INFO] Running diagnostic..." -ForegroundColor Cyan
& "$PSScriptRoot\run-diagnostic.bat"

# Run setup
Write-Host "`n[INFO] Running setup..." -ForegroundColor Cyan
& "$PSScriptRoot\setup.ps1"

# Start development servers
Write-Host "`n[INFO] Starting development servers..." -ForegroundColor Cyan
& "$PSScriptRoot\start-dev.ps1"