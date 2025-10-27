# phase3/overseer/start-overseer.ps1
# Start Rika Overseer service

Write-Host "Starting Rika Overseer - Policy Gatekeeper..." -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Gray
$deps = @("fastapi", "uvicorn", "asyncpg", "httpx", "pydantic")
foreach ($dep in $deps) {
    try {
        python -c "import $dep; print('$dep: OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $dep" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $dep (installing...)" -ForegroundColor Yellow
            pip install $dep
        }
    } catch {
        Write-Host "  ❌ $dep (installing...)" -ForegroundColor Yellow
        pip install $dep
    }
}

# Load environment
if (Test-Path ".env") {
    Write-Host "Loading .env file..." -ForegroundColor Gray
} else {
    Write-Host "Creating .env from template..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
}

# Check port availability
$port = 5319
$portBusy = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($portBusy) {
    Write-Host "WARNING: Port $port is busy!" -ForegroundColor Yellow
    $process = Get-Process -Id $portBusy.OwningProcess -ErrorAction SilentlyContinue
    Write-Host "Process: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
    
    $choice = Read-Host "Kill process and start Overseer? (y/n)"
    if ($choice -eq "y") {
        Stop-Process -Id $process.Id -Force
        Write-Host "Process killed." -ForegroundColor Green
    } else {
        exit
    }
}

Write-Host ""
Write-Host "Starting Overseer on port $port..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Green
Write-Host "  • Health: http://localhost:$port/health" -ForegroundColor White
Write-Host "  • Policy: http://localhost:$port/policy" -ForegroundColor White
Write-Host "  • Check: POST http://localhost:$port/check" -ForegroundColor White
Write-Host "  • Approve: POST http://localhost:$port/approve" -ForegroundColor White
Write-Host "  • Docs: http://localhost:$port/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start Overseer
python -m uvicorn overseer:app --host 0.0.0.0 --port $port --reload