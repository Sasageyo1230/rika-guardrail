# Rika Phase 3.3 Development Startup - Auto-detects Python entrypoints
# NO venv activation - assumes user environment is ready

param(
    [switch]$NoBrowser
)

# Build paths for PS 5.1
$ScriptDir = $PSScriptRoot
$Phase33Root = Split-Path -Path $ScriptDir -Parent
$RikaRoot = Split-Path -Path $Phase33Root -Parent

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🚀 Rika Phase 3.3 - Development Mode" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Check environment status only (no activation)
if ($env:VIRTUAL_ENV) {
    Write-Host "[OK] Using venv: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "[WARNING] No virtual environment detected" -ForegroundColor Yellow
}

# Function to detect Python app module
function Get-PythonModule {
    param([string]$ServicePath)
    
    $mainPy = Join-Path -Path $ServicePath -ChildPath "main.py"
    $apiPy = Join-Path -Path $ServicePath -ChildPath "api.py"
    $appPy = Join-Path -Path $ServicePath -ChildPath "app.py"
    
    # Check main.py first
    if (Test-Path $mainPy) {
        $content = Get-Content -Path $mainPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) {
            return @{ Module = "main"; Found = $true }
        }
    }
    
    # Check api.py
    if (Test-Path $apiPy) {
        $content = Get-Content -Path $apiPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) {
            return @{ Module = "api"; Found = $true }
        }
    }
    
    # Check app.py
    if (Test-Path $appPy) {
        $content = Get-Content -Path $appPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) {
            return @{ Module = "app"; Found = $true }
        }
    }
    
    # Fallback to api (common default)
    return @{ Module = "api"; Found = $false }
}

# Service definitions
$services = @(
    @{
        Name = "Core API"
        Folder = "core"
        Port = 5317
        Type = "python"
    },
    @{
        Name = "Overseer"
        Folder = "overseer"
        Port = 5319
        Type = "python"
    },
    @{
        Name = "Great Sage"
        Folder = "great_sage"
        Port = 5320
        Type = "python"
    },
    @{
        Name = "Research Vault"
        Folder = "research_vault"
        Port = 5321
        Type = "python"
    },
    @{
        Name = "Atlas UI"
        Folder = "ui"
        Port = 5173
        Type = "node"
    }
)

Write-Host "`nStarting services..." -ForegroundColor Yellow
Write-Host ("-" * 50) -ForegroundColor Gray

$startedServices = @()

foreach ($service in $services) {
    $servicePath = Join-Path -Path $RikaRoot -ChildPath $service.Folder
    
    if (Test-Path $servicePath) {
        Write-Host "$($service.Name)..." -ForegroundColor Cyan -NoNewline
        
        try {
            if ($service.Type -eq "python") {
                # Auto-detect Python module
                $moduleInfo = Get-PythonModule -ServicePath $servicePath
                $moduleApp = "$($moduleInfo.Module):app"
                
                if (-not $moduleInfo.Found) {
                    Write-Host " [WARNING] Using fallback ($moduleApp)" -ForegroundColor Yellow
                    Write-Host "    Hint: Create $($service.Folder)\main.py with app = FastAPI()" -ForegroundColor Gray
                }
                
                # Start Python service
                $args = @(
                    "-m", "uvicorn",
                    $moduleApp,
                    "--reload",
                    "--host", "0.0.0.0",
                    "--port", $service.Port
                )
                
                Start-Process -FilePath "python" `
                             -ArgumentList $args `
                             -WorkingDirectory $servicePath `
                             -PassThru | Out-Null
                
                $startedServices += $service
                if ($moduleInfo.Found) {
                    Write-Host " [OK] Started on port $($service.Port) ($moduleApp)" -ForegroundColor Green
                } else {
                    Write-Host " [WARNING] Started on port $($service.Port) ($moduleApp - fallback)" -ForegroundColor Yellow
                }
                
            } elseif ($service.Type -eq "node") {
                # Check if package.json exists
                $packageJson = Join-Path -Path $servicePath -ChildPath "package.json"
                if (-not (Test-Path $packageJson)) {
                    Write-Host " [ERROR] No package.json found" -ForegroundColor Red
                    continue
                }
                
                # Start Node service
                Start-Process -FilePath "npm" `
                             -ArgumentList "run", "dev" `
                             -WorkingDirectory $servicePath `
                             -PassThru | Out-Null
                
                $startedServices += $service
                Write-Host " [OK] Started on port $($service.Port)" -ForegroundColor Green
            }
            
            # Brief pause between starts
            Start-Sleep -Milliseconds 800
            
        } catch {
            Write-Host " [ERROR] Failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "$($service.Name)... - Skipped (folder not found)" -ForegroundColor Gray
    }
}

# Display summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🎯 Services Running:" -ForegroundColor Green
Write-Host ("-" * 50) -ForegroundColor Gray

if ($startedServices.Count -gt 0) {
    foreach ($service in $startedServices) {
        $url = "http://localhost:$($service.Port)"
        Write-Host "  * $($service.Name): $url" -ForegroundColor White
    }
    
    Write-Host "`nTo stop services: Close console windows or Ctrl+C in each" -ForegroundColor Yellow
    
    # Open browser
    if (-not $NoBrowser) {
        $atlasService = $startedServices | Where-Object { $_.Name -eq "Atlas UI" }
        if ($atlasService) {
            Start-Sleep -Seconds 3
            Write-Host "`n🌐 Opening Atlas UI..." -ForegroundColor Cyan
            Start-Process "http://localhost:5173"
        }
    }
} else {
    Write-Host "[FAIL] No services started!" -ForegroundColor Red
    Write-Host "Create service folders with FastAPI apps:" -ForegroundColor Yellow
    Write-Host "  core\main.py with app = FastAPI()" -ForegroundColor White
    Write-Host "  overseer\main.py with app = FastAPI()" -ForegroundColor White
}

Write-Host ("=" * 70) -ForegroundColor Cyan