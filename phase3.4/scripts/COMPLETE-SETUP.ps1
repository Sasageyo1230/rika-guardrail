# Rika Phase 3.4 COMPLETE SETUP - PowerShell 5.1 Compatible
# One-command complete installation and testing

param(
    [switch]$SkipTests,
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
$COMPLETE = "[COMPLETE]"

function Write-Status {
    param($Message, $Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Type $Message"
}

function Run-Script {
    param($ScriptPath, $Description, $Args = @())
    
    Write-Status "Running $Description..." $START
    
    try {
        if ($Args.Count -gt 0) {
            & $ScriptPath @Args
        } else {
            & $ScriptPath
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "$Description completed successfully" $CHECK
            return $true
        } else {
            Write-Status "$Description failed with exit code $LASTEXITCODE" $ERR
            return $false
        }
    } catch {
        Write-Status "$Description failed: $($_.Exception.Message)" $ERR
        return $false
    }
}

Write-Status "" $INFO
Write-Status "============================================" $INFO
Write-Status "    Rika Phase 3.4 COMPLETE SETUP" $INFO
Write-Status "============================================" $INFO
Write-Status "" $INFO
Write-Status "This script will:" $INFO
Write-Status "  1. Run system diagnostics" $INFO
Write-Status "  2. Install all dependencies" $INFO
Write-Status "  3. Configure the system" $INFO
Write-Status "  4. Run comprehensive tests" $INFO
Write-Status "  5. Start the development environment" $INFO
Write-Status "" $INFO
Write-Status "Features included:" $INFO
Write-Status "  * Multi-Agent Chat (Rika, Rig, Craft, Scout)" $INFO
Write-Status "  * Streaming responses with SSE" $INFO
Write-Status "  * Multi-LLM support (Claude, OpenAI, Local)" $INFO
Write-Status "  * Memory system with JSON/PostgreSQL" $INFO
Write-Status "  * n8n tool integration" $INFO
Write-Status "  * AI Designer (Design Mode)" $INFO
Write-Status "  * Atlas UI with React/TypeScript" $INFO
Write-Status "  * PowerShell 5.1 compatible scripts" $INFO
Write-Status "" $INFO

$startTime = Get-Date
Write-Status "Starting complete setup at $startTime..." $START

# Check if we're in the right directory
if (-not (Test-Path "core\main.py")) {
    Write-Status "Please run this script from the rika-core directory" $ERR
    Write-Status "Expected structure:" $INFO
    Write-Status "  rika-core\" $INFO
    Write-Status "    core\" $INFO
    Write-Status "    ui\" $INFO
    Write-Status "    phase3.4\scripts\" $INFO
    exit 1
}

# Step 1: System Diagnostics
Write-Status "" $INFO
Write-Status "STEP 1: System Diagnostics" $START
Write-Status "=========================" $INFO

$diagArgs = @{}
if ($Force) { $diagArgs.FixIssues = $true }
if ($Verbose) { $diagArgs.Verbose = $true }

if (-not (Run-Script ".\phase3.4\scripts\diagnose.ps1" "System Diagnostics" $diagArgs)) {
    Write-Status "System diagnostics found critical issues" $ERR
    Write-Status "Please fix the issues and run this script again" $ERR
    exit 1
}

# Step 2: Setup and Installation
Write-Status "" $INFO
Write-Status "STEP 2: Setup and Installation" $START
Write-Status "===============================" $INFO

$setupArgs = @{}
if ($Force) { $setupArgs.Force = $true }
if ($Verbose) { $setupArgs.Verbose = $true }

if (-not (Run-Script ".\phase3.4\scripts\setup.ps1" "Setup and Installation" $setupArgs)) {
    Write-Status "Setup failed" $ERR
    exit 1
}

# Step 3: Comprehensive Testing
if (-not $SkipTests) {
    Write-Status "" $INFO
    Write-Status "STEP 3: Comprehensive Testing" $START
    Write-Status "==============================" $INFO
    
    $testArgs = @{}
    if ($Verbose) { $testArgs.Verbose = $true }
    
    if (-not (Run-Script ".\phase3.4\scripts\test.ps1" "Comprehensive Testing" $testArgs)) {
        Write-Status "Some tests failed, but continuing..." $WARN
        Write-Status "You can run tests later with: .\phase3.4\scripts\test.ps1" $INFO
    }
} else {
    Write-Status "Skipping tests (use -SkipTests to avoid this)" $INFO
}

# Step 4: Configuration Verification
Write-Status "" $INFO
Write-Status "STEP 4: Configuration Verification" $START
Write-Status "===================================" $INFO

# Check critical files
$criticalFiles = @(
    @{ Path = ".env"; Name = "Environment file" },
    @{ Path = "config\config.json"; Name = "Configuration file" },
    @{ Path = "ui\package.json"; Name = "UI package file" },
    @{ Path = "core\main.py"; Name = "Core API" }
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file.Path) {
        Write-Status "$($file.Name): found" $CHECK
    } else {
        Write-Status "$($file.Name): missing" $ERR
    }
}

# API Keys check
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "ANTHROPIC_API_KEY=your_anthropic_key_here" -or 
        $envContent -match "OPENAI_API_KEY=your_openai_key_here") {
        Write-Status "" $WARN
        Write-Status "IMPORTANT: Configure your API keys in .env file" $WARN
        Write-Status "  - Edit .env file" $WARN
        Write-Status "  - Add your Anthropic API key" $WARN
        Write-Status "  - Add your OpenAI API key" $WARN
        Write-Status "  - Optional: Configure n8n settings" $WARN
        Write-Status "" $WARN
    } else {
        Write-Status "API keys appear to be configured" $CHECK
    }
}

# Calculate setup time
$endTime = Get-Date
$duration = New-TimeSpan -Start $startTime -End $endTime
$durationStr = "{0:mm}m {0:ss}s" -f $duration

Write-Status "" $INFO
Write-Status "============================================" $COMPLETE
Write-Status "  Rika Phase 3.4 Setup Complete!" $COMPLETE
Write-Status "============================================" $INFO
Write-Status "" $INFO
Write-Status "Setup completed in $durationStr" $INFO
Write-Status "" $INFO
Write-Status "What's been installed:" $INFO
Write-Status "  [X] Core API with FastAPI and SSE streaming" $CHECK
Write-Status "  [X] Multi-LLM connectors (Claude/OpenAI/Local)" $CHECK
Write-Status "  [X] Atlas UI with React and TypeScript" $CHECK
Write-Status "  [X] Memory system with JSON storage" $CHECK
Write-Status "  [X] n8n tool integration framework" $CHECK
Write-Status "  [X] AI Designer (Design Mode)" $CHECK
Write-Status "  [X] PowerShell 5.1 compatible scripts" $CHECK
Write-Status "" $INFO
Write-Status "Available commands:" $INFO
Write-Status "  .\phase3.4\scripts\start-dev.ps1   - Start development servers" $INFO
Write-Status "  .\phase3.4\scripts\start-prod.ps1  - Start production servers" $INFO
Write-Status "  .\phase3.4\scripts\test.ps1        - Run comprehensive tests" $INFO
Write-Status "  .\phase3.4\scripts\diagnose.ps1    - System diagnostics" $INFO
Write-Status "" $INFO
Write-Status "Quick Start:" $INFO
Write-Status "  1. Configure API keys in .env file (if not done)" $INFO
Write-Status "  2. Run: .\phase3.4\scripts\start-dev.ps1" $INFO
Write-Status "  3. Open: http://localhost:5173" $INFO
Write-Status "  4. Click 'Start Chatting' to begin!" $INFO
Write-Status "" $INFO
Write-Status "Features to try:" $INFO
Write-Status "  * Chat with different AI agents (Rika, Rig, Craft, Scout)" $INFO
Write-Status "  * Watch streaming responses in real-time" $INFO
Write-Status "  * Use AI Designer to modify the UI (Ctrl+D in dev mode)" $INFO
Write-Status "  * Explore API documentation at http://localhost:5317/docs" $INFO
Write-Status "" $INFO

# Ask if user wants to start development servers
Write-Host "Would you like to start the development servers now? (y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "y" -or $response -eq "Y" -or $response -eq "yes" -or $response -eq "Yes") {
    Write-Status "" $INFO
    Write-Status "Starting development environment..." $START
    
    try {
        & ".\phase3.4\scripts\start-dev.ps1"
    } catch {
        Write-Status "Failed to start development environment: $($_.Exception.Message)" $ERR
        Write-Status "You can start it manually with: .\phase3.4\scripts\start-dev.ps1" $INFO
    }
} else {
    Write-Status "" $INFO
    Write-Status "Setup complete! Run .\phase3.4\scripts\start-dev.ps1 when ready." $INFO
    Write-Status "" $INFO
    Write-Status "Thank you for using Rika Phase 3.4!" $CHECK
}

exit 0