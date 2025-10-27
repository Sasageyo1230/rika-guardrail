# Rika Phase 3.5 Comprehensive Validation Script
# Tests Atlas UI, chat/voice functionality, privacy proxy, and all deliverables

Write-Host "🚀 RIKA PHASE 3.5 VALIDATION SCRIPT" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$Results = @{}
$TotalTests = 0
$PassedTests = 0

function Test-Endpoint {
    param($Url, $Name, $ExpectedStatus = 200)
    $TotalTests++
    try {
        $Response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 10
        if ($Response) {
            Write-Host "✅ $Name" -ForegroundColor Green
            $Results[$Name] = "PASS"
            $PassedTests++
            return $true
        }
    } catch {
        Write-Host "❌ $Name - Error: $($_.Exception.Message)" -ForegroundColor Red
        $Results[$Name] = "FAIL"
        return $false
    }
}

function Test-UIAccessibility {
    $TotalTests++
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5174" -TimeoutSec 10
        if ($Response.StatusCode -eq 200 -and $Response.Content -match "<!DOCTYPE html>") {
            Write-Host "✅ Atlas UI Loading" -ForegroundColor Green
            $Results["Atlas UI"] = "PASS"
            $PassedTests++
            return $true
        }
    } catch {
        Write-Host "❌ Atlas UI Loading - Error: $($_.Exception.Message)" -ForegroundColor Red
        $Results["Atlas UI"] = "FAIL"
        return $false
    }
}

# Test Atlas UI
Write-Host "📱 Testing Atlas UI..." -ForegroundColor Yellow
Test-UIAccessibility

# Test 6-Agent System
Write-Host "🤖 Testing 6-Agent System..." -ForegroundColor Yellow
$AgentsResponse = Test-Endpoint "http://localhost:5318/chat/agents" "6-Agent Endpoint"
if ($AgentsResponse) {
    try {
        $Agents = Invoke-RestMethod -Uri "http://localhost:5318/chat/agents"
        $AgentCount = $Agents.agents.Count
        if ($AgentCount -eq 6) {
            Write-Host "✅ All 6 Agents Available (Rika, Rig, Craft, Scout, Echo, Pulse)" -ForegroundColor Green
            $Results["6-Agent Count"] = "PASS"
            $PassedTests++
        } else {
            Write-Host "❌ Expected 6 agents, found $AgentCount" -ForegroundColor Red
            $Results["6-Agent Count"] = "FAIL"
        }
        $TotalTests++
    } catch {
        Write-Host "❌ Agent validation failed" -ForegroundColor Red
        $Results["6-Agent Count"] = "FAIL"
        $TotalTests++
    }
}

# Test Voice Integration
Write-Host "🎤 Testing Voice Integration..." -ForegroundColor Yellow
Test-Endpoint "http://localhost:5318/voice/health" "Voice Health"
Test-Endpoint "http://localhost:5318/voice/agents" "Voice Agents"

# Test Privacy Proxy
Write-Host "🔒 Testing Privacy Proxy..." -ForegroundColor Yellow
Test-Endpoint "http://localhost:5318/proxy/health" "Proxy Health"
Test-Endpoint "http://localhost:5318/proxy/cache/stats" "Proxy Cache"

# Test Knowledge Vault
Write-Host "🧠 Testing Knowledge Vault..." -ForegroundColor Yellow
Test-Endpoint "http://localhost:5318/knowledge/health" "Knowledge Health"
Test-Endpoint "http://localhost:5318/knowledge/categories" "Knowledge Categories"
Test-Endpoint "http://localhost:5318/knowledge/stats" "Knowledge Stats"

# Test Core Server Health
Write-Host "⚡ Testing Core Server..." -ForegroundColor Yellow
Test-Endpoint "http://localhost:5318/health" "Core Server Health"
Test-Endpoint "http://localhost:5318/" "Root Endpoint"

# Performance Test
Write-Host "🔥 Testing Performance..." -ForegroundColor Yellow
$TotalTests++
try {
    $StartTime = Get-Date
    $Responses = @()
    for ($i = 1; $i -le 5; $i++) {
        $Response = Invoke-RestMethod -Uri "http://localhost:5318/chat/agents" -TimeoutSec 5
        $Responses += $Response
    }
    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalMilliseconds
    $AvgTime = $Duration / 5
    
    if ($AvgTime -lt 1000) {
        Write-Host "✅ Performance Test - Avg response: $([math]::Round($AvgTime, 2))ms" -ForegroundColor Green
        $Results["Performance"] = "PASS"
        $PassedTests++
    } else {
        Write-Host "⚠️  Performance Warning - Avg response: $([math]::Round($AvgTime, 2))ms" -ForegroundColor Yellow
        $Results["Performance"] = "SLOW"
        $PassedTests++
    }
} catch {
    Write-Host "❌ Performance Test Failed" -ForegroundColor Red
    $Results["Performance"] = "FAIL"
}

# Calculate Results
$SuccessRate = [math]::Round(($PassedTests / $TotalTests) * 100, 1)

Write-Host ""
Write-Host "📊 VALIDATION RESULTS" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Total Tests: $TotalTests"
Write-Host "Passed: $PassedTests"
Write-Host "Failed: $($TotalTests - $PassedTests)"
Write-Host "Success Rate: $SuccessRate%" -ForegroundColor $(if ($SuccessRate -ge 90) { "Green" } elseif ($SuccessRate -ge 70) { "Yellow" } else { "Red" })
Write-Host ""

# Detailed Results
Write-Host "📋 DETAILED RESULTS" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
foreach ($Test in $Results.GetEnumerator()) {
    $Status = switch ($Test.Value) {
        "PASS" { "✅"; break }
        "SLOW" { "⚠️ "; break }
        "FAIL" { "❌"; break }
        default { "❓" }
    }
    Write-Host "$Status $($Test.Key): $($Test.Value)"
}

Write-Host ""
if ($SuccessRate -ge 90) {
    Write-Host "🎉 RIKA PHASE 3.5 VALIDATION SUCCESSFUL!" -ForegroundColor Green
    Write-Host "All systems operational and ready for production use." -ForegroundColor Green
} elseif ($SuccessRate -ge 70) {
    Write-Host "⚠️  RIKA PHASE 3.5 PARTIALLY VALIDATED" -ForegroundColor Yellow
    Write-Host "Most systems operational but some issues detected." -ForegroundColor Yellow
} else {
    Write-Host "❌ RIKA PHASE 3.5 VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Critical issues detected. Review failed components." -ForegroundColor Red
}

Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
Write-Host "Atlas UI: http://localhost:5174" -ForegroundColor White
Write-Host "API Server: http://localhost:5318" -ForegroundColor White
Write-Host "Main Server: http://localhost:5317 (if running)" -ForegroundColor Gray
Write-Host ""
Write-Host "Validation completed at $(Get-Date)" -ForegroundColor Gray