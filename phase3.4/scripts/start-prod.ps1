# Rika Phase 3.4 Production Server - PowerShell 5.1 Compatible
# Starts production-optimized servers

param(
    [switch]$SkipUI,
    [switch]$SkipAPI,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# ASCII-safe status indicators
$CHECK = "[OK]"
$ERR = "[ERROR]"
$WARN = "[WARNING]"
$INFO = "[INFO]"
$START = "[START]"

function Write-Status {
    param($Message, $Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Type $Message"
}

function Test-Port {
    param($Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Wait-ForService {
    param($Url, $Name, $MaxAttempts = 30)
    
    Write-Status "Waiting for $Name to start..." $INFO
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Status "$Name is ready!" $CHECK
                return $true
            }
        } catch {
            # Service not ready yet
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    
    Write-Status "$Name failed to start within $MaxAttempts seconds" $ERR
    return $false
}

Write-Status "Starting Rika Phase 3.4 Production Environment..." $START

# Check if we're in the right directory
if (-not (Test-Path "core\main.py")) {
    Write-Status "Please run this script from the rika-core directory" $ERR
    exit 1
}

# Auto-detect virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Status "Using virtual environment: $env:VIRTUAL_ENV" $CHECK
    $pythonCmd = "python"
} elseif (Test-Path "venv\Scripts\python.exe") {
    Write-Status "Using local virtual environment" $CHECK
    $pythonCmd = "venv\Scripts\python.exe"
} else {
    Write-Status "Using system Python" $INFO
    $pythonCmd = "python"
}

# Check for required files
if (-not (Test-Path ".env")) {
    Write-Status "No .env file found. Run setup.ps1 first." $ERR
    exit 1
}

# Build UI for production
if (-not $SkipUI) {
    Write-Status "Building Atlas UI for production..." $START
    
    Push-Location "ui"
    try {
        # Install dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Status "Installing UI dependencies..." $INFO
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Status "Failed to install UI dependencies" $ERR
                exit 1
            }
        }
        
        # Build production version
        Write-Status "Building production assets..." $INFO
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Status "Failed to build UI" $ERR
            exit 1
        }
        
        Write-Status "UI build completed successfully" $CHECK
    } finally {
        Pop-Location
    }
}

# Stop any existing services on our ports
$ports = @(5317, 5173)
foreach ($port in $ports) {
    if (Test-Port $port) {
        Write-Status "Port $port is in use. Attempting to free it..." $WARN
        
        # Find and kill processes using the port
        $processes = netstat -ano | Select-String ":$port "
        foreach ($line in $processes) {
            if ($line -match "\s+(\d+)$") {
                $pid = $matches[1]
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Status "Stopped process $pid using port $port" $INFO
                } catch {
                    # Process might already be stopped
                }
            }
        }
        
        Start-Sleep -Seconds 2
    }
}

# Start Core API in production mode
if (-not $SkipAPI) {
    Write-Status "Starting Core API in production mode..." $START
    
    $apiJob = Start-Job -ScriptBlock {
        param($pythonCmd, $workingDir)
        
        Set-Location (Join-Path $workingDir "core")
        
        # Production settings: more workers, no reload, optimized for performance
        if ($pythonCmd -eq "python") {
            python -m uvicorn main:app --host 0.0.0.0 --port 5317 --workers 4 --log-level warning
        } else {
            & (Join-Path $workingDir $pythonCmd) -m uvicorn main:app --host 0.0.0.0 --port 5317 --workers 4 --log-level warning
        }
    } -ArgumentList $pythonCmd, (Get-Location).Path
    
    # Wait for API to be ready
    if (-not (Wait-ForService "http://localhost:5317/health" "Core API")) {
        Write-Status "Failed to start Core API" $ERR
        exit 1
    }
    
    Write-Status "Core API started in production mode" $CHECK
    Write-Status "API Documentation: http://localhost:5317/docs" $INFO
} else {
    Write-Status "Skipping Core API startup" $INFO
}

# Start UI in production mode
if (-not $SkipUI) {
    Write-Status "Starting Atlas UI in production mode..." $START
    
    Push-Location "ui"
    try {
        # Serve the built files using npm preview
        $uiJob = Start-Job -ScriptBlock {
            param($workingDir)
            Set-Location (Join-Path $workingDir "ui")
            # Production preview with optimized settings
            npm run preview -- --host 0.0.0.0 --port 5173
        } -ArgumentList (Get-Location).Parent.Path
        
        # Wait for UI to be ready
        if (-not (Wait-ForService "http://localhost:5173" "Atlas UI")) {
            Write-Status "Failed to start Atlas UI" $ERR
            exit 1
        }
        
        Write-Status "Atlas UI started in production mode" $CHECK
        Write-Status "Atlas UI: http://localhost:5173" $INFO
    } finally {
        Pop-Location
    }
} else {
    Write-Status "Skipping Atlas UI startup" $INFO
}

Write-Status "" $INFO
Write-Status "Rika Phase 3.4 Production Environment is running!" $CHECK
Write-Status "" $INFO
Write-Status "Services:" $INFO
if (-not $SkipAPI) {
    Write-Status "  Core API:        http://localhost:5317" $INFO
    Write-Status "  API Docs:        http://localhost:5317/docs" $INFO
}
if (-not $SkipUI) {
    Write-Status "  Atlas UI:        http://localhost:5173" $INFO
}
Write-Status "" $INFO
Write-Status "Production Features:" $INFO
Write-Status "  - Optimized performance" $INFO
Write-Status "  - Multiple API workers" $INFO
Write-Status "  - Minified UI assets" $INFO
Write-Status "  - Production logging" $INFO
Write-Status "" $INFO
Write-Status "Monitoring:" $INFO
Write-Status "  - Health check: http://localhost:5317/health" $INFO
Write-Status "  - Logs are minimal in production mode" $INFO
Write-Status "" $INFO
Write-Status "Press Ctrl+C to stop all services" $INFO

# Keep the script running and monitor services
try {
    while ($true) {
        Start-Sleep -Seconds 30  # Less frequent checks in production
        
        # Check if jobs are still running
        if (-not $SkipAPI) {
            if ($apiJob.State -ne "Running") {
                Write-Status "Core API job stopped unexpectedly" $ERR
                break
            }
        }
        
        if (-not $SkipUI) {
            if ($uiJob.State -ne "Running") {
                Write-Status "Atlas UI job stopped unexpectedly" $ERR
                break
            }
        }
        
        # Periodic health check
        try {
            if (-not $SkipAPI) {
                $response = Invoke-WebRequest -Uri "http://localhost:5317/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
                if ($response.StatusCode -ne 200) {
                    Write-Status "Health check failed - API may be unresponsive" $WARN
                }
            }
        } catch {
            Write-Status "Health check failed - API may be down" $ERR
        }
    }
} catch {
    Write-Status "Shutting down production services..." $INFO
} finally {
    # Clean up jobs
    if (-not $SkipAPI -and $apiJob) {
        Stop-Job -Job $apiJob -ErrorAction SilentlyContinue
        Remove-Job -Job $apiJob -ErrorAction SilentlyContinue
    }
    
    if (-not $SkipUI -and $uiJob) {
        Stop-Job -Job $uiJob -ErrorAction SilentlyContinue
        Remove-Job -Job $uiJob -ErrorAction SilentlyContinue
    }
    
    Write-Status "All production services stopped" $CHECK
}