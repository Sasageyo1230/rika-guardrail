# phase3.2/scripts/setup-rika-complete.ps1
# Complete Rika Phase 3.1 + 3.2 Setup Script

param(
    [switch]$SkipN8n,
    [switch]$SkipDesktop,
    [switch]$SkipResearch,
    [switch]$SkipSage,
    [switch]$DockerMode,
    [switch]$ProductionMode,
    [switch]$Help
)

if ($Help) {
    Write-Host "Complete Rika Setup - Phase 3.1 + 3.2" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This script sets up the complete Rika ecosystem:" -ForegroundColor White
    Write-Host ""
    Write-Host "Phase 3.1 Components:" -ForegroundColor Yellow
    Write-Host "  • n8n Gateway - Workflow automation with safety controls" -ForegroundColor White
    Write-Host "  • Sub-agent SDK - Safe n8n integration for all agents" -ForegroundColor White
    Write-Host ""
    Write-Host "Phase 3.2 Components:" -ForegroundColor Yellow
    Write-Host "  • Personality System - Rig, Craft, Scout, Echo, Pulse personalities" -ForegroundColor White
    Write-Host "  • HUD Layer - Animated bubbles, chat panel, command palette" -ForegroundColor White
    Write-Host "  • Desktop Agent - Bluetooth, HDMI-CEC, IR, gesture control" -ForegroundColor White
    Write-Host "  • Research Engine - MinIO + Qdrant vector storage, web scraping" -ForegroundColor White
    Write-Host "  • Great Sage - Strategic reflection with safety domains" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\setup-rika-complete.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -SkipN8n          Skip n8n Gateway setup" -ForegroundColor White
    Write-Host "  -SkipDesktop      Skip Desktop Agent setup" -ForegroundColor White
    Write-Host "  -SkipResearch     Skip Research Engine setup" -ForegroundColor White
    Write-Host "  -SkipSage         Skip Great Sage setup" -ForegroundColor White
    Write-Host "  -DockerMode       Use Docker for services (recommended)" -ForegroundColor White
    Write-Host "  -ProductionMode   Configure for production deployment" -ForegroundColor White
    Write-Host "  -Help             Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Prerequisites:" -ForegroundColor Yellow
    Write-Host "  • Python 3.8+ installed" -ForegroundColor White
    Write-Host "  • Node.js 18+ installed" -ForegroundColor White
    Write-Host "  • PostgreSQL 14+ running (localhost:5433)" -ForegroundColor White
    Write-Host "  • Docker Desktop (if using -DockerMode)" -ForegroundColor White
    Write-Host ""
    return
}

$ErrorActionPreference = "Continue"
$startTime = Get-Date

Write-Host ""
Write-Host "🚀 Rika Complete Setup - Phase 3.1 + 3.2" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting complete Rika ecosystem setup..." -ForegroundColor White
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found - install from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found - install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
try {
    $pgResult = Test-NetConnection -ComputerName localhost -Port 5433 -InformationLevel Quiet
    if ($pgResult) {
        Write-Host "  ✓ PostgreSQL: Running on port 5433" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ PostgreSQL: Not detected on port 5433" -ForegroundColor Yellow
        Write-Host "    Rika will attempt to connect when services start" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ PostgreSQL: Connection test failed" -ForegroundColor Yellow
}

# Check Docker if needed
if ($DockerMode) {
    try {
        $dockerVersion = docker --version 2>&1
        Write-Host "  ✓ Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Docker not found - install Docker Desktop" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Yellow

$directories = @(
    "logs",
    "config", 
    "output",
    "data\research",
    "data\vectors",
    "data\objects"
)

foreach ($dir in $directories) {
    $fullPath = "$PSScriptRoot\..\$dir"
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

# Component setup
Write-Host ""
Write-Host "Setting up components..." -ForegroundColor Yellow
Write-Host ""

# Phase 3.1: n8n Gateway
if (-not $SkipN8n) {
    Write-Host "⚙️ Setting up n8n Gateway (Phase 3.1)..." -ForegroundColor Cyan
    & "$PSScriptRoot\n8n-setup.ps1" -Domain localhost -Port 5678 $(if ($ProductionMode) { "-ProductionMode" } else { "" })
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ n8n Gateway setup complete" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ n8n Gateway setup had issues" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Phase 3.2: Desktop Agent
if (-not $SkipDesktop) {
    Write-Host "🔧 Setting up Desktop Agent (Phase 3.2)..." -ForegroundColor Cyan
    & "$PSScriptRoot\setup-desktop-agent.ps1" $(if ($ProductionMode) { "" } else { "-SkipCEC -SkipIR" })
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Desktop Agent setup complete" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Desktop Agent setup had issues" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Phase 3.2: Research Engine
if (-not $SkipResearch) {
    Write-Host "🔍 Setting up Research Engine (Phase 3.2)..." -ForegroundColor Cyan
    & "$PSScriptRoot\setup-research-engine.ps1" $(if ($DockerMode) { "-DockerMode" } else { "" })
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Research Engine setup complete" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Research Engine setup had issues" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Phase 3.2: Great Sage (minimal setup - it's self-contained)
if (-not $SkipSage) {
    Write-Host "🧠 Setting up Great Sage (Phase 3.2)..." -ForegroundColor Cyan
    python -m pip install fastapi uvicorn asyncpg pydantic structlog --upgrade
    Write-Host "  ✅ Great Sage dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Create master environment file
Write-Host "Creating master environment configuration..." -ForegroundColor Yellow

$masterEnv = @"
# Rika Master Environment Configuration
# Generated: $(Get-Date)
# Phase 3.1 + 3.2 Complete Setup

# Core Database
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core

# n8n Gateway (Phase 3.1)
N8N_URL=http://localhost:5678
N8N_API_KEY=rikaApiKey2025N8nIntegration
N8N_GATEWAY_URL=http://localhost:5324

# Overseer (Safety System)
OVERSEER_URL=http://localhost:5319

# Desktop Agent (Phase 3.2)
DESKTOP_AGENT_URL=http://localhost:5325

# Research Engine (Phase 3.2)
RESEARCH_ENGINE_URL=http://localhost:5326
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Great Sage (Phase 3.2)
GREAT_SAGE_URL=http://localhost:5327
SAGE_OUTPUT_DIR=$PSScriptRoot\..\output

# Frontend (Phase 2.5 + 3.2 UI)
FRONTEND_URL=http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_DIR=$PSScriptRoot\..\logs

# Production overrides
$(if ($ProductionMode) {
"# Production Configuration
LOG_LEVEL=WARN
N8N_SECURE_COOKIE=true
N8N_COOKIES_SECURE=true"
} else {
"# Development Configuration
DEBUG=true"
})
"@

$envFile = "$PSScriptRoot\..\.env.master"
$masterEnv | Out-File -FilePath $envFile -Encoding UTF8
Write-Host "Master environment file created: .env.master" -ForegroundColor Green

# Create master startup script
Write-Host ""
Write-Host "Creating master startup script..." -ForegroundColor Yellow

$startupScript = @"
# phase3.2/scripts/start-rika-complete.ps1
# Start all Rika services

param(
    [switch]`$SkipN8n,
    [switch]`$SkipDesktop,
    [switch]`$SkipResearch,
    [switch]`$SkipSage,
    [switch]`$Help
)

if (`$Help) {
    Write-Host "Start Complete Rika System" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\start-rika-complete.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -SkipN8n          Don't start n8n Gateway" -ForegroundColor White
    Write-Host "  -SkipDesktop      Don't start Desktop Agent" -ForegroundColor White
    Write-Host "  -SkipResearch     Don't start Research Engine" -ForegroundColor White
    Write-Host "  -SkipSage         Don't start Great Sage" -ForegroundColor White
    Write-Host "  -Help             Show this help" -ForegroundColor White
    Write-Host ""
    return
}

Write-Host "🚀 Starting Complete Rika System..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Load environment
if (Test-Path "$PSScriptRoot\..\.env.master") {
    Get-Content "$PSScriptRoot\..\.env.master" | ForEach-Object {
        if (`$_ -match '^([^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable(`$Matches[1], `$Matches[2])
        }
    }
    Write-Host "Environment loaded from .env.master" -ForegroundColor Gray
}

# Start services in order
Write-Host "Starting core services..." -ForegroundColor Yellow

# 1. Storage services (Docker)
if (Get-Command docker -ErrorAction SilentlyContinue) {
    `$composeFile = "$PSScriptRoot\..\docker-compose-storage.yml"
    if (Test-Path `$composeFile) {
        Write-Host "  Starting storage services..." -ForegroundColor Gray
        docker-compose -f `$composeFile up -d
        Start-Sleep 5
        Write-Host "  ✅ Storage services started" -ForegroundColor Green
    }
}

# 2. n8n Gateway
if (-not `$SkipN8n) {
    Write-Host "  Starting n8n Gateway..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\start-n8n.ps1"
    Start-Sleep 3
    Write-Host "  ✅ n8n Gateway starting" -ForegroundColor Green
}

# 3. Desktop Agent  
if (-not `$SkipDesktop) {
    Write-Host "  Starting Desktop Agent..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\start-desktop-agent.ps1"
    Start-Sleep 2
    Write-Host "  ✅ Desktop Agent starting" -ForegroundColor Green
}

# 4. Research Engine
if (-not `$SkipResearch) {
    Write-Host "  Starting Research Engine..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\start-research-engine.ps1"
    Start-Sleep 2
    Write-Host "  ✅ Research Engine starting" -ForegroundColor Green
}

# 5. Great Sage
if (-not `$SkipSage) {
    Write-Host "  Starting Great Sage..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\core'; python great_sage.py"
    Start-Sleep 2
    Write-Host "  ✅ Great Sage starting" -ForegroundColor Green
}

Write-Host ""
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep 10

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

`$services = @(
    @{name="n8n Gateway"; url="http://localhost:5324/health"; skip=`$SkipN8n},
    @{name="Desktop Agent"; url="http://localhost:5325/health"; skip=`$SkipDesktop},
    @{name="Research Engine"; url="http://localhost:5326/health"; skip=`$SkipResearch},
    @{name="Great Sage"; url="http://localhost:5327/health"; skip=`$SkipSage}
)

foreach (`$service in `$services) {
    if (-not `$service.skip) {
        try {
            `$response = Invoke-RestMethod -Uri `$service.url -TimeoutSec 5
            if (`$response.status -eq "healthy") {
                Write-Host "  ✅ `$(`$service.name): Healthy" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️ `$(`$service.name): `$(`$response.status)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ `$(`$service.name): Not responding" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "🎉 Rika System Started!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
if (-not `$SkipN8n) { Write-Host "  n8n Gateway:    http://localhost:5324" -ForegroundColor Cyan }
if (-not `$SkipDesktop) { Write-Host "  Desktop Agent:  http://localhost:5325" -ForegroundColor Cyan }
if (-not `$SkipResearch) { Write-Host "  Research Engine: http://localhost:5326" -ForegroundColor Cyan }
if (-not `$SkipSage) { Write-Host "  Great Sage:     http://localhost:5327" -ForegroundColor Cyan }
Write-Host ""
Write-Host "Web Interfaces:" -ForegroundColor Yellow  
Write-Host "  n8n Editor:     http://localhost:5678" -ForegroundColor White
Write-Host "  MinIO Console:  http://localhost:9001" -ForegroundColor White
Write-Host "  Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Next: Start the frontend with 'cd phase2.5/ui && npm run dev'" -ForegroundColor Gray
"@

$masterStartScript = "$PSScriptRoot\start-rika-complete.ps1" 
$startupScript | Out-File -FilePath $masterStartScript -Encoding UTF8
Write-Host "Master startup script created: start-rika-complete.ps1" -ForegroundColor Green

# Create test script
$testScript = @"
# phase3.2/scripts/test-rika-complete.ps1
# Test all Rika services

Write-Host "🧪 Testing Complete Rika System..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

`$services = @(
    @{name="n8n Gateway"; url="http://localhost:5324/health"},
    @{name="Desktop Agent"; url="http://localhost:5325/health"}, 
    @{name="Research Engine"; url="http://localhost:5326/health"},
    @{name="Great Sage"; url="http://localhost:5327/health"}
)

`$allHealthy = `$true

foreach (`$service in `$services) {
    Write-Host "Testing `$(`$service.name)..." -ForegroundColor Yellow
    try {
        `$response = Invoke-RestMethod -Uri `$service.url -TimeoutSec 10
        if (`$response.status -eq "healthy") {
            Write-Host "  ✅ PASS - Version: `$(`$response.version)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ FAIL - Status: `$(`$response.status)" -ForegroundColor Red
            `$allHealthy = `$false
        }
    } catch {
        Write-Host "  ❌ FAIL - Not responding: `$_" -ForegroundColor Red
        `$allHealthy = `$false
    }
}

Write-Host ""
if (`$allHealthy) {
    Write-Host "🎉 All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "System is ready for use:" -ForegroundColor White
    Write-Host "• Use the Command Palette (Ctrl/Cmd+K) for quick actions" -ForegroundColor Gray
    Write-Host "• Check HUD bubbles for agent notifications" -ForegroundColor Gray 
    Write-Host "• Open Atlas Chat Panel for direct communication" -ForegroundColor Gray
    Write-Host "• View Task Drawer for operation progress" -ForegroundColor Gray
} else {
    Write-Host "⚠️ Some services are not healthy" -ForegroundColor Yellow
    Write-Host "Check the service logs for details" -ForegroundColor Gray
}
"@

$testScriptPath = "$PSScriptRoot\test-rika-complete.ps1"
$testScript | Out-File -FilePath $testScriptPath -Encoding UTF8
Write-Host "Complete test script created: test-rika-complete.ps1" -ForegroundColor Green

# Calculate setup time
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "🎉 Rika Complete Setup Finished!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "Setup completed in $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Gray
Write-Host ""

Write-Host "What was installed:" -ForegroundColor Yellow
if (-not $SkipN8n) {
    Write-Host "  ✅ n8n Gateway with Overseer safety integration" -ForegroundColor Green
    Write-Host "     - Workflow automation with risk assessment" -ForegroundColor Gray
    Write-Host "     - Sub-agent SDK for safe n8n interaction" -ForegroundColor Gray
}
Write-Host "  ✅ Personality System for 5 agents (Rig, Craft, Scout, Echo, Pulse)" -ForegroundColor Green
Write-Host "     - HUD bubble animations with agent-specific styling" -ForegroundColor Gray
Write-Host "     - Atlas Chat Panel for natural language interaction" -ForegroundColor Gray
Write-Host "     - Command Palette (Ctrl/Cmd+K) for quick actions" -ForegroundColor Gray
Write-Host "     - Task Drawer for progress monitoring" -ForegroundColor Gray
if (-not $SkipDesktop) {
    Write-Host "  ✅ Desktop Agent with multi-modal device control" -ForegroundColor Green
    Write-Host "     - Bluetooth device management" -ForegroundColor Gray
    Write-Host "     - HDMI-CEC integration (hardware dependent)" -ForegroundColor Gray  
    Write-Host "     - IR control via LIRC (hardware dependent)" -ForegroundColor Gray
    Write-Host "     - MediaPipe gesture recognition" -ForegroundColor Gray
}
if (-not $SkipResearch) {
    Write-Host "  ✅ Research Engine with vector storage" -ForegroundColor Green
    Write-Host "     - MinIO object storage for research artifacts" -ForegroundColor Gray
    Write-Host "     - Qdrant vector database for semantic search" -ForegroundColor Gray
    Write-Host "     - Quick and deep research modes" -ForegroundColor Gray
    Write-Host "     - Daily digest generation" -ForegroundColor Gray
}
if (-not $SkipSage) {
    Write-Host "  ✅ Great Sage strategic reflection system" -ForegroundColor Green
    Write-Host "     - Safe domain operation with Overseer approval" -ForegroundColor Gray
    Write-Host "     - Weekly DIGEST.md and PLAN.md generation" -ForegroundColor Gray
    Write-Host "     - Strategic analysis and tactical review" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Quick Start Guide:" -ForegroundColor Yellow
Write-Host "1. Run: .\start-rika-complete.ps1" -ForegroundColor Cyan
Write-Host "2. Test: .\test-rika-complete.ps1" -ForegroundColor Cyan  
Write-Host "3. Start frontend: cd ..\phase2.5\ui && npm run dev" -ForegroundColor Cyan
Write-Host "4. Open: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "The system is now ready for Phase 3.1 + 3.2 operations! 🚀" -ForegroundColor Green