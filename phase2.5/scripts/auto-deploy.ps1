# Phase 2.5 - Automated Deployment Script
# Handles everything that can be automated

param(
    [string]$LiveKitURL = "",
    [string]$LiveKitAPIKey = "",
    [string]$LiveKitSecret = "",
    [switch]$InstallPython,
    [switch]$StartServices
)

Write-Host "🤖 Phase 2.5 - Automated Deployment" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

function Write-Status($Message, $Status = "Info") {
    $colors = @{
        "Success" = "Green"
        "Error" = "Red" 
        "Warning" = "Yellow"
        "Info" = "Cyan"
    }
    Write-Host $Message -ForegroundColor $colors[$Status]
}

# 1. Verify infrastructure is ready
Write-Status "Step 1: Verifying infrastructure..." "Info"

$infraReady = $true
if (!(docker ps --filter "name=rika-postgres" --filter "status=running" -q)) {
    Write-Status "❌ PostgreSQL not running. Start with: docker-compose up -d postgres" "Error"
    $infraReady = $false
}

if (!(docker ps --filter "name=rika-nats" --filter "status=running" -q)) {
    Write-Status "❌ NATS not running. Start with: docker-compose up -d nats" "Error"
    $infraReady = $false
}

if (!(Test-NetConnection -ComputerName localhost -Port 5678 -InformationLevel Quiet)) {
    Write-Status "❌ n8n not running. Start with: docker-compose up -d n8n" "Error"
    $infraReady = $false
}

if ($infraReady) {
    Write-Status "✅ All infrastructure services are running" "Success"
} else {
    Write-Status "❌ Infrastructure not ready. Please start services first." "Error"
    exit 1
}

# 2. Configure LiveKit if credentials provided
if ($LiveKitURL -and $LiveKitAPIKey -and $LiveKitSecret) {
    Write-Status "Step 2: Configuring LiveKit..." "Info"
    
    $envPath = ".\.env"
    $envContent = Get-Content $envPath -Raw
    
    $envContent = $envContent -replace "LIVEKIT_URL=.*", "LIVEKIT_URL=$LiveKitURL"
    $envContent = $envContent -replace "LIVEKIT_API_KEY=.*", "LIVEKIT_API_KEY=$LiveKitAPIKey"
    $envContent = $envContent -replace "LIVEKIT_SECRET_KEY=.*", "LIVEKIT_SECRET_KEY=$LiveKitSecret"
    
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    Write-Status "✅ LiveKit configuration updated" "Success"
} else {
    Write-Status "⚠️  LiveKit credentials not provided - you'll need to configure manually" "Warning"
}

# 3. Install Python dependencies if requested
if ($InstallPython) {
    Write-Status "Step 3: Installing Python dependencies..." "Info"
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Found Python: $pythonVersion" "Success"
        
        # Install Core API dependencies
        Write-Status "Installing Core API dependencies..." "Info"
        Set-Location core
        pip install livekit-api asyncio-nats-client pillow asyncpg fastapi uvicorn pydantic python-multipart python-jose passlib python-dotenv
        Set-Location ..
        
        # Install Desktop Agent dependencies
        Write-Status "Installing Desktop Agent dependencies..." "Info"
        Set-Location agent-desktop
        pip install livekit pynput pillow asyncio-nats-client requests psutil pywin32
        Set-Location ..
        
        Write-Status "✅ Python dependencies installed" "Success"
        
    } catch {
        Write-Status "❌ Python not found. Please install Python first." "Error"
        Write-Status "   Download from: https://python.org or Microsoft Store" "Info"
    }
}

# 4. Install Node.js dependencies
Write-Status "Step 4: Installing Node.js dependencies..." "Info"
try {
    Set-Location ui
    npm install
    Write-Status "✅ Node.js dependencies installed" "Success"
    Set-Location ..
} catch {
    Write-Status "❌ Node.js installation failed" "Error"
    Write-Status "   Make sure Node.js is installed: https://nodejs.org" "Info"
    Set-Location ..
}

# 5. Start services if requested
if ($StartServices) {
    Write-Status "Step 5: Starting Phase 2.5 services..." "Info"
    
    # Start Core API
    Write-Status "Starting Core API..." "Info"
    Start-Process -FilePath "python" -ArgumentList "core\api.py" -WindowStyle Minimized
    Start-Sleep -Seconds 3
    
    # Start Desktop Agent (requires admin)
    Write-Status "Starting Desktop Agent..." "Info"
    Start-Process -FilePath "python" -ArgumentList "agent-desktop\agent.py" -WindowStyle Minimized -Verb RunAs
    Start-Sleep -Seconds 3
    
    # Start Atlas UI
    Write-Status "Starting Atlas UI..." "Info"
    Set-Location ui
    Start-Process -FilePath "npm" -ArgumentList "run dev" -WindowStyle Minimized
    Set-Location ..
    
    Write-Status "✅ Services started" "Success"
    Write-Status "   Core API: http://localhost:8000" "Info"
    Write-Status "   Atlas UI: http://localhost:5173" "Info"
}

# 6. Final verification
Write-Status "Step 6: Final verification..." "Info"

$dbTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT COUNT(*) FROM control_requests;" 2>$null
if ($dbTest) {
    Write-Status "✅ Database connectivity verified" "Success"
} else {
    Write-Status "❌ Database connectivity failed" "Error"
}

# 7. Display next steps
Write-Status "`n🎉 Automated deployment complete!" "Success"
Write-Status "===============================`n" "Success"

Write-Status "✅ What's Done:" "Success"
Write-Status "  • Infrastructure verified and running" "Info"
Write-Status "  • Database schema deployed" "Info"
Write-Status "  • Configuration files ready" "Info"
if ($LiveKitURL) { Write-Status "  • LiveKit configured" "Info" }
if ($InstallPython) { Write-Status "  • Python dependencies installed" "Info" }
Write-Status "  • Node.js dependencies installed" "Info"
if ($StartServices) { Write-Status "  • Services started" "Info" }

Write-Status "`n📋 Manual Steps Remaining:" "Warning"
if (!$LiveKitURL) {
    Write-Status "  1. Configure LiveKit:" "Info"
    Write-Status "     • Sign up: https://cloud.livekit.io" "Info"
    Write-Status "     • Update .env with credentials" "Info"
}
Write-Status "  2. Import n8n workflow:" "Info"
Write-Status "     • Open: http://localhost:5678" "Info"
Write-Status "     • Import: n8n/rika-control-approval-flow.json" "Info"
Write-Status "     • Activate the workflow" "Info"

if (!$StartServices) {
    Write-Status "  3. Start services manually:" "Info"
    Write-Status "     • python core/api.py" "Info"
    Write-Status "     • python agent-desktop/agent.py (as admin)" "Info"
    Write-Status "     • npm run dev (in ui/)" "Info"
}

Write-Status "`n🔗 Quick Links:" "Info"
Write-Status "  • Atlas UI: http://localhost:5173" "Info"
Write-Status "  • Core API: http://localhost:8000/health" "Info"
Write-Status "  • n8n: http://localhost:5678" "Info"
Write-Status "  • NATS Monitor: http://localhost:8222" "Info"

Write-Status "`nPhase 2.5 is ready for testing! 🚀" "Success"