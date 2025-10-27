# Rika Phase 3.3 Production Startup - Background services with logging
# NO venv activation - assumes user environment is ready

param(
    [switch]$ShowLogs
)

# Build paths for PS 5.1
$ScriptDir = $PSScriptRoot
$Phase33Root = Split-Path -Path $ScriptDir -Parent
$RikaRoot = Split-Path -Path $Phase33Root -Parent
$LogsDir = Join-Path -Path $Phase33Root -ChildPath "logs"

# Ensure log directory
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🏭 Rika Phase 3.3 - Production Mode" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Function to detect Python module
function Get-PythonModule {
    param([string]$ServicePath)
    
    $mainPy = Join-Path -Path $ServicePath -ChildPath "main.py"
    $apiPy = Join-Path -Path $ServicePath -ChildPath "api.py"
    $appPy = Join-Path -Path $ServicePath -ChildPath "app.py"
    
    if (Test-Path $mainPy) {
        $content = Get-Content -Path $mainPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) { return "main" }
    }
    
    if (Test-Path $apiPy) {
        $content = Get-Content -Path $apiPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) { return "api" }
    }
    
    if (Test-Path $appPy) {
        $content = Get-Content -Path $appPy -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'app\s*=' -or $content -match 'FastAPI')) { return "app" }
    }
    
    return "api"
}

# Service definitions
$services = @(
    @{
        Name = "Core API"
        Folder = "core"
        Port = 5317
        Type = "python"
        LogFile = "core_api.log"
    },
    @{
        Name = "Overseer"
        Folder = "overseer"
        Port = 5319
        Type = "python"
        LogFile = "overseer.log"
    },
    @{
        Name = "Great Sage"
        Folder = "great_sage"
        Port = 5320
        Type = "python"
        LogFile = "great_sage.log"
    },
    @{
        Name = "Research Vault"
        Folder = "research_vault"
        Port = 5321
        Type = "python"
        LogFile = "research_vault.log"
    },
    @{
        Name = "Atlas UI"
        Folder = "ui"
        Port = 5173
        Type = "node"
        LogFile = "atlas_ui.log"
    }
)

Write-Host "`nStarting production services..." -ForegroundColor Yellow
Write-Host ("-" * 50) -ForegroundColor Gray

$startedServices = @()

foreach ($service in $services) {
    $servicePath = Join-Path -Path $RikaRoot -ChildPath $service.Folder
    $logPath = Join-Path -Path $LogsDir -ChildPath $service.LogFile
    
    if (Test-Path $servicePath) {
        Write-Host "$($service.Name)..." -ForegroundColor Cyan -NoNewline
        
        try {
            # Add timestamp to log
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            "[$timestamp] Starting $($service.Name) on port $($service.Port)" | Out-File -FilePath $logPath -Append
            
            if ($service.Type -eq "python") {
                $module = Get-PythonModule -ServicePath $servicePath
                $moduleApp = "${module}:app"
                
                $args = @(
                    "-m", "uvicorn",
                    $moduleApp,
                    "--host", "0.0.0.0",
                    "--port", $service.Port
                )
                
                Start-Process -FilePath "python" `
                             -ArgumentList $args `
                             -WorkingDirectory $servicePath `
                             -WindowStyle Hidden `
                             -RedirectStandardOutput $logPath `
                             -RedirectStandardError $logPath
                
                $startedServices += @{
                    Name = $service.Name
                    Port = $service.Port
                    LogFile = $logPath
                    Module = $moduleApp
                }
                Write-Host " [OK] Started ($moduleApp)" -ForegroundColor Green
                
            } elseif ($service.Type -eq "node") {
                # Check for package.json
                $packageJson = Join-Path -Path $servicePath -ChildPath "package.json"
                if (-not (Test-Path $packageJson)) {
                    Write-Host " [ERROR] No package.json" -ForegroundColor Red
                    continue
                }
                
                Start-Process -FilePath "npm" `
                             -ArgumentList "run", "start" `
                             -WorkingDirectory $servicePath `
                             -WindowStyle Hidden `
                             -RedirectStandardOutput $logPath `
                             -RedirectStandardError $logPath
                
                $startedServices += @{
                    Name = $service.Name
                    Port = $service.Port
                    LogFile = $logPath
                }
                Write-Host " [OK] Started" -ForegroundColor Green
            }
            
            Start-Sleep -Milliseconds 800
            
        } catch {
            Write-Host " [ERROR] Failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "$($service.Name)... - Skipped (not found)" -ForegroundColor Gray
    }
}

# Display summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🏭 Production Services Running:" -ForegroundColor Green
Write-Host ("-" * 50) -ForegroundColor Gray

if ($startedServices.Count -gt 0) {
    foreach ($service in $startedServices) {
        Write-Host "  * $($service.Name): http://localhost:$($service.Port)" -ForegroundColor White
        Write-Host "    📄 Log: $($service.LogFile)" -ForegroundColor Gray
    }
    
    Write-Host "`nTo stop all services:" -ForegroundColor Yellow
    Write-Host "  Get-Process python, node | Stop-Process -Force" -ForegroundColor White
} else {
    Write-Host "[FAIL] No services started!" -ForegroundColor Red
}

# Show logs if requested
if ($ShowLogs -and $startedServices.Count -gt 0) {
    Write-Host "`n📄 Tailing logs (Ctrl+C to stop)..." -ForegroundColor Yellow
    $logFiles = $startedServices | ForEach-Object { $_.LogFile }
    Get-Content -Path $logFiles -Wait -Tail 10
}

Write-Host ("=" * 70) -ForegroundColor Cyan