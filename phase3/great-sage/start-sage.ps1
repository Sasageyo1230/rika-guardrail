# phase3/great-sage/start-sage.ps1
# Start Great Sage - Meta-Cortex Improvement Loop

Write-Host "Starting Great Sage - Meta-Cortex Improvement Loop..." -ForegroundColor Magenta
Write-Host "====================================================" -ForegroundColor Magenta

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
$deps = @("fastapi", "uvicorn", "asyncpg", "httpx", "pydantic", "pandas", "numpy", "spacy")
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
$port = 5320
$portBusy = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($portBusy) {
    Write-Host "WARNING: Port $port is busy!" -ForegroundColor Yellow
    $process = Get-Process -Id $portBusy.OwningProcess -ErrorAction SilentlyContinue
    Write-Host "Process: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
    
    $choice = Read-Host "Kill process and start Great Sage? (y/n)"
    if ($choice -eq "y") {
        Stop-Process -Id $process.Id -Force
        Write-Host "Process killed." -ForegroundColor Green
    } else {
        exit
    }
}

# Check Overseer dependency
Write-Host "Checking Overseer connection..." -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5319/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Overseer available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Overseer not available (starting anyway)" -ForegroundColor Yellow
    Write-Host "     Some features may be limited without Overseer" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Starting Great Sage on port $port..." -ForegroundColor Magenta
Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Green
Write-Host "  • Health: http://localhost:$port/health" -ForegroundColor White
Write-Host "  • Reflect: POST http://localhost:$port/reflect" -ForegroundColor White  
Write-Host "  • Evaluate: POST http://localhost:$port/evaluate" -ForegroundColor White
Write-Host "  • Promote: POST http://localhost:$port/promote" -ForegroundColor White
Write-Host "  • Status: http://localhost:$port/status" -ForegroundColor White
Write-Host "  • Docs: http://localhost:$port/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start Great Sage
python -m uvicorn sage:app --host 0.0.0.0 --port $port --reload