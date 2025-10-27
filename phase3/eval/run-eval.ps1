# phase3/eval/run-eval.ps1
# PowerShell wrapper for Rika Evaluation Harness

param(
    [string[]]$Domains,
    [string[]]$Suites,
    [string]$Output,
    [switch]$Verbose,
    [switch]$List,
    [switch]$Help
)

if ($Help) {
    Write-Host "Rika Evaluation Harness" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\run-eval.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Domains <domain1,domain2>    Run specific domains" -ForegroundColor White
    Write-Host "  -Suites <suite1,suite2>       Run specific suites" -ForegroundColor White  
    Write-Host "  -Output <file.json>           Save results to file" -ForegroundColor White
    Write-Host "  -Verbose                      Show detailed output" -ForegroundColor White
    Write-Host "  -List                         List available suites" -ForegroundColor White
    Write-Host "  -Help                         Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\run-eval.ps1 -List" -ForegroundColor Gray
    Write-Host "  .\run-eval.ps1 -Domains presence_query,link_command -Verbose" -ForegroundColor Gray
    Write-Host "  .\run-eval.ps1 -Output results.json" -ForegroundColor Gray
    Write-Host ""
    return
}

Write-Host "Rika Evaluation Harness" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and ensure it's in your PATH" -ForegroundColor Yellow
    exit 1
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Gray
$deps = @("asyncio", "asyncpg", "httpx", "structlog", "minio", "python-dotenv")
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
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
    } else {
        Write-Host "WARNING: No .env.example found, using defaults" -ForegroundColor Yellow
    }
}

# Check Core API availability
Write-Host "Checking Core API..." -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5317/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Core API available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Core API not available" -ForegroundColor Yellow
    Write-Host "     Starting evaluation anyway (some tests may fail)" -ForegroundColor Gray
}

# Build Python command
$pythonArgs = @("run-eval.py")

if ($List) {
    $pythonArgs += "--list"
}

if ($Domains) {
    $pythonArgs += "--domains"
    $pythonArgs += $Domains
}

if ($Suites) {
    $pythonArgs += "--suites" 
    $pythonArgs += $Suites
}

if ($Output) {
    $pythonArgs += "--output"
    $pythonArgs += $Output
}

if ($Verbose) {
    $pythonArgs += "--verbose"
}

Write-Host ""
Write-Host "Starting evaluation..." -ForegroundColor Cyan
Write-Host "Command: python $($pythonArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run evaluation
try {
    python $pythonArgs
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "✅ Evaluation completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Evaluation completed with issues (exit code: $exitCode)" -ForegroundColor Red
    }
    
    exit $exitCode
    
} catch {
    Write-Host "❌ Evaluation failed: $_" -ForegroundColor Red
    exit 1
}