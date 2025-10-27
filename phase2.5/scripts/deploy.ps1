# Rika Phase 2.5 - Simple Deployment Script
param(
    [switch]$Force
)

Write-Host "Rika Phase 2.5 - Deployment Starting..." -ForegroundColor Cyan

# Function to write colored output
function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-ColoredOutput "Python found: $pythonVersion" Green
} catch {
    Write-ColoredOutput "Python not found. Please install Python 3.9+" Red
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-ColoredOutput "Node.js found: $nodeVersion" Green
} catch {
    Write-ColoredOutput "Node.js not found. Please install Node.js 18+" Red
    exit 1
}

# Create directory structure
Write-ColoredOutput "Creating directory structure..." Yellow
$directories = @("logs", "nats-data", "config", "core\logs", "agent-desktop\logs", "ui\logs")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-ColoredOutput "  Created $dir" Gray
    }
}

# Install Python dependencies
Write-ColoredOutput "Installing Python dependencies..." Yellow
Set-Location core
pip install livekit-api asyncio-nats-client pillow asyncpg fastapi uvicorn pydantic python-multipart python-jose passlib python-dotenv
Set-Location ..

Set-Location agent-desktop  
pip install livekit pynput pillow asyncio-nats-client requests psutil pywin32
Set-Location ..

# Install Node.js dependencies
Write-ColoredOutput "Installing Node.js dependencies..." Yellow
Set-Location ui
npm install
npm install livekit-client @livekit/components-react lucide-react date-fns
Set-Location ..

Write-ColoredOutput "Phase 2.5 basic setup complete!" Green
Write-ColoredOutput "Next: Configure .env file and run services manually" White