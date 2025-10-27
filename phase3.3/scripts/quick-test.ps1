# Quick Test Script for Rika Phase 3.3
param([switch]$Verbose)

Write-Host ""
Write-Host "======================================================================"
Write-Host "[TEST] Rika Phase 3.3 - Service Health Check"
Write-Host "======================================================================"

$services = @(
    @{ Name = "Core API"; Port = 5317; Path = "/health" },
    @{ Name = "Core API Self-Check"; Port = 5317; Path = "/selfcheck" },
    @{ Name = "Atlas UI"; Port = 5173; Path = "/" }
)

$passed = 0
$failed = 0

foreach ($service in $services) {
    $url = "http://localhost:$($service.Port)$($service.Path)"
    Write-Host "Testing $($service.Name)..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host " [OK]" -ForegroundColor Green
            $passed++
        } else {
            Write-Host " [WARN] HTTP $($response.StatusCode)" -ForegroundColor Yellow
            $passed++
        }
    } catch {
        Write-Host " [FAIL] Not responding" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "======================================================================"
if ($failed -eq 0) {
    Write-Host "[SUCCESS] All $passed tests passed!" -ForegroundColor Green
    Write-Host "Atlas UI available at: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "Core API available at: http://localhost:5317" -ForegroundColor Cyan
    Write-Host "API Docs available at: http://localhost:5317/docs" -ForegroundColor Cyan
} else {
    Write-Host "[PARTIAL] $passed passed, $failed failed" -ForegroundColor Yellow
    Write-Host "Some services may still be starting..." -ForegroundColor Yellow
}
Write-Host "======================================================================"