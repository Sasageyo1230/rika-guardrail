# Rika Phase 3.4 Setup Script - PowerShell 5.1 Compatible
# Auto-installs all dependencies for the complete system

param(
    [switch]$Force,
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

function Test-Command {
    param($CommandName)
    $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Install-NodeDependencies {
    param($Path)
    
    if (-not (Test-Path $Path)) {
        Write-Status "Directory not found: $Path" $ERR
        return $false
    }
    
    Push-Location $Path
    try {
        if (Test-Path "package.json") {
            Write-Status "Installing Node dependencies in $Path..." $INFO
            npm install
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Node dependencies installed successfully" $CHECK
                return $true
            } else {
                Write-Status "npm install failed in $Path" $ERR
                return $false
            }
        } else {
            Write-Status "No package.json found in $Path" $WARN
            return $true
        }
    } finally {
        Pop-Location
    }
}

Write-Status "Starting Rika Phase 3.4 Complete Setup..." $START
Write-Status "PowerShell 5.1 Compatible - Zero venv activation issues" $INFO

# Check if we're in the right directory
if (-not (Test-Path "core\main.py")) {
    Write-Status "Please run this script from the rika-core directory" $ERR
    exit 1
}

# Check Python
if (-not (Test-Command "python")) {
    Write-Status "Python not found. Please install Python 3.8+ and add to PATH" $ERR
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Status "Found Python: $pythonVersion" $CHECK

# Check Node.js
if (-not (Test-Command "node")) {
    Write-Status "Node.js not found. Please install Node.js 16+ and add to PATH" $ERR
    exit 1
}

$nodeVersion = node --version
Write-Status "Found Node.js: $nodeVersion" $CHECK

# Check npm
if (-not (Test-Command "npm")) {
    Write-Status "npm not found. Please ensure Node.js installation includes npm" $ERR
    exit 1
}

$npmVersion = npm --version
Write-Status "Found npm: $npmVersion" $CHECK

# Auto-detect if we're already in a virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Status "Already in virtual environment: $env:VIRTUAL_ENV" $CHECK
    $useVenv = $false
} else {
    Write-Status "Not in virtual environment, will create one" $INFO
    $useVenv = $true
}

# Create virtual environment if needed
if ($useVenv) {
    if (Test-Path "venv") {
        if ($Force) {
            Write-Status "Removing existing virtual environment..." $WARN
            Remove-Item "venv" -Recurse -Force
        } else {
            Write-Status "Virtual environment already exists (use -Force to recreate)" $INFO
        }
    }
    
    if (-not (Test-Path "venv")) {
        Write-Status "Creating virtual environment..." $INFO
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Status "Failed to create virtual environment" $ERR
            exit 1
        }
        Write-Status "Virtual environment created" $CHECK
    }
}

# Install Python dependencies
Write-Status "Installing Python dependencies..." $INFO

$pythonPackages = @(
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "pydantic==2.5.0",
    "python-multipart==0.0.6",
    "aiofiles==23.2.1",
    "anthropic==0.8.0",
    "openai==1.3.0",
    "httpx==0.25.0",
    "psycopg2-binary==2.9.9",
    "python-dotenv==1.0.0"
)

foreach ($package in $pythonPackages) {
    Write-Status "Installing $package..." $INFO
    if ($useVenv) {
        & "venv\Scripts\python.exe" -m pip install $package
    } else {
        python -m pip install $package
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to install $package" $ERR
        exit 1
    }
}

Write-Status "Python dependencies installed successfully" $CHECK

# Install UI dependencies
Write-Status "Installing UI dependencies..." $INFO
if (-not (Install-NodeDependencies "ui")) {
    Write-Status "Failed to install UI dependencies" $ERR
    exit 1
}

# Create config directory and files
Write-Status "Setting up configuration..." $INFO

if (-not (Test-Path "config")) {
    New-Item -ItemType Directory -Path "config" | Out-Null
    Write-Status "Created config directory" $CHECK
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Status "Creating default .env file..." $INFO
    $envContent = @"
# Rika Phase 3.4 Environment Configuration

# API Configuration
API_HOST=0.0.0.0
API_PORT=5317
API_RELOAD=true

# LLM Providers
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
LOCAL_LLM_URL=http://localhost:11434

# Database (Optional)
DATABASE_URL=sqlite:///./rika.db

# n8n Integration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key_here

# Development
DEBUG=true
LOG_LEVEL=info
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Status "Created .env file - please configure your API keys" $CHECK
} else {
    Write-Status ".env file already exists" $INFO
}

# Create default config.json
$configPath = Join-Path "config" "config.json"
if (-not (Test-Path $configPath)) {
    Write-Status "Creating default config.json..." $INFO
    $configContent = @"
{
  "llm": {
    "default_provider": "anthropic",
    "providers": {
      "anthropic": {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4000
      },
      "openai": {
        "model": "gpt-4",
        "max_tokens": 4000
      },
      "local": {
        "model": "llama2:7b",
        "max_tokens": 4000
      }
    }
  },
  "memory": {
    "provider": "json",
    "max_history": 50
  },
  "tools": {
    "n8n": {
      "enabled": true,
      "timeout": 30
    }
  },
  "ui": {
    "design_mode_enabled": true,
    "auto_backup": true
  }
}
"@
    $configContent | Out-File -FilePath $configPath -Encoding UTF8
    Write-Status "Created config.json" $CHECK
} else {
    Write-Status "config.json already exists" $INFO
}

# Test the installation
Write-Status "Testing installation..." $INFO

# Test Core API
Write-Status "Testing Core API startup..." $INFO
$coreTestJob = Start-Job -ScriptBlock {
    param($useVenv)
    
    Set-Location "C:\Users\ebrig\rika-core\core"
    
    if ($useVenv) {
        & "..\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 5317 --timeout-keep-alive 1
    } else {
        python -m uvicorn main:app --host 0.0.0.0 --port 5317 --timeout-keep-alive 1
    }
} -ArgumentList $useVenv

Start-Sleep -Seconds 5

# Check if API is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5317/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Status "Core API test passed" $CHECK
    } else {
        Write-Status "Core API test failed - unexpected status code" $WARN
    }
} catch {
    Write-Status "Core API test failed - server not responding" $WARN
}

# Stop test job
Stop-Job -Job $coreTestJob -ErrorAction SilentlyContinue
Remove-Job -Job $coreTestJob -ErrorAction SilentlyContinue

# Test UI build
Write-Status "Testing UI build..." $INFO
Push-Location "ui"
try {
    npm run typecheck
    if ($LASTEXITCODE -eq 0) {
        Write-Status "UI typecheck passed" $CHECK
    } else {
        Write-Status "UI typecheck failed" $WARN
    }
} finally {
    Pop-Location
}

Write-Status "Setup complete!" $CHECK
Write-Status "" $INFO
Write-Status "Next steps:" $INFO
Write-Status "1. Configure your API keys in .env file" $INFO
Write-Status "2. Run: .\phase3.4\scripts\start-dev.ps1" $INFO
Write-Status "3. Open: http://localhost:5173" $INFO
Write-Status "" $INFO
Write-Status "Available commands:" $INFO
Write-Status "  .\phase3.4\scripts\start-dev.ps1  - Start development servers" $INFO
Write-Status "  .\phase3.4\scripts\start-prod.ps1 - Start production servers" $INFO
Write-Status "  .\phase3.4\scripts\test.ps1       - Run comprehensive tests" $INFO
Write-Status "  .\phase3.4\scripts\diagnose.ps1   - System diagnostics" $INFO