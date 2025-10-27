# Rika Phase 3.4 System Diagnostics - PowerShell 5.1 Compatible
# Comprehensive system health check and troubleshooting

param(
    [switch]$Detailed,
    [switch]$FixIssues,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# ASCII-safe status indicators
$CHECK = "[OK]"
$ERR = "[ERROR]"
$WARN = "[WARNING]"
$INFO = "[INFO]"
$START = "[START]"
$FIX = "[FIX]"

function Write-Status {
    param($Message, $Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Type $Message"
}

function Test-Command {
    param($CommandName)
    $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
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

function Test-PythonPackage {
    param($PackageName, $PythonCmd)
    try {
        & $PythonCmd -c "import $PackageName" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-DiskSpace {
    param($Path)
    try {
        $drive = Split-Path $Path -Qualifier
        $disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq $drive }
        if ($disk) {
            $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
            $totalGB = [math]::Round($disk.Size / 1GB, 2)
            return @{ Free = $freeGB; Total = $totalGB; Percent = [math]::Round(($freeGB / $totalGB) * 100, 1) }
        }
    } catch {
        return $null
    }
}

Write-Status "Starting Rika Phase 3.4 System Diagnostics..." $START
Write-Status "PowerShell Version: $($PSVersionTable.PSVersion)" $INFO

$issues = @()
$fixes = @()

# 1. System Requirements Check
Write-Status "Checking system requirements..." $INFO

# PowerShell version
if ($PSVersionTable.PSVersion.Major -ge 5) {
    Write-Status "PowerShell version check passed" $CHECK
} else {
    Write-Status "PowerShell version too old (need 5.0+)" $ERR
    $issues += "PowerShell version too old"
}

# Windows version
$windowsVersion = [System.Environment]::OSVersion.Version
Write-Status "Windows version: $windowsVersion" $INFO

# Disk space
$diskInfo = Get-DiskSpace (Get-Location).Path
if ($diskInfo) {
    Write-Status "Disk space: $($diskInfo.Free)GB free of $($diskInfo.Total)GB ($($diskInfo.Percent)%)" $INFO
    if ($diskInfo.Free -lt 1) {
        Write-Status "Low disk space warning" $WARN
        $issues += "Low disk space"
    }
} else {
    Write-Status "Could not check disk space" $WARN
}

# Memory
$memory = Get-WmiObject -Class Win32_ComputerSystem
$totalMemoryGB = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
Write-Status "Total system memory: ${totalMemoryGB}GB" $INFO
if ($totalMemoryGB -lt 4) {
    Write-Status "Low system memory (recommend 8GB+)" $WARN
    $issues += "Low system memory"
}

# 2. Python Environment Check
Write-Status "Checking Python environment..." $INFO

# Auto-detect Python
if ($env:VIRTUAL_ENV) {
    Write-Status "Virtual environment detected: $env:VIRTUAL_ENV" $CHECK
    $pythonCmd = "python"
} elseif (Test-Path "venv\Scripts\python.exe") {
    Write-Status "Local virtual environment found" $CHECK
    $pythonCmd = "venv\Scripts\python.exe"
} else {
    Write-Status "No virtual environment detected" $INFO
    $pythonCmd = "python"
}

# Test Python availability
if (Test-Command $pythonCmd) {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-Status "Python: $pythonVersion" $CHECK
    
    # Check Python version
    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = [int]$matches[3]
        
        if ($major -eq 3 -and $minor -ge 8) {
            Write-Status "Python version is compatible" $CHECK
        } elseif ($major -eq 3 -and $minor -lt 8) {
            Write-Status "Python version too old (need 3.8+)" $ERR
            $issues += "Python version too old"
        } elseif ($major -eq 2) {
            Write-Status "Python 2 detected, need Python 3.8+" $ERR
            $issues += "Python 2 detected"
        }
    }
} else {
    Write-Status "Python not found in PATH" $ERR
    $issues += "Python not found"
    
    if ($FixIssues) {
        Write-Status "Attempting to find Python installations..." $FIX
        $pythonPaths = @(
            "C:\Python*\python.exe",
            "C:\Program Files\Python*\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe"
        )
        
        foreach ($path in $pythonPaths) {
            $found = Get-ChildItem $path -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) {
                Write-Status "Found Python at: $($found.FullName)" $FIX
                $fixes += "Add $($found.Directory) to PATH"
                break
            }
        }
    }
}

# 3. Python Packages Check
if (Test-Command $pythonCmd) {
    Write-Status "Checking Python packages..." $INFO
    
    $requiredPackages = @(
        "fastapi", "uvicorn", "pydantic", "python-multipart", 
        "aiofiles", "anthropic", "openai", "httpx", "python-dotenv"
    )
    
    foreach ($package in $requiredPackages) {
        if (Test-PythonPackage $package $pythonCmd) {
            Write-Status "Package $package: installed" $CHECK
        } else {
            Write-Status "Package $package: missing" $ERR
            $issues += "Missing Python package: $package"
            
            if ($FixIssues) {
                Write-Status "Installing $package..." $FIX
                & $pythonCmd -m pip install $package
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "Successfully installed $package" $FIX
                    $fixes += "Installed $package"
                } else {
                    Write-Status "Failed to install $package" $ERR
                }
            }
        }
    }
}

# 4. Node.js Environment Check
Write-Status "Checking Node.js environment..." $INFO

if (Test-Command "node") {
    $nodeVersion = node --version
    Write-Status "Node.js: $nodeVersion" $CHECK
    
    # Check version
    if ($nodeVersion -match "v(\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        if ($major -ge 16) {
            Write-Status "Node.js version is compatible" $CHECK
        } else {
            Write-Status "Node.js version too old (need 16+)" $ERR
            $issues += "Node.js version too old"
        }
    }
} else {
    Write-Status "Node.js not found in PATH" $ERR
    $issues += "Node.js not found"
    
    if ($FixIssues) {
        Write-Status "Node.js installation required" $FIX
        $fixes += "Install Node.js from https://nodejs.org/"
    }
}

if (Test-Command "npm") {
    $npmVersion = npm --version
    Write-Status "npm: $npmVersion" $CHECK
} else {
    Write-Status "npm not found" $ERR
    $issues += "npm not found"
}

# 5. Project Structure Check
Write-Status "Checking project structure..." $INFO

$requiredFiles = @(
    "core\main.py",
    "core\config.py",
    "core\chat.py",
    "ui\package.json",
    "ui\src\App.tsx",
    "ui\src\main.tsx"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Status "File $file: exists" $CHECK
    } else {
        Write-Status "File $file: missing" $ERR
        $issues += "Missing file: $file"
    }
}

$requiredDirs = @(
    "core",
    "ui",
    "ui\src",
    "ui\src\components",
    "ui\src\services",
    "ui\src\types",
    "config",
    "phase3.4\scripts"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Status "Directory $dir: exists" $CHECK
    } else {
        Write-Status "Directory $dir: missing" $ERR
        $issues += "Missing directory: $dir"
        
        if ($FixIssues) {
            Write-Status "Creating directory $dir..." $FIX
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            $fixes += "Created directory $dir"
        }
    }
}

# 6. Configuration Check
Write-Status "Checking configuration..." $INFO

if (Test-Path ".env") {
    Write-Status ".env file: exists" $CHECK
    
    # Check for required environment variables
    $envContent = Get-Content ".env" -Raw
    $requiredEnvVars = @("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "API_HOST", "API_PORT")
    
    foreach ($var in $requiredEnvVars) {
        if ($envContent -match "^$var=") {
            Write-Status "Environment variable $var: configured" $CHECK
        } else {
            Write-Status "Environment variable $var: missing" $WARN
            $issues += "Missing environment variable: $var"
        }
    }
} else {
    Write-Status ".env file: missing" $ERR
    $issues += "Missing .env file"
    
    if ($FixIssues) {
        Write-Status "Would create .env file (run setup.ps1)" $FIX
        $fixes += "Run setup.ps1 to create .env file"
    }
}

if (Test-Path "config\config.json") {
    Write-Status "config.json: exists" $CHECK
    
    try {
        $config = Get-Content "config\config.json" | ConvertFrom-Json
        $requiredSections = @("llm", "memory", "tools", "ui")
        
        foreach ($section in $requiredSections) {
            if ($config.$section) {
                Write-Status "Config section $section: found" $CHECK
            } else {
                Write-Status "Config section $section: missing" $ERR
                $issues += "Missing config section: $section"
            }
        }
    } catch {
        Write-Status "config.json: invalid JSON" $ERR
        $issues += "Invalid config.json"
    }
} else {
    Write-Status "config.json: missing" $ERR
    $issues += "Missing config.json"
}

# 7. Network Connectivity Check
Write-Status "Checking network connectivity..." $INFO

# Test external connectivity
try {
    $response = Invoke-WebRequest -Uri "https://api.anthropic.com" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "Anthropic API connectivity: OK" $CHECK
} catch {
    Write-Status "Anthropic API connectivity: failed" $WARN
    $issues += "Cannot reach Anthropic API"
}

try {
    $response = Invoke-WebRequest -Uri "https://api.openai.com" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "OpenAI API connectivity: OK" $CHECK
} catch {
    Write-Status "OpenAI API connectivity: failed" $WARN
    $issues += "Cannot reach OpenAI API"
}

# 8. Port Availability Check
Write-Status "Checking port availability..." $INFO

$requiredPorts = @(5317, 5173)
foreach ($port in $requiredPorts) {
    if (Test-Port $port) {
        Write-Status "Port $port: in use" $WARN
        $issues += "Port $port is occupied"
        
        if ($FixIssues) {
            Write-Status "Attempting to free port $port..." $FIX
            $processes = netstat -ano | Select-String ":$port "
            foreach ($line in $processes) {
                if ($line -match "\s+(\d+)$") {
                    $pid = $matches[1]
                    try {
                        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-Status "Killing process $($process.ProcessName) (PID: $pid)" $FIX
                            Stop-Process -Id $pid -Force
                            $fixes += "Stopped process using port $port"
                        }
                    } catch {
                        Write-Status "Could not stop process $pid" $WARN
                    }
                }
            }
        }
    } else {
        Write-Status "Port $port: available" $CHECK
    }
}

# 9. UI Dependencies Check
if (Test-Path "ui\package.json") {
    Write-Status "Checking UI dependencies..." $INFO
    
    Push-Location "ui"
    try {
        if (Test-Path "node_modules") {
            Write-Status "node_modules: exists" $CHECK
            
            # Check if package-lock.json exists
            if (Test-Path "package-lock.json") {
                Write-Status "package-lock.json: exists" $CHECK
            } else {
                Write-Status "package-lock.json: missing (consider npm install)" $WARN
            }
        } else {
            Write-Status "node_modules: missing" $ERR
            $issues += "UI dependencies not installed"
            
            if ($FixIssues) {
                Write-Status "Installing UI dependencies..." $FIX
                npm install
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "UI dependencies installed successfully" $FIX
                    $fixes += "Installed UI dependencies"
                } else {
                    Write-Status "Failed to install UI dependencies" $ERR
                }
            }
        }
    } finally {
        Pop-Location
    }
}

# Summary
Write-Status "" $INFO
Write-Status "Diagnostic Summary" $START
Write-Status "=================" $INFO

if ($issues.Count -eq 0) {
    Write-Status "No issues detected! System appears ready." $CHECK
} else {
    Write-Status "Found $($issues.Count) issue(s):" $WARN
    foreach ($issue in $issues) {
        Write-Status "  - $issue" $ERR
    }
}

if ($fixes.Count -gt 0) {
    Write-Status "" $INFO
    Write-Status "Applied $($fixes.Count) fix(es):" $INFO
    foreach ($fix in $fixes) {
        Write-Status "  - $fix" $FIX
    }
}

Write-Status "" $INFO
Write-Status "Recommended Actions:" $INFO
if ($issues -contains "Python not found") {
    Write-Status "  1. Install Python 3.8+ from https://python.org" $INFO
}
if ($issues -contains "Node.js not found") {
    Write-Status "  2. Install Node.js 16+ from https://nodejs.org" $INFO
}
if ($issues -contains "Missing .env file" -or $issues -contains "Missing config.json") {
    Write-Status "  3. Run: .\phase3.4\scripts\setup.ps1" $INFO
}
if ($issues -like "*Missing Python package*") {
    Write-Status "  4. Run: python -m pip install <package-name>" $INFO
}
if ($issues -contains "UI dependencies not installed") {
    Write-Status "  5. Run: cd ui && npm install" $INFO
}

Write-Status "" $INFO
Write-Status "Next Steps:" $INFO
Write-Status "  - Run setup.ps1 if you haven't already" $INFO
Write-Status "  - Configure API keys in .env file" $INFO
Write-Status "  - Run start-dev.ps1 to test the system" $INFO
Write-Status "  - Run test.ps1 for comprehensive testing" $INFO

if ($issues.Count -eq 0) {
    exit 0
} else {
    exit 1
}