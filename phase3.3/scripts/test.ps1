# Rika Phase 3.3 Service Health Check

param(
    [switch]$Verbose
)

# Build paths
$ScriptDir = $PSScriptRoot
$Phase33Root = Split-Path -Path $ScriptDir -Parent
$RikaRoot = Split-Path -Path $Phase33Root -Parent

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🔍 Rika Phase 3.3 - Service Health Check" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Service test definitions (only test if folder exists)
$serviceTests = @(
    @{
        Name = "Core API"
        Folder = "core"
        Port = 5317
        Tests = @(
            @{ Path = "/health"; Name = "Health" },
            @{ Path = "/selfcheck"; Name = "SelfCheck" }
        )
    },
    @{
        Name = "Overseer"
        Folder = "overseer"
        Port = 5319
        Tests = @(
            @{ Path = "/health"; Name = "Health" },
            @{ Path = "/status"; Name = "Status" }
        )
    },
    @{
        Name = "Great Sage"
        Folder = "great_sage"
        Port = 5320
        Tests = @(
            @{ Path = "/health"; Name = "Health" },
            @{ Path = "/status"; Name = "Status" }
        )
    },
    @{
        Name = "Research Vault"
        Folder = "research_vault"
        Port = 5321
        Tests = @(
            @{ Path = "/health"; Name = "Health" },
            @{ Path = "/status"; Name = "Status" }
        )
    },
    @{
        Name = "Atlas UI"
        Folder = "ui"
        Port = 5173
        Tests = @(
            @{ Path = "/"; Name = "Home" }
        )
    }
)

Write-Host "`nTesting services..." -ForegroundColor Yellow
Write-Host ("-" * 50) -ForegroundColor Gray

$results = @()
$totalPass = 0
$totalFail = 0
$totalSkip = 0

foreach ($service in $serviceTests) {
    $servicePath = Join-Path -Path $RikaRoot -ChildPath $service.Folder
    
    # Only test if service folder exists
    if (-not (Test-Path $servicePath)) {
        Write-Host "$($service.Name): SKIPPED (folder not found)" -ForegroundColor Gray
        $totalSkip++
        continue
    }
    
    Write-Host "$($service.Name) (port $($service.Port)):" -ForegroundColor Cyan
    
    $serviceResults = @()
    $servicePassed = $true
    
    foreach ($test in $service.Tests) {
        $url = "http://localhost:$($service.Port)$($test.Path)"
        
        if ($Verbose) {
            Write-Host "  🔗 Testing: $url" -ForegroundColor Gray
        }
        
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                Write-Host "  [OK] $($test.Name)" -ForegroundColor Green
                $serviceResults += @{ Test = $test.Name; Result = "PASS" }
                $totalPass++
            } else {
                Write-Host "  [WARNING] $($test.Name) (HTTP $($response.StatusCode))" -ForegroundColor Yellow
                $serviceResults += @{ Test = $test.Name; Result = "WARN" }
                $totalPass++  # Count warnings as passes for overall rate
            }
        } catch {
            Write-Host "  [ERROR] $($test.Name) (not responding)" -ForegroundColor Red
            $serviceResults += @{ Test = $test.Name; Result = "FAIL" }
            $servicePassed = $false
            $totalFail++
        }
    }
    
    $results += @{
        Service = $service.Name
        Port = $service.Port
        Tests = $serviceResults
        Passed = $servicePassed
    }
}

# Summary Table
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📊 Test Summary" -ForegroundColor White
Write-Host ("-" * 70) -ForegroundColor Gray

# Table header
Write-Host ("{0,-20} {1,-8} {2,-25} {3,-10}" -f "Service", "Port", "Tests", "Status") -ForegroundColor Yellow
Write-Host ("-" * 70) -ForegroundColor Gray

# Table rows
foreach ($result in $results) {
    $testSummary = ($result.Tests | ForEach-Object { $_.Result }) -join ", "
    $statusColor = if ($result.Passed) { "Green" } else { "Red" }
    $status = if ($result.Passed) { "[OK] PASS" } else { "[ERROR] FAIL" }
    
    Write-Host ("{0,-20} {1,-8} {2,-25} " -f $result.Service, $result.Port, $testSummary) -NoNewline
    Write-Host $status -ForegroundColor $statusColor
}

if ($totalSkip -gt 0) {
    Write-Host "`n- Skipped $totalSkip services (folders not found)" -ForegroundColor Gray
}

# Overall result
Write-Host ("-" * 70) -ForegroundColor Gray
$totalTests = $totalPass + $totalFail
if ($totalTests -gt 0) {
    $passRate = [math]::Round(($totalPass / $totalTests) * 100, 1)
    
    Write-Host "`n📈 Overall Status:" -ForegroundColor White
    Write-Host "  * Passed: $totalPass" -ForegroundColor Green
    Write-Host "  * Failed: $totalFail" -ForegroundColor Red
    Write-Host "  * Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 80) { "Green" } elseif ($passRate -ge 50) { "Yellow" } else { "Red" })
    
    if ($totalFail -eq 0) {
        Write-Host "`n🎉 All tests passed!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n[WARNING] Some tests failed" -ForegroundColor Yellow
        Write-Host "  Ensure services are running: .\start-dev.ps1" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "[FAIL] No services to test!" -ForegroundColor Yellow
    Write-Host "  Run .\setup.ps1 first, then .\start-dev.ps1" -ForegroundColor White
    exit 1
}

Write-Host ("=" * 70) -ForegroundColor Cyan