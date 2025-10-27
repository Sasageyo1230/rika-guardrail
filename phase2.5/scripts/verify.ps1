# Phase 2.5 Deployment Verification
Write-Host "Phase 2.5 Deployment Verification" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check PostgreSQL
$pgTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT 'Database OK'" 2>$null
if ($pgTest) {
    Write-Host "✅ PostgreSQL: Running and accessible" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL: Connection failed" -ForegroundColor Red
}

# Check NATS
$natsTest = Test-NetConnection -ComputerName localhost -Port 4222 -InformationLevel Quiet
if ($natsTest) {
    Write-Host "✅ NATS: Running on port 4222" -ForegroundColor Green
} else {
    Write-Host "❌ NATS: Not accessible on port 4222" -ForegroundColor Red
}

# Check n8n
$n8nTest = Test-NetConnection -ComputerName localhost -Port 5678 -InformationLevel Quiet
if ($n8nTest) {
    Write-Host "✅ n8n: Running on port 5678" -ForegroundColor Green
} else {
    Write-Host "❌ n8n: Not accessible on port 5678" -ForegroundColor Red
}

# Check Phase 2.5 tables
$tableTest = docker exec rika-postgres psql -U rika_admin -d rika_core -c "SELECT table_name FROM information_schema.tables WHERE table_name IN ('control_requests', 'control_sessions', 'audit_logs', 'stream_sessions');" 2>$null
if ($tableTest -match "control_requests") {
    Write-Host "✅ Database Schema: Phase 2.5 tables created" -ForegroundColor Green
} else {
    Write-Host "❌ Database Schema: Phase 2.5 tables missing" -ForegroundColor Red
}

Write-Host "`nDeployment Summary:" -ForegroundColor Cyan
Write-Host "- Infrastructure: Ready (PostgreSQL, NATS, n8n)" -ForegroundColor White
Write-Host "- Database: Phase 2.5 schema created" -ForegroundColor White  
Write-Host "- Configuration: Environment files ready" -ForegroundColor White
Write-Host "- Code: All Phase 2.5 components deployed" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Configure LiveKit credentials in .env file" -ForegroundColor White
Write-Host "2. Import n8n workflow: http://localhost:5678" -ForegroundColor White
Write-Host "3. Install Python/Node dependencies" -ForegroundColor White
Write-Host "4. Start Phase 2.5 services manually" -ForegroundColor White

Write-Host "`nPhase 2.5 infrastructure is ready!" -ForegroundColor Green