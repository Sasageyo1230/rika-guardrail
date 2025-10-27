# Rika Phase 2.5 - Dependency Installation Script
# This script installs all required dependencies for Phase 2.5

param(
    [switch]$SkipNATS,
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$Force
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

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Install-NATS {
    Write-ColoredOutput "📦 Installing NATS Server..." "Yellow"
    
    $natsVersion = "v2.9.22"
    $natsUrl = "https://github.com/nats-io/nats-server/releases/download/$natsVersion/nats-server-$natsVersion-windows-amd64.zip"
    $downloadPath = Join-Path $env:TEMP "nats-server.zip"
    $installPath = "C:\nats"
    
    try {
        # Download NATS
        Write-ColoredOutput "  Downloading NATS Server $natsVersion..." "Gray"
        Invoke-WebRequest -Uri $natsUrl -OutFile $downloadPath -UseBasicParsing
        
        # Extract NATS
        Write-ColoredOutput "  Extracting to $installPath..." "Gray"
        if (Test-Path $installPath) {
            Remove-Item $installPath -Recurse -Force
        }
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        Expand-Archive -Path $downloadPath -DestinationPath $installPath -Force
        
        # Move executable to root of install path
        $extractedPath = Get-ChildItem $installPath -Directory | Select-Object -First 1
        if ($extractedPath) {
            Get-ChildItem $extractedPath.FullName | Move-Item -Destination $installPath
            Remove-Item $extractedPath.FullName -Recurse -Force
        }
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
        if (-not $currentPath.Contains($installPath)) {
            Write-ColoredOutput "  Adding NATS to system PATH..." "Gray"
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$installPath", "Machine")
            $env:PATH += ";$installPath"
        }
        
        # Clean up
        Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
        
        # Test installation
        $natsExe = Join-Path $installPath "nats-server.exe"
        if (Test-Path $natsExe) {
            Write-ColoredOutput "  ✅ NATS Server installed successfully" "Green"
            & $natsExe --version
            return $true
        } else {
            Write-ColoredOutput "  ❌ NATS Server installation failed" "Red"
            return $false
        }
        
    } catch {
        Write-ColoredOutput "  ❌ NATS installation failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Install-PythonDependencies {
    Write-ColoredOutput "🐍 Installing Python Dependencies..." "Yellow"
    
    $rootPath = Split-Path -Parent $PSScriptRoot
    $success = $true
    
    # Core API dependencies
    Write-ColoredOutput "  Installing Core API dependencies..." "Gray"
    $coreApiPath = Join-Path $rootPath "core"
    Push-Location $coreApiPath
    
    try {
        $packages = @(
            "livekit-api==0.5.0",
            "asyncio-nats-client==0.11.5",
            "pillow==10.0.0",
            "asyncpg>=0.28.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.4.0",
            "python-multipart>=0.0.6",
            "python-jose>=3.3.0",
            "passlib>=1.7.4",
            "python-dotenv>=1.0.0"
        )
        
        foreach ($package in $packages) {
            Write-ColoredOutput "    Installing $package..." "DarkGray"
            $result = pip install $package 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ColoredOutput "    ❌ Failed to install $package" "Red"
                $success = $false
            }
        }
        
        if ($success) {
            Write-ColoredOutput "  ✅ Core API dependencies installed" "Green"
        }
        
    } catch {
        Write-ColoredOutput "  ❌ Core API dependency installation failed: $($_.Exception.Message)" "Red"
        $success = $false
    } finally {
        Pop-Location
    }
    
    # Desktop Agent dependencies
    Write-ColoredOutput "  Installing Desktop Agent dependencies..." "Gray"
    $agentPath = Join-Path $rootPath "agent-desktop"
    Push-Location $agentPath
    
    try {
        $packages = @(
            "livekit==0.9.0",
            "pynput==1.7.6",
            "pillow==10.0.0",
            "asyncio-nats-client==0.11.5",
            "requests>=2.31.0",
            "psutil>=5.9.0",
            "pywin32>=306"
        )
        
        foreach ($package in $packages) {
            Write-ColoredOutput "    Installing $package..." "DarkGray"
            $result = pip install $package 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ColoredOutput "    ❌ Failed to install $package" "Red"
                $success = $false
            }
        }
        
        if ($success) {
            Write-ColoredOutput "  ✅ Desktop Agent dependencies installed" "Green"
        }
        
        # Test pynput (requires admin rights)
        if (Test-Administrator) {
            Write-ColoredOutput "  Testing pynput (requires admin rights)..." "Gray"
            $testResult = python -c "from pynput import mouse, keyboard; print('pynput test OK')" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColoredOutput "  ✅ pynput test successful" "Green"
            } else {
                Write-ColoredOutput "  ⚠️  pynput test failed - antivirus may be blocking" "Yellow"
            }
        } else {
            Write-ColoredOutput "  ⚠️  Cannot test pynput (requires admin rights)" "Yellow"
        }
        
    } catch {
        Write-ColoredOutput "  ❌ Desktop Agent dependency installation failed: $($_.Exception.Message)" "Red"
        $success = $false
    } finally {
        Pop-Location
    }
    
    return $success
}

function Install-NodeDependencies {
    Write-ColoredOutput "📦 Installing Node.js Dependencies..." "Yellow"
    
    $rootPath = Split-Path -Parent $PSScriptRoot
    $uiPath = Join-Path $rootPath "ui"
    
    if (-not (Test-Path $uiPath)) {
        Write-ColoredOutput "  ❌ UI directory not found: $uiPath" "Red"
        return $false
    }
    
    Push-Location $uiPath
    
    try {
        # Check if package.json exists
        if (-not (Test-Path "package.json")) {
            Write-ColoredOutput "  ❌ package.json not found in UI directory" "Red"
            return $false
        }
        
        # Install base dependencies first
        Write-ColoredOutput "  Installing base dependencies..." "Gray"
        $result = npm install 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColoredOutput "  ❌ Failed to install base dependencies" "Red"
            Write-ColoredOutput "$result" "Red"
            return $false
        }
        
        # Install Phase 2.5 specific packages
        Write-ColoredOutput "  Installing Phase 2.5 specific packages..." "Gray"
        $phase25Packages = @(
            "livekit-client@1.15.0",
            "@livekit/components-react@1.4.0", 
            "lucide-react@0.263.1",
            "date-fns@2.30.0"
        )
        
        foreach ($package in $phase25Packages) {
            Write-ColoredOutput "    Installing $package..." "DarkGray"
            $result = npm install $package 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ColoredOutput "    ❌ Failed to install $package" "Red"
                return $false
            }
        }
        
        Write-ColoredOutput "  ✅ Node.js dependencies installed successfully" "Green"
        
        # Verify key packages
        Write-ColoredOutput "  Verifying installations..." "Gray"
        $verification = npm list livekit-client @livekit/components-react lucide-react date-fns 2>&1
        Write-ColoredOutput "$verification" "DarkGray"
        
        return $true
        
    } catch {
        Write-ColoredOutput "  ❌ Node.js dependency installation failed: $($_.Exception.Message)" "Red"
        return $false
    } finally {
        Pop-Location
    }
}

function Test-Prerequisites {
    Write-ColoredOutput "🔍 Checking Prerequisites..." "Yellow"
    
    $allGood = $true
    
    # Check Python
    if (Test-Command "python") {
        $pythonVersion = python --version 2>&1
        Write-ColoredOutput "  ✅ Python: $pythonVersion" "Green"
        
        # Check pip
        if (Test-Command "pip") {
            $pipVersion = pip --version 2>&1
            Write-ColoredOutput "  ✅ pip: $pipVersion" "Green"
        } else {
            Write-ColoredOutput "  ❌ pip not found" "Red"
            $allGood = $false
        }
    } else {
        Write-ColoredOutput "  ❌ Python not found" "Red"
        $allGood = $false
    }
    
    # Check Node.js
    if (Test-Command "node") {
        $nodeVersion = node --version 2>&1
        Write-ColoredOutput "  ✅ Node.js: $nodeVersion" "Green"
        
        # Check npm
        if (Test-Command "npm") {
            $npmVersion = npm --version 2>&1
            Write-ColoredOutput "  ✅ npm: $npmVersion" "Green"
        } else {
            Write-ColoredOutput "  ❌ npm not found" "Red"
            $allGood = $false
        }
    } else {
        Write-ColoredOutput "  ❌ Node.js not found" "Red"
        $allGood = $false
    }
    
    # Check Git
    if (Test-Command "git") {
        $gitVersion = git --version 2>&1
        Write-ColoredOutput "  ✅ Git: $gitVersion" "Green"
    } else {
        Write-ColoredOutput "  ⚠️  Git not found (optional)" "Yellow"
    }
    
    # Check PostgreSQL
    if (Test-Command "psql") {
        try {
            $pgVersion = psql --version 2>&1
            Write-ColoredOutput "  ✅ PostgreSQL client: $pgVersion" "Green"
        } catch {
            Write-ColoredOutput "  ⚠️  PostgreSQL client found but not responding" "Yellow"
        }
    } else {
        Write-ColoredOutput "  ⚠️  PostgreSQL client not found (psql)" "Yellow"
    }
    
    # Check admin rights
    if (Test-Administrator) {
        Write-ColoredOutput "  ✅ Running as Administrator" "Green"
    } else {
        Write-ColoredOutput "  ⚠️  Not running as Administrator (required for some features)" "Yellow"
    }
    
    return $allGood
}

function Create-DirectoryStructure {
    Write-ColoredOutput "📁 Creating Directory Structure..." "Yellow"
    
    $rootPath = Split-Path -Parent $PSScriptRoot
    $directories = @(
        "logs",
        "nats-data",
        "config",
        "core\logs",
        "agent-desktop\logs", 
        "ui\logs"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $rootPath $dir
        if (-not (Test-Path $fullPath)) {
            Write-ColoredOutput "  Creating $dir..." "Gray"
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        } else {
            Write-ColoredOutput "  ✅ $dir already exists" "DarkGray"
        }
    }
    
    Write-ColoredOutput "  ✅ Directory structure created" "Green"
}

function Install-DevTools {
    Write-ColoredOutput "🔧 Installing Development Tools..." "Yellow"
    
    # Check if chocolatey is available for optional tools
    if (Test-Command "choco") {
        Write-ColoredOutput "  Chocolatey found, installing optional tools..." "Gray"
        
        $tools = @(
            "curl",
            "jq",
            "netstat"
        )
        
        foreach ($tool in $tools) {
            if (-not (Test-Command $tool)) {
                Write-ColoredOutput "  Installing $tool..." "DarkGray"
                choco install $tool -y 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-ColoredOutput "  ✅ $tool installed" "Green"
                } else {
                    Write-ColoredOutput "  ⚠️  $tool installation failed" "Yellow"
                }
            } else {
                Write-ColoredOutput "  ✅ $tool already available" "DarkGray"
            }
        }
    } else {
        Write-ColoredOutput "  Chocolatey not found, skipping optional tools" "Gray"
    }
}

# Main installation process
Write-ColoredOutput "🚀 Rika Phase 2.5 - Dependency Installation" "Cyan"
Write-ColoredOutput "===========================================" "Cyan"

# Check prerequisites
$prereqsOk = Test-Prerequisites
if (-not $prereqsOk -and -not $Force) {
    Write-ColoredOutput "" "White"
    Write-ColoredOutput "❌ Prerequisites not met. Install missing tools or use -Force to continue." "Red"
    exit 1
}

Write-ColoredOutput "" "White"

# Create directory structure
Create-DirectoryStructure

# Install NATS if not skipped
if (-not $SkipNATS) {
    if (Test-Command "nats-server") {
        Write-ColoredOutput "📦 NATS Server already installed" "Green"
        nats-server --version
    } else {
        if (-not (Test-Administrator)) {
            Write-ColoredOutput "❌ Administrator privileges required to install NATS Server" "Red"
            Write-ColoredOutput "   Run PowerShell as Administrator or use -SkipNATS" "Yellow"
            exit 1
        }
        
        $natsInstalled = Install-NATS
        if (-not $natsInstalled) {
            Write-ColoredOutput "❌ NATS installation failed" "Red"
            exit 1
        }
    }
} else {
    Write-ColoredOutput "⏭️  Skipping NATS installation" "Yellow"
}

Write-ColoredOutput "" "White"

# Install Python dependencies if not skipped
if (-not $SkipPython) {
    $pythonSuccess = Install-PythonDependencies
    if (-not $pythonSuccess) {
        Write-ColoredOutput "❌ Python dependency installation failed" "Red"
        exit 1
    }
} else {
    Write-ColoredOutput "⏭️  Skipping Python dependencies" "Yellow"
}

Write-ColoredOutput "" "White"

# Install Node.js dependencies if not skipped
if (-not $SkipNode) {
    $nodeSuccess = Install-NodeDependencies
    if (-not $nodeSuccess) {
        Write-ColoredOutput "❌ Node.js dependency installation failed" "Red"
        exit 1
    }
} else {
    Write-ColoredOutput "⏭️  Skipping Node.js dependencies" "Yellow"
}

Write-ColoredOutput "" "White"

# Install optional development tools
Install-DevTools

Write-ColoredOutput "" "White"
Write-ColoredOutput "✅ Phase 2.5 Dependencies Installation Complete!" "Green"
Write-ColoredOutput "" "White"

# Show next steps
Write-ColoredOutput "📋 Next Steps:" "Cyan"
Write-ColoredOutput "1. Configure your .env file with LiveKit and other credentials" "White"
Write-ColoredOutput "2. Run database migration: cd core; python migrate.py" "White"
Write-ColoredOutput "3. Import n8n workflow from n8n/rika-control-approval-flow.json" "White"
Write-ColoredOutput "4. Start services: .\scripts\start-all.ps1 start" "White"
Write-ColoredOutput "5. Test installation: .\scripts\start-all.ps1 status" "White"

Write-ColoredOutput "" "White"
Write-ColoredOutput "🔗 Useful Commands:" "Cyan"
Write-ColoredOutput ".\scripts\start-all.ps1 start    # Start all services" "White"
Write-ColoredOutput ".\scripts\start-all.ps1 status   # Check service status" "White"
Write-ColoredOutput ".\scripts\start-all.ps1 stop     # Stop all services" "White"
Write-ColoredOutput ".\scripts\start-all.ps1 logs     # View service logs" "White"

if (-not (Test-Administrator)) {
    Write-ColoredOutput "" "White"
    Write-ColoredOutput "⚠️  Note: Some features require Administrator privileges:" "Yellow"
    Write-ColoredOutput "   - Desktop Agent remote control (pynput)" "White"
    Write-ColoredOutput "   - NATS server installation" "White"
    Write-ColoredOutput "   - System-level service management" "White"
}