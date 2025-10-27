# Phase 2.5 - Complete Deployment Script
# Run this script to finish the Phase 2.5 deployment

param(
    [string]$LiveKitURL = "",
    [string]$LiveKitAPIKey = "",
    [string]$LiveKitSecret = "",
    [switch]$SkipLiveKit
)

Write-Host "🚀 Rika Phase 2.5 - Final Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

function Write-Status($Message, $Status = "Info") {
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "White"
    }
    Write-Host $Message -ForegroundColor $colors[$Status]
}

# Check prerequisites
Write-Status "Checking prerequisites..." "Info"

$checks = @()
$checks += @{Name="PostgreSQL"; Check={docker ps --filter "name=rika-postgres" --filter "status=running" -q}}
$checks += @{Name="NATS"; Check={docker ps --filter "name=rika-nats" --filter "status=running" -q}}
$checks += @{Name="n8n"; Check={Test-NetConnection -ComputerName localhost -Port 5678 -InformationLevel Quiet}}

foreach ($check in $checks) {
    $result = & $check.Check
    if ($result) {
        Write-Status "✅ $($check.Name) is running" "Success"
    } else {
        Write-Status "❌ $($check.Name) is not running" "Error"
        Write-Status "   Please start services with: docker-compose up -d" "Warning"
        exit 1
    }
}

# Update LiveKit configuration if provided
if (-not $SkipLiveKit -and ($LiveKitURL -or $LiveKitAPIKey -or $LiveKitSecret)) {
    Write-Status "Updating LiveKit configuration..." "Info"
    
    $envPath = ".env"
    $envContent = Get-Content $envPath -Raw
    
    if ($LiveKitURL) {
        $envContent = $envContent -replace "LIVEKIT_URL=.*", "LIVEKIT_URL=$LiveKitURL"
        Write-Status "  ✅ LiveKit URL updated" "Success"
    }
    
    if ($LiveKitAPIKey) {
        $envContent = $envContent -replace "LIVEKIT_API_KEY=.*", "LIVEKIT_API_KEY=$LiveKitAPIKey"  
        Write-Status "  ✅ LiveKit API Key updated" "Success"
    }
    
    if ($LiveKitSecret) {
        $envContent = $envContent -replace "LIVEKIT_SECRET_KEY=.*", "LIVEKIT_SECRET_KEY=$LiveKitSecret"
        Write-Status "  ✅ LiveKit Secret updated" "Success"
    }
    
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
}

# Test database connectivity
Write-Status "Testing database connectivity..." "Info"
try {
    $dbTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT COUNT(*) FROM control_requests;" 2>$null
    if ($dbTest) {
        Write-Status "✅ Database connection successful" "Success"
    } else {
        Write-Status "❌ Database connection failed" "Error"
        exit 1
    }
} catch {
    Write-Status "❌ Database test failed: $($_.Exception.Message)" "Error"
    exit 1
}

# Test NATS connectivity
Write-Status "Testing NATS connectivity..." "Info"
try {
    $natsTest = Test-NetConnection -ComputerName localhost -Port 4222 -InformationLevel Quiet
    if ($natsTest) {
        Write-Status "✅ NATS connection successful" "Success"
    } else {
        Write-Status "❌ NATS connection failed" "Error"
        exit 1
    }
} catch {
    Write-Status "❌ NATS test failed" "Error"
    exit 1
}

# Display deployment summary
Write-Status "`n🎉 Phase 2.5 Deployment Complete!" "Success"
Write-Status "==================================" "Success"

Write-Status "`n📊 Service Status:" "Info"
Write-Status "  • PostgreSQL: http://localhost:5050 (pgAdmin)" "Info"
Write-Status "  • NATS Monitor: http://localhost:8222" "Info" 
Write-Status "  • n8n Workflows: http://localhost:5678" "Info"

Write-Status "`n📋 Next Steps:" "Info"
Write-Status "1. Install Python dependencies:" "Info"
Write-Status "   cd core && pip install -r requirements.txt" "Info"
Write-Status "   cd agent-desktop && pip install -r requirements.txt" "Info"

Write-Status "`n2. Install Node.js dependencies:" "Info"
Write-Status "   cd ui && npm install" "Info"

Write-Status "`n3. Import n8n workflow:" "Info"
Write-Status "   • Open http://localhost:5678" "Info"
Write-Status "   • Import: n8n/rika-control-approval-flow.json" "Info"
Write-Status "   • Activate the workflow" "Info"

Write-Status "`n4. Start Phase 2.5 services:" "Info"
Write-Status "   • Terminal 1: python core/api.py" "Info"
Write-Status "   • Terminal 2: python agent-desktop/agent.py" "Info"
Write-Status "   • Terminal 3: npm run dev (in ui/)" "Info"

Write-Status "`n5. Test deployment:" "Info"
Write-Status "   • Atlas UI: http://localhost:5173" "Info"
Write-Status "   • Core API: http://localhost:8000/health" "Info"

if (-not $SkipLiveKit -and -not ($LiveKitURL -and $LiveKitAPIKey -and $LiveKitSecret)) {
    Write-Status "`n⚠️  LiveKit Configuration Required:" "Warning"
    Write-Status "   1. Sign up at https://cloud.livekit.io" "Warning"
    Write-Status "   2. Get your project credentials" "Warning" 
    Write-Status "   3. Re-run: .\complete-deployment.ps1 -LiveKitURL 'wss://...' -LiveKitAPIKey '...' -LiveKitSecret '...'" "Warning"
}

Write-Status "`n🔗 Documentation:" "Info"
Write-Status "  • Setup Guide: docs/SETUP-GUIDE.md" "Info"
Write-Status "  • Testing: docs/TESTING-SCENARIOS.md" "Info"
Write-Status "  • NATS Protocols: docs/NATS-PROTOCOLS.md" "Info"

Write-Status "`n✨ Phase 2.5 is ready for testing!" "Success"