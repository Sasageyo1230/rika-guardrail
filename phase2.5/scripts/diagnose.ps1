# phase2.5/scripts/diagnose.ps1
# Comprehensive diagnostics for Phase 2.5 deployment

param(
    [switch]$AutoFix,
    [int]$AlternativePort = 5318
)

Write-Host "🔍 Rika Phase 2.5 - Diagnostic Tool" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$results = @{}
$warnings = @()
$errors = @()

function Test-Port {
    param([string]$Host = "localhost", [int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName $Host -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return $connection
    } catch {
        return $false
    }
}

function Write-TestResult {
    param([string]$Test, [bool]$Passed, [string]$Details = "")
    $status = if ($Passed) { "✅" } else { "❌" }
    $color = if ($Passed) { "Green" } else { "Red" }
    Write-Host "$status $Test" -ForegroundColor $color
    if ($Details) {
        Write-Host "   $Details" -ForegroundColor Gray
    }
}

# Test 1: Core API Port
Write-Host "`n1. Testing Core API Port (5317)..." -ForegroundColor Yellow
$apiPortOpen = Test-Port -Port 5317
if ($apiPortOpen) {
    Write-TestResult "Port 5317 accessible" $true
    $results["port"] = "accessible"
} else {
    Write-TestResult "Port 5317 not accessible" $false "Core API may not be running"
    $results["port"] = "closed"
    $errors += "Core API not running on port 5317"
    
    # Check for process using port
    $portInUse = Get-NetTCPConnection -LocalPort 5317 -ErrorAction SilentlyContinue
    if ($portInUse) {
        $process = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "   Port is busy: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
        if ($AutoFix) {
            Write-Host "   Auto-fixing: Killing process..." -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force
        }
    } else {
        Write-Host "   Port is free - API server not started" -ForegroundColor Gray
        if ($AutoFix) {
            Write-Host "   Auto-fixing: Starting Core API..." -ForegroundColor Yellow
            Start-Process -FilePath "powershell" -ArgumentList "-File", "core/start-core.ps1" -WindowStyle Minimized
            Start-Sleep -Seconds 5
            $apiPortOpen = Test-Port -Port 5317
        }
    }
}

# Test 2: Health Check
Write-Host "`n2. Testing Core API Health..." -ForegroundColor Yellow
if ($apiPortOpen) {
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5317/health" -TimeoutSec 10
        Write-TestResult "Health endpoint responds" $true "Status: $($healthResponse.status)"
        $results["health"] = $healthResponse.status
    } catch {
        Write-TestResult "Health endpoint failed" $false $_.Exception.Message
        $results["health"] = "failed"
        $errors += "Health endpoint error: $($_.Exception.Message)"
    }
} else {
    Write-TestResult "Health endpoint skipped" $false "Port not accessible"
    $results["health"] = "skipped"
}

# Test 3: Self Check
Write-Host "`n3. Testing Core API Self Check..." -ForegroundColor Yellow
if ($apiPortOpen) {
    try {
        $selfcheckResponse = Invoke-RestMethod -Uri "http://localhost:5317/selfcheck" -TimeoutSec 15
        Write-TestResult "Selfcheck endpoint responds" $true "Status: $($selfcheckResponse.status)"
        $results["selfcheck"] = $selfcheckResponse
        
        # Detail component status
        foreach ($component in $selfcheckResponse.components.PSObject.Properties) {
            $name = $component.Name
            $status = $component.Value.status
            $icon = if ($status -eq "healthy") { "✅" } else { "⚠️" }
            Write-Host "   $icon $name`: $status" -ForegroundColor $(if ($status -eq "healthy") { "Green" } else { "Yellow" })
        }
        
        if ($selfcheckResponse.warnings) {
            foreach ($warning in $selfcheckResponse.warnings) {
                Write-Host "   ⚠️ $warning" -ForegroundColor Yellow
                $warnings += $warning
            }
        }
    } catch {
        Write-TestResult "Selfcheck endpoint failed" $false $_.Exception.Message
        $results["selfcheck"] = "failed"
        $errors += "Selfcheck error: $($_.Exception.Message)"
    }
} else {
    Write-TestResult "Selfcheck endpoint skipped" $false "Port not accessible"
    $results["selfcheck"] = "skipped"
}

# Test 4: UI Environment
Write-Host "`n4. Testing UI Environment..." -ForegroundColor Yellow
if (Test-Path "ui\.env") {
    $envContent = Get-Content "ui\.env" -Raw
    $apiUrlMatch = $envContent | Select-String "VITE_API_BASE_URL=(.+)"
    if ($apiUrlMatch) {
        $configuredUrl = $apiUrlMatch.Matches[0].Groups[1].Value
        $correctUrl = $configuredUrl -eq "http://localhost:5317"
        Write-TestResult "UI .env file exists" $true "API URL: $configuredUrl"
        if (-not $correctUrl) {
            $warnings += "UI configured for different API URL: $configuredUrl"
        }
        $results["ui_env"] = "present"
    } else {
        Write-TestResult "UI .env missing API URL" $false
        $results["ui_env"] = "missing_api_url"
        $errors += "VITE_API_BASE_URL not configured in ui/.env"
    }
} else {
    Write-TestResult "UI .env file missing" $false "Create from .env.example"
    $results["ui_env"] = "missing"
    $errors += "ui/.env file not found"
    
    if ($AutoFix) {
        Write-Host "   Auto-fixing: Creating .env file..." -ForegroundColor Yellow
        Copy-Item "ui\.env.example" "ui\.env"
    }
}

# Test 5: Database Connectivity
Write-Host "`n5. Testing Database..." -ForegroundColor Yellow
$dbPortOpen = Test-Port -Port 5433
if ($dbPortOpen) {
    Write-TestResult "PostgreSQL port accessible" $true "Port 5433"
    try {
        # Test via Docker
        $dbTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT 'DB OK'" 2>$null
        if ($dbTest -match "DB OK") {
            Write-TestResult "Database query successful" $true
            $results["database"] = "healthy"
            
            # Test Phase 2.5 tables
            $tableTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT COUNT(*) FROM control_requests" 2>$null
            if ($tableTest) {
                Write-TestResult "Phase 2.5 tables present" $true
                $results["db_schema"] = "ready"
            } else {
                Write-TestResult "Phase 2.5 tables missing" $false
                $results["db_schema"] = "missing"
                $errors += "Phase 2.5 database schema not deployed"
            }
        } else {
            Write-TestResult "Database query failed" $false
            $results["database"] = "query_failed"
        }
    } catch {
        Write-TestResult "Database connection failed" $false $_.Exception.Message
        $results["database"] = "connection_failed"
        $errors += "Database connection error"
    }
} else {
    Write-TestResult "PostgreSQL port not accessible" $false "Port 5433"
    $results["database"] = "port_closed"
    $errors += "PostgreSQL not running on port 5433"
}

# Test 6: NATS
Write-Host "`n6. Testing NATS..." -ForegroundColor Yellow
$natsPortOpen = Test-Port -Port 4222
$natsMonitorOpen = Test-Port -Port 8222
if ($natsPortOpen) {
    Write-TestResult "NATS client port accessible" $true "Port 4222"
    $results["nats_client"] = "accessible"
} else {
    Write-TestResult "NATS client port not accessible" $false "Port 4222"
    $results["nats_client"] = "closed"
    $errors += "NATS not running on port 4222"
}

if ($natsMonitorOpen) {
    Write-TestResult "NATS monitor accessible" $true "Port 8222"
    $results["nats_monitor"] = "accessible"
    
    try {
        $natsInfo = Invoke-RestMethod -Uri "http://localhost:8222/varz" -TimeoutSec 5
        Write-Host "   NATS Version: $($natsInfo.version)" -ForegroundColor Gray
        Write-Host "   Connections: $($natsInfo.connections)" -ForegroundColor Gray
    } catch {
        Write-Host "   Monitor info unavailable" -ForegroundColor Gray
    }
} else {
    Write-TestResult "NATS monitor not accessible" $false "Port 8222"
    $results["nats_monitor"] = "closed"
    $warnings += "NATS monitor not accessible"
}

# Test 7: MinIO
Write-Host "`n7. Testing MinIO..." -ForegroundColor Yellow
$minioPortOpen = Test-Port -Port 9000
if ($minioPortOpen) {
    Write-TestResult "MinIO port accessible" $true "Port 9000"
    try {
        $minioHealth = Invoke-RestMethod -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 5
        Write-TestResult "MinIO health check" $true
        $results["minio"] = "healthy"
        
        # Test thumbnails bucket access
        try {
            $minioConsole = Test-Port -Port 9001
            if ($minioConsole) {
                Write-Host "   MinIO Console: http://localhost:9001" -ForegroundColor Gray
            }
        } catch {
            # Console test is optional
        }
    } catch {
        Write-TestResult "MinIO health failed" $false $_.Exception.Message
        $results["minio"] = "unhealthy"
        $errors += "MinIO health check failed"
    }
} else {
    Write-TestResult "MinIO port not accessible" $false "Port 9000"
    $results["minio"] = "port_closed"
    $errors += "MinIO not running on port 9000"
}

# Test 8: n8n
Write-Host "`n8. Testing n8n..." -ForegroundColor Yellow
$n8nPortOpen = Test-Port -Port 5678
if ($n8nPortOpen) {
    Write-TestResult "n8n port accessible" $true "Port 5678"
    try {
        $n8nHealth = Invoke-RestMethod -Uri "http://localhost:5678/healthz" -TimeoutSec 5
        Write-TestResult "n8n health check" $true
        $results["n8n"] = "healthy"
    } catch {
        # n8n may not have /healthz, try root
        try {
            $n8nRoot = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 5
            if ($n8nRoot.StatusCode -eq 200) {
                Write-TestResult "n8n web interface accessible" $true
                $results["n8n"] = "accessible"
            }
        } catch {
            Write-TestResult "n8n not responding" $false
            $results["n8n"] = "not_responding"
            $warnings += "n8n may not be fully started"
        }
    }
} else {
    Write-TestResult "n8n port not accessible" $false "Port 5678"
    $results["n8n"] = "port_closed"
    $errors += "n8n not running on port 5678"
}

# Summary
Write-Host "`n📊 Diagnostic Summary" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

$totalTests = 8
$passedTests = 0
$failedTests = 0

# Count status
foreach ($key in $results.Keys) {
    if ($results[$key] -in @("accessible", "healthy", "present", "ready")) {
        $passedTests++
    } else {
        $failedTests++
    }
}

Write-Host "Tests: $passedTests passed, $failedTests failed" -ForegroundColor $(if ($failedTests -eq 0) { "Green" } else { "Yellow" })

if ($errors.Count -gt 0) {
    Write-Host "`n❌ Critical Issues:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  • $error" -ForegroundColor Red
    }
}

if ($warnings.Count -gt 0) {
    Write-Host "`n⚠️  Warnings:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  • $warning" -ForegroundColor Yellow
    }
}

# Quick fixes
Write-Host "`n🔧 Quick Fixes:" -ForegroundColor Green
Write-Host "  • Start Core API: .\core\start-core.ps1" -ForegroundColor White
Write-Host "  • Start all services: docker-compose up -d" -ForegroundColor White
Write-Host "  • Test API: Invoke-WebRequest http://localhost:5317/health" -ForegroundColor White
Write-Host "  • Create UI env: Copy-Item ui\.env.example ui\.env" -ForegroundColor White

# Service URLs
Write-Host "`n🌐 Service URLs:" -ForegroundColor Green
Write-Host "  • Core API: http://localhost:5317" -ForegroundColor White
Write-Host "  • Atlas UI: http://localhost:5173" -ForegroundColor White
Write-Host "  • n8n: http://localhost:5678" -ForegroundColor White
Write-Host "  • MinIO Console: http://localhost:9001" -ForegroundColor White
Write-Host "  • NATS Monitor: http://localhost:8222" -ForegroundColor White
Write-Host "  • pgAdmin: http://localhost:5050" -ForegroundColor White

# Export results for automation
$results | ConvertTo-Json -Depth 3 | Out-File "diagnostic-results.json" -Encoding UTF8
Write-Host "Results saved to: diagnostic-results.json" -ForegroundColor Gray