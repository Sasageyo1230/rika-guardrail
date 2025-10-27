# Rika Phase 2.5 - Service Management Script
# Usage: .\start-all.ps1 [start|stop|restart|status]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs")]
    [string]$Action = "start"
)

# Configuration
$RootPath = Split-Path -Parent $PSScriptRoot
$Services = @(
    @{
        Name = "NATS Server"
        Path = $RootPath
        Command = "nats-server"
        Args = @("--config", "nats.conf")
        Port = 4222
        LogFile = "logs\nats.log"
        ProcessName = "nats-server"
    },
    @{
        Name = "Core API"
        Path = Join-Path $RootPath "core"
        Command = "python"
        Args = @("api.py")
        Port = 8000
        LogFile = "logs\api.log"
        ProcessName = "python"
        Env = @{
            "PYTHONPATH" = Join-Path $RootPath "core"
        }
    },
    @{
        Name = "Desktop Agent"
        Path = Join-Path $RootPath "agent-desktop"
        Command = "python"
        Args = @("agent.py")
        Port = $null
        LogFile = "logs\agent.log"
        ProcessName = "python"
        RequiresAdmin = $true
    },
    @{
        Name = "Atlas UI"
        Path = Join-Path $RootPath "ui"
        Command = "npm"
        Args = @("run", "dev")
        Port = 5173
        LogFile = "logs\ui.log"
        ProcessName = "node"
    }
)

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-ServicePort {
    param([int]$Port)
    if (-not $Port) { return $true }
    
    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port $Port -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

function Start-RikaService {
    param($Service)
    
    Write-ColoredOutput "Starting $($Service.Name)..." "Yellow"
    
    # Check if service requires admin rights
    if ($Service.RequiresAdmin -and -not (Test-Administrator)) {
        Write-ColoredOutput "  ERROR: $($Service.Name) requires Administrator privileges" "Red"
        Write-ColoredOutput "  Please run PowerShell as Administrator" "Red"
        return $false
    }
    
    # Create logs directory
    $logDir = Join-Path $Service.Path "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Set working directory
    $originalLocation = Get-Location
    Set-Location $Service.Path
    
    try {
        # Prepare environment variables
        $env = @{}
        if ($Service.Env) {
            foreach ($key in $Service.Env.Keys) {
                $env[$key] = $Service.Env[$key]
            }
        }
        
        # Start the service
        $processArgs = @{
            FilePath = $Service.Command
            ArgumentList = $Service.Args
            WindowStyle = "Minimized"
            PassThru = $true
        }
        
        if ($Service.LogFile) {
            $logPath = Join-Path $Service.Path $Service.LogFile
            $processArgs.RedirectStandardOutput = $logPath
            $processArgs.RedirectStandardError = $logPath + ".err"
        }
        
        # Set environment variables
        foreach ($key in $env.Keys) {
            Set-Item -Path "env:$key" -Value $env[$key]
        }
        
        $process = Start-Process @processArgs
        
        # Wait a moment for startup
        Start-Sleep -Seconds 3
        
        # Check if service started successfully
        if ($Service.Port) {
            $retries = 0
            $maxRetries = 20  # 20 seconds total
            
            do {
                Start-Sleep -Seconds 1
                $isRunning = Test-ServicePort -Port $Service.Port
                $retries++
            } while (-not $isRunning -and $retries -lt $maxRetries)
            
            if ($isRunning) {
                Write-ColoredOutput "  ✓ $($Service.Name) started successfully on port $($Service.Port)" "Green"
                return $true
            } else {
                Write-ColoredOutput "  ✗ $($Service.Name) failed to start (port $($Service.Port) not accessible)" "Red"
                return $false
            }
        } else {
            # For services without ports, check process is still running
            if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
                Write-ColoredOutput "  ✓ $($Service.Name) started successfully" "Green"
                return $true
            } else {
                Write-ColoredOutput "  ✗ $($Service.Name) process exited unexpectedly" "Red"
                return $false
            }
        }
        
    } catch {
        Write-ColoredOutput "  ✗ Failed to start $($Service.Name): $($_.Exception.Message)" "Red"
        return $false
    } finally {
        Set-Location $originalLocation
    }
}

function Stop-RikaService {
    param($Service)
    
    Write-ColoredOutput "Stopping $($Service.Name)..." "Yellow"
    
    try {
        # Find and stop processes
        $processes = Get-Process -Name $Service.ProcessName -ErrorAction SilentlyContinue
        
        if ($processes) {
            foreach ($process in $processes) {
                # For Python processes, check command line to match specific service
                if ($Service.ProcessName -eq "python") {
                    $commandLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
                    if ($commandLine -and $commandLine.Contains($Service.Args[0])) {
                        $process.Kill()
                        Write-ColoredOutput "  ✓ Stopped $($Service.Name) (PID: $($process.Id))" "Green"
                    }
                } else {
                    $process.Kill()
                    Write-ColoredOutput "  ✓ Stopped $($Service.Name) (PID: $($process.Id))" "Green"
                }
            }
        } else {
            Write-ColoredOutput "  - $($Service.Name) was not running" "Gray"
        }
        
        return $true
        
    } catch {
        Write-ColoredOutput "  ✗ Failed to stop $($Service.Name): $($_.Exception.Message)" "Red"
        return $false
    }
}

function Get-ServiceStatus {
    param($Service)
    
    $isRunning = $false
    $pid = $null
    
    if ($Service.Port) {
        $isRunning = Test-ServicePort -Port $Service.Port
        if ($isRunning) {
            # Try to find the process using the port
            try {
                $connection = Get-NetTCPConnection -LocalPort $Service.Port -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($connection) {
                    $pid = (Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue).Id
                }
            } catch {
                # Ignore errors getting process info
            }
        }
    } else {
        # Check by process name
        $processes = Get-Process -Name $Service.ProcessName -ErrorAction SilentlyContinue
        if ($processes) {
            $isRunning = $true
            $pid = $processes[0].Id
        }
    }
    
    return @{
        Name = $Service.Name
        Running = $isRunning
        Port = $Service.Port
        ProcessId = $pid
    }
}

function Show-ServiceLogs {
    param($Service)
    
    Write-ColoredOutput "=== $($Service.Name) Logs ===" "Cyan"
    
    $logPath = Join-Path $Service.Path $Service.LogFile
    $errorLogPath = $logPath + ".err"
    
    if (Test-Path $logPath) {
        Write-ColoredOutput "--- Standard Output ---" "Yellow"
        Get-Content $logPath -Tail 20 | ForEach-Object { Write-Host $_ }
    }
    
    if (Test-Path $errorLogPath) {
        Write-ColoredOutput "--- Standard Error ---" "Red"
        Get-Content $errorLogPath -Tail 20 | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    }
    
    if (-not (Test-Path $logPath) -and -not (Test-Path $errorLogPath)) {
        Write-ColoredOutput "No log files found for $($Service.Name)" "Gray"
    }
    
    Write-ColoredOutput "" "White"
}

# Main script logic
switch ($Action.ToLower()) {
    "start" {
        Write-ColoredOutput "🚀 Starting Rika Phase 2.5 Services" "Cyan"
        Write-ColoredOutput "=====================================" "Cyan"
        
        $allStarted = $true
        
        foreach ($service in $Services) {
            $started = Start-RikaService -Service $service
            $allStarted = $allStarted -and $started
        }
        
        Write-ColoredOutput "" "White"
        if ($allStarted) {
            Write-ColoredOutput "✅ All services started successfully!" "Green"
            Write-ColoredOutput "🌐 Atlas Dashboard: http://localhost:5173" "Cyan"
            Write-ColoredOutput "🔧 Core API: http://localhost:8000" "Cyan"
            Write-ColoredOutput "📊 n8n: http://localhost:5678" "Cyan"
        } else {
            Write-ColoredOutput "❌ Some services failed to start. Check logs for details." "Red"
        }
    }
    
    "stop" {
        Write-ColoredOutput "🛑 Stopping Rika Phase 2.5 Services" "Cyan"
        Write-ColoredOutput "====================================" "Cyan"
        
        # Stop services in reverse order
        $reversedServices = $Services | Sort-Object { $_.Name } -Descending
        
        foreach ($service in $reversedServices) {
            Stop-RikaService -Service $service
        }
        
        Write-ColoredOutput "" "White"
        Write-ColoredOutput "✅ All services stopped" "Green"
    }
    
    "restart" {
        Write-ColoredOutput "🔄 Restarting Rika Phase 2.5 Services" "Cyan"
        Write-ColoredOutput "======================================" "Cyan"
        
        # Stop all services first
        $reversedServices = $Services | Sort-Object { $_.Name } -Descending
        foreach ($service in $reversedServices) {
            Stop-RikaService -Service $service
        }
        
        Write-ColoredOutput "Waiting 5 seconds before restart..." "Yellow"
        Start-Sleep -Seconds 5
        
        # Start all services
        $allStarted = $true
        foreach ($service in $Services) {
            $started = Start-RikaService -Service $service
            $allStarted = $allStarted -and $started
        }
        
        Write-ColoredOutput "" "White"
        if ($allStarted) {
            Write-ColoredOutput "✅ All services restarted successfully!" "Green"
        } else {
            Write-ColoredOutput "❌ Some services failed to restart. Check logs for details." "Red"
        }
    }
    
    "status" {
        Write-ColoredOutput "📊 Rika Phase 2.5 Service Status" "Cyan"
        Write-ColoredOutput "=================================" "Cyan"
        
        foreach ($service in $Services) {
            $status = Get-ServiceStatus -Service $service
            
            $statusText = if ($status.Running) { "✅ RUNNING" } else { "❌ STOPPED" }
            $portText = if ($status.Port) { " (Port: $($status.Port))" } else { "" }
            $pidText = if ($status.ProcessId) { " [PID: $($status.ProcessId)]" } else { "" }
            
            $color = if ($status.Running) { "Green" } else { "Red" }
            Write-ColoredOutput "$($status.Name): $statusText$portText$pidText" $color
        }
        
        Write-ColoredOutput "" "White"
        
        # Additional health checks
        Write-ColoredOutput "🔍 Health Checks" "Cyan"
        Write-ColoredOutput "=================" "Cyan"
        
        # Test Core API health
        try {
            $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
            if ($healthResponse.status -eq "healthy") {
                Write-ColoredOutput "Core API Health: ✅ HEALTHY" "Green"
            } else {
                Write-ColoredOutput "Core API Health: ⚠️  DEGRADED" "Yellow"
            }
        } catch {
            Write-ColoredOutput "Core API Health: ❌ UNHEALTHY" "Red"
        }
        
        # Test Atlas UI
        try {
            $uiResponse = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5
            if ($uiResponse.StatusCode -eq 200) {
                Write-ColoredOutput "Atlas UI: ✅ ACCESSIBLE" "Green"
            } else {
                Write-ColoredOutput "Atlas UI: ⚠️  DEGRADED" "Yellow"
            }
        } catch {
            Write-ColoredOutput "Atlas UI: ❌ INACCESSIBLE" "Red"
        }
        
        # Test NATS
        try {
            $natsRunning = Test-ServicePort -Port 4222
            if ($natsRunning) {
                Write-ColoredOutput "NATS: ✅ ACCESSIBLE" "Green"
            } else {
                Write-ColoredOutput "NATS: ❌ INACCESSIBLE" "Red"
            }
        } catch {
            Write-ColoredOutput "NATS: ❌ ERROR" "Red"
        }
        
        # Test Database (if we can connect)
        try {
            # This would require postgres client tools
            # For now, just check if PostgreSQL process is running
            $postgresProcess = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
            if ($postgresProcess) {
                Write-ColoredOutput "PostgreSQL: ✅ RUNNING" "Green"
            } else {
                Write-ColoredOutput "PostgreSQL: ❓ STATUS UNKNOWN" "Yellow"
            }
        } catch {
            Write-ColoredOutput "PostgreSQL: ❓ STATUS UNKNOWN" "Yellow"
        }
    }
    
    "logs" {
        Write-ColoredOutput "📋 Rika Phase 2.5 Service Logs" "Cyan"
        Write-ColoredOutput "===============================" "Cyan"
        
        foreach ($service in $Services) {
            if ($service.LogFile) {
                Show-ServiceLogs -Service $service
            }
        }
    }
    
    default {
        Write-ColoredOutput "❓ Unknown action: $Action" "Red"
        Write-ColoredOutput "" "White"
        Write-ColoredOutput "Usage: .\start-all.ps1 [start|stop|restart|status|logs]" "Yellow"
        Write-ColoredOutput "" "White"
        Write-ColoredOutput "Actions:" "White"
        Write-ColoredOutput "  start   - Start all Phase 2.5 services" "White"
        Write-ColoredOutput "  stop    - Stop all Phase 2.5 services" "White"
        Write-ColoredOutput "  restart - Stop and start all services" "White"
        Write-ColoredOutput "  status  - Show status of all services" "White"
        Write-ColoredOutput "  logs    - Show recent logs from all services" "White"
    }
}