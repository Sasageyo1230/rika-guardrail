# Rika Phase 3.5 Simple Validation Script
Write-Host "RIKA PHASE 3.5 VALIDATION" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

$Tests = @()
$Pass = 0
$Total = 0

function Test-URL($Url, $Name) {
    $Total++
    try {
        $Response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
        Write-Host "[PASS] $Name" -ForegroundColor Green
        $Pass++
        return $true
    } catch {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        return $false
    }
}

# Test Atlas UI
$Total++
try {
    $UI = Invoke-WebRequest -Uri "http://localhost:5174" -TimeoutSec 10
    if ($UI.StatusCode -eq 200) {
        Write-Host "[PASS] Atlas UI Loading" -ForegroundColor Green
        $Pass++
    }
} catch {
    Write-Host "[FAIL] Atlas UI Loading" -ForegroundColor Red
}

# Test API Endpoints
Test-URL "http://localhost:5318/chat/agents" "6-Agent System"
Test-URL "http://localhost:5318/voice/health" "Voice Integration"
Test-URL "http://localhost:5318/proxy/health" "Privacy Proxy"
Test-URL "http://localhost:5318/knowledge/health" "Knowledge Vault"
Test-URL "http://localhost:5318/health" "Core Server"

# Check Agent Count
try {
    $Agents = Invoke-RestMethod -Uri "http://localhost:5318/chat/agents"
    $Count = $Agents.agents.Count
    $Total++
    if ($Count -eq 6) {
        Write-Host "[PASS] 6 Agents Available ($Count)" -ForegroundColor Green
        $Pass++
    } else {
        Write-Host "[FAIL] Expected 6 agents, found $Count" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Agent count validation" -ForegroundColor Red
    $Total++
}

$SuccessRate = [math]::Round(($Pass / $Total) * 100, 1)

Write-Host ""
Write-Host "RESULTS: $Pass/$Total passed ($SuccessRate%)" -ForegroundColor $(if ($SuccessRate -ge 90) { "Green" } else { "Yellow" })

if ($SuccessRate -ge 90) {
    Write-Host "SUCCESS: All systems operational!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Some systems need attention" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Atlas UI: http://localhost:5174"
Write-Host "API Server: http://localhost:5318"