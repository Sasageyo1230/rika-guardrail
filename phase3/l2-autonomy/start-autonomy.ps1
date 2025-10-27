# phase3/l2-autonomy/start-autonomy.ps1
# Start L2 Guarded Autonomy System

param(
    [string]$Level = "disabled",  # disabled, l1_supervised, l2_guarded
    [switch]$EnableHUD,
    [switch]$TestMode,
    [switch]$Help
)

if ($Help) {
    Write-Host "Rika L2 Guarded Autonomy System" -ForegroundColor Cyan
    Write-Host "===============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\start-autonomy.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Level <level>     Set autonomy level (disabled, l1_supervised, l2_guarded)" -ForegroundColor White
    Write-Host "  -EnableHUD         Enable autonomy status HUD" -ForegroundColor White
    Write-Host "  -TestMode          Start in test mode with mock agents" -ForegroundColor White
    Write-Host "  -Help              Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\start-autonomy.ps1 -Level l2_guarded -EnableHUD" -ForegroundColor Gray
    Write-Host "  .\start-autonomy.ps1 -TestMode" -ForegroundColor Gray
    Write-Host ""
    return
}

Write-Host "🤖 Rika L2 Guarded Autonomy System" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

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
$deps = @("fastapi", "uvicorn", "asyncpg", "httpx", "pydantic", "structlog")
$missing = @()

foreach ($dep in $deps) {
    try {
        python -c "import $dep" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $dep" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $dep" -ForegroundColor Red
            $missing += $dep
        }
    } catch {
        Write-Host "  ❌ $dep" -ForegroundColor Red
        $missing += $dep
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Installing missing dependencies..." -ForegroundColor Yellow
    pip install $missing
}

# Load environment
if (Test-Path ".env") {
    Write-Host "Found .env file" -ForegroundColor Green
} else {
    Write-Host "Creating .env from example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Check port availability
$port = 5322
$portBusy = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($portBusy) {
    Write-Host "WARNING: Port $port is busy!" -ForegroundColor Yellow
    $process = Get-Process -Id $portBusy.OwningProcess -ErrorAction SilentlyContinue
    Write-Host "Process: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
    
    $choice = Read-Host "Kill process and start L2 Autonomy? (y/n)"
    if ($choice -eq "y") {
        Stop-Process -Id $process.Id -Force
        Write-Host "Process killed." -ForegroundColor Green
    } else {
        exit
    }
}

# Check dependencies - Overseer
Write-Host "Checking system dependencies..." -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5319/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Overseer available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Overseer not available" -ForegroundColor Yellow
    Write-Host "     Some autonomy features will be limited" -ForegroundColor Gray
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5320/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Great Sage available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Great Sage not available" -ForegroundColor Yellow
    Write-Host "     Reflection and improvement features disabled" -ForegroundColor Gray
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5317/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Core API available" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Core API not available" -ForegroundColor Red
    Write-Host "     L2 Autonomy requires Core API to function" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting L2 Autonomy Controller on port $port..." -ForegroundColor Cyan
Write-Host "Initial autonomy level: $Level" -ForegroundColor Yellow

if ($TestMode) {
    Write-Host "🧪 Test mode enabled - using mock agents" -ForegroundColor Magenta
}

if ($EnableHUD) {
    Write-Host "📊 Autonomy HUD enabled" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Green
Write-Host "  • Health: http://localhost:$port/health" -ForegroundColor White
Write-Host "  • Status: http://localhost:$port/status" -ForegroundColor White
Write-Host "  • Set Level: POST http://localhost:$port/set-level" -ForegroundColor White
Write-Host "  • Request Action: POST http://localhost:$port/request-action" -ForegroundColor White
Write-Host "  • Execute Task: POST http://localhost:$port/execute-task" -ForegroundColor White
Write-Host "  • Task Status: GET http://localhost:$port/task/{id}" -ForegroundColor White
Write-Host "  • Docs: http://localhost:$port/docs" -ForegroundColor White
Write-Host ""
Write-Host "Agent Commands:" -ForegroundColor Green
Write-Host "  • Scout: python agents/scout.py '<task>'" -ForegroundColor White  
Write-Host "  • Craft: python agents/craft.py '<task>'" -ForegroundColor White
Write-Host ""

# Set environment variables for initial configuration
$env:INITIAL_AUTONOMY_LEVEL = $Level
if ($TestMode) { $env:TEST_MODE = "true" }
if ($EnableHUD) { $env:ENABLE_HUD = "true" }

Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start L2 Autonomy Controller
python -m uvicorn autonomy_controller:app --host 0.0.0.0 --port $port --reload