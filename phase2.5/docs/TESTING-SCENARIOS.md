# Phase 2.5 Testing Scenarios

## 🧪 Comprehensive Test Suite

This document provides detailed testing scenarios to validate all Phase 2.5 capabilities. Use these tests before production deployment and for ongoing validation.

## Test Environment Setup

### Prerequisites
- Phase 2.5 fully installed per Setup Guide
- At least 2 Windows machines (Controller + Target)
- Administrator rights on target machine
- All services running and healthy

### Test Data Setup
```powershell
# Create test user accounts
$testUsers = @(
    @{name="test-admin"; role="admin"; email="admin@test.com"}
    @{name="test-user"; role="user"; email="user@test.com"}
    @{name="test-viewer"; role="viewer"; email="viewer@test.com"}
)

# Create test devices (add to database)
$testDevices = @(
    @{id="test-desktop-1"; name="Test Desktop 1"; type="desktop"}
    @{id="test-laptop-2"; name="Test Laptop 2"; type="laptop"}
    @{id="test-workstation-3"; name="Test Workstation 3"; type="desktop"}
)
```

## 🔍 Test Categories

### A. Basic Health & Connectivity Tests

#### A1. Service Health Check
**Objective**: Verify all services are running and responding
```powershell
# Test script
$services = @(
    @{name="Core API"; url="http://localhost:8000/health"; expected="healthy"}
    @{name="Atlas UI"; url="http://localhost:5173"; expected="200"}
    @{name="NATS"; port=4222}
    @{name="PostgreSQL"; port=5432}
    @{name="n8n"; url="http://localhost:5678/healthz"; expected="200"}
)

foreach ($service in $services) {
    if ($service.url) {
        $response = Invoke-RestMethod -Uri $service.url -Method GET
        Write-Host "$($service.name): $($response.status -eq $service.expected ? 'PASS' : 'FAIL')"
    } elseif ($service.port) {
        $connection = Test-NetConnection -ComputerName localhost -Port $service.port -InformationLevel Quiet
        Write-Host "$($service.name): $($connection ? 'PASS' : 'FAIL')"
    }
}
```

**Expected Results**:
- All services return healthy status
- All ports accessible
- No error logs in service outputs

#### A2. Database Connectivity
**Objective**: Verify Phase 2.5 database tables and connectivity
```sql
-- Execute in PostgreSQL
-- Test 1: Table existence
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN 
('control_requests', 'control_sessions', 'audit_logs', 'stream_sessions');

-- Test 2: Basic operations
INSERT INTO control_requests (request_id, device_id, requester, ttl_minutes) 
VALUES ('test-req-1', 'test-device-1', 'test-user', 15);

SELECT * FROM control_requests WHERE request_id = 'test-req-1';
DELETE FROM control_requests WHERE request_id = 'test-req-1';
```

**Expected Results**:
- All 4 Phase 2.5 tables exist
- CRUD operations work without errors
- Indexes created successfully

#### A3. NATS Messaging
**Objective**: Verify NATS pub/sub functionality
```powershell
# Terminal 1: Subscribe to test topic
nats sub "rika.test.*"

# Terminal 2: Publish test message
nats pub "rika.test.connection" '{"test": "connectivity", "timestamp": "'$(Get-Date -Format 'o')'"}'
```

**Expected Results**:
- Message received in subscriber
- No connection errors
- Message format preserved

### B. Authentication & Authorization Tests

#### B1. User Role Validation
**Objective**: Verify role-based access controls

**Test Case**: Admin Role
1. Login as admin user
2. Attempt control request → Should succeed
3. Attempt stream start → Should succeed
4. Check audit logs → Should have access

**Test Case**: Regular User Role  
1. Login as regular user
2. Attempt control request → Should require approval
3. Attempt policy modification → Should fail
4. Check audit logs → Should have limited access

**Test Case**: Viewer Role
1. Login as viewer user
2. Attempt control request → Should fail
3. Attempt stream viewing → Should succeed
4. Check audit logs → Should be read-only

#### B2. Session Management
**Objective**: Verify user session handling
```powershell
# Test session timeout
$session = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method POST -Body @{
    username="test-user"
    password="test-pass"
} -ContentType "application/json"

# Wait for session timeout + 1 minute
Start-Sleep -Seconds 3660

# Try authenticated request (should fail)
$result = Invoke-RestMethod -Uri "http://localhost:8000/links" -Headers @{
    Authorization="Bearer $($session.token)"
} -Method GET -ErrorAction SilentlyContinue
```

**Expected Results**:
- Login successful with valid credentials
- Session expires after configured timeout
- Expired sessions rejected with 401 error

### C. Streaming Tests (EXTEND/VIEW Mode)

#### C1. Basic Streaming
**Objective**: Verify LiveKit streaming functionality

**Prerequisites**: 
- Device linked in VIEW or EXTEND mode
- Target device has active desktop session

**Test Steps**:
1. Click "Start Stream" on linked device
2. Wait for stream initialization (30 seconds max)
3. Click "View Stream" 
4. Verify stream quality and latency

**Validation**:
```powershell
# Check stream session in database
$streamCheck = Invoke-RestMethod -Uri "http://localhost:8000/streams" -Method GET
Write-Host "Active streams: $($streamCheck.Count)"

# Check LiveKit room status
# (Use LiveKit dashboard or API)
```

**Expected Results**:
- Stream starts within 30 seconds
- Video quality matches configured settings (720p/1080p)
- Audio synchronized (if enabled)
- Watermark visible on stream
- Stream session recorded in database

#### C2. Stream Quality Adaptation
**Objective**: Test adaptive bitrate and quality settings

**Test Matrix**:
| Network Condition | Expected Quality | Expected FPS | Max Latency |
|-------------------|------------------|--------------|-------------|
| Excellent (>10Mbps) | 1080p | 30 FPS | <200ms |
| Good (5-10Mbps) | 720p | 30 FPS | <300ms |
| Poor (1-5Mbps) | 480p | 15 FPS | <500ms |
| Very Poor (<1Mbps) | Auto-disconnect | N/A | N/A |

**Test Procedure**:
```powershell
# Simulate network conditions using NetLimiter or similar
# Monitor stream quality in Atlas UI
# Check bandwidth usage in LiveKit dashboard
```

#### C3. Multi-Viewer Streaming
**Objective**: Test multiple concurrent viewers

**Test Steps**:
1. Start stream on one device
2. Open Atlas UI in 3 different browser tabs/computers
3. Join stream from all 3 viewers simultaneously
4. Monitor performance and resource usage

**Expected Results**:
- All viewers see synchronized stream
- No significant quality degradation
- Server resources within acceptable limits
- Viewer count accurately tracked

#### C4. Stream Security Features
**Objective**: Verify security overlays and consent

**Test Cases**:

**Watermark Test**:
1. Start stream with watermark enabled
2. Verify watermark shows: "RIKA MONITORED - [timestamp] - [user]"
3. Check watermark not removable from stream
4. Verify watermark updates every 30 seconds

**Consent Banner Test**:
1. Start stream on target device
2. Verify consent banner appears on target screen
3. Check banner shows: stream status, viewer count, expiration
4. Verify banner cannot be dismissed by target user

### D. Remote Control Tests (CONTROL Mode)

#### D1. Control Request Workflow
**Objective**: Test end-to-end control request and approval process

**Test Steps**:
1. Link device in CONTROL mode
2. Click "Request Control" 
3. Fill form with TTL=10min, reason="Testing remote control"
4. Submit request
5. Monitor n8n workflow execution
6. Approve request via n8n interface
7. Verify control session activation

**Validation Points**:
```sql
-- Check control request created
SELECT * FROM control_requests WHERE device_id = 'test-device-1' ORDER BY created_at DESC LIMIT 1;

-- Check n8n execution (via API or UI)
-- Check approval notification sent

-- Check control session created after approval
SELECT * FROM control_sessions WHERE device_id = 'test-device-1' AND status = 'active';
```

**Expected Results**:
- Request created in database
- n8n workflow triggers within 5 seconds
- Notification sent via configured channel (email/Telegram)
- Approval creates active control session
- TTL correctly calculated and enforced

#### D2. Input Event Testing
**Objective**: Verify mouse and keyboard input forwarding

**Test Matrix**:
| Input Type | Test Action | Expected Result |
|------------|-------------|-----------------|
| Mouse Move | Move cursor in stream viewer | Cursor moves on target screen |
| Left Click | Click button in stream | Button activates on target |
| Right Click | Right-click in stream | Context menu appears on target |
| Double Click | Double-click file in stream | File opens on target |
| Keyboard | Type "Hello World" | Text appears on target |
| Key Combo | Ctrl+C, Ctrl+V | Copy/paste works on target |
| Function Keys | F1, F5, Alt+Tab | Function keys work on target |
| Special Keys | Windows key, Print Screen | Special keys work on target |

**Test Procedure**:
```powershell
# Start control session
# Use automated testing script
$inputTests = @(
    @{type="mouse_move"; x=100; y=100; expected="cursor at (100,100)"}
    @{type="left_click"; x=50; y=50; expected="click registered"}
    @{type="key_press"; key="H"; expected="H typed"}
    @{type="key_combo"; keys=@("ctrl", "c"); expected="copy action"}
)

foreach ($test in $inputTests) {
    # Send input event via Atlas UI
    # Verify result on target screen
    # Log result
}
```

#### D3. Control Session Management
**Objective**: Test session lifecycle and TTL enforcement

**TTL Test**:
1. Start control session with TTL=5 minutes
2. Monitor session status every minute
3. At 4 minutes: verify session still active
4. At 6 minutes: verify session auto-terminated

**Manual Termination Test**:
1. Start control session
2. Click "Revoke Control" in Atlas UI
3. Verify immediate session termination
4. Verify target device shows session ended

**Concurrent Session Limits**:
1. Start control session on device A
2. Attempt second control session on device A
3. Verify second session rejected (if policy limits = 1)
4. Start control session on device B 
5. Verify both sessions work independently

#### D4. Control Security Features
**Objective**: Verify security measures during control

**Consent Banner Test**:
1. Start control session
2. Verify banner appears on target screen immediately
3. Check banner shows: "REMOTE CONTROL ACTIVE", controller name, time remaining
4. Verify banner updates countdown in real-time
5. Check banner disappears when session ends

**Audit Logging Test**:
```sql
-- Verify comprehensive audit trail
SELECT event_type, details, timestamp 
FROM audit_logs 
WHERE session_id = 'test-session-id' 
ORDER BY timestamp;

-- Expected events:
-- control_session_requested
-- control_session_approved  
-- control_session_started
-- mouse_move events (sampled)
-- key_press events (sampled)
-- control_session_ended
```

**Screen Recording Test** (if enabled):
1. Start control session with recording enabled
2. Perform various actions
3. End session
4. Verify recording file created and playable
5. Check recording contains all actions

### E. n8n Workflow Tests

#### E1. Approval Workflow
**Objective**: Test automated approval process

**Happy Path Test**:
1. Generate control request via API
2. Monitor n8n execution log
3. Verify webhook received within 5 seconds
4. Check notification sent (email/Telegram)
5. Use approval link to approve
6. Verify callback to Core API
7. Check control session created

**Timeout Test**:
1. Generate control request
2. Do NOT approve within timeout period (5 minutes)
3. Verify auto-denial triggered
4. Check denial notification sent
5. Verify request marked as denied in database

**Error Handling Test**:
1. Stop Core API temporarily
2. Generate approval in n8n (simulate webhook from external source)
3. Verify n8n handles callback failure gracefully
4. Start Core API
5. Check n8n retries callback (if configured)

#### E2. Notification Delivery
**Objective**: Verify approval notifications work

**Email Notification Test**:
1. Configure SMTP settings in n8n
2. Generate control request
3. Verify email received within 60 seconds
4. Check email contains: device info, requester, reason, approval links
5. Test approval/denial links work

**Telegram Notification Test**:
1. Configure Telegram bot in n8n
2. Generate control request  
3. Verify Telegram message received
4. Check message format and approval buttons
5. Test inline approval buttons

### F. Performance & Load Tests

#### F1. Concurrent Streaming
**Objective**: Test system under multiple simultaneous streams

**Test Procedure**:
```powershell
# Start multiple streams simultaneously
$devices = @("device-1", "device-2", "device-3", "device-4", "device-5")
foreach ($device in $devices) {
    # Start stream via API call
    Invoke-RestMethod -Uri "http://localhost:8000/stream/start" -Method POST -Body @{
        device_id = $device
        quality = "720p"
    } -ContentType "application/json"
}

# Monitor system resources
Get-Counter -Counter "\Processor(_Total)\% Processor Time" -SampleInterval 5 -MaxSamples 60
Get-Counter -Counter "\Memory\Available MBytes" -SampleInterval 5 -MaxSamples 60
```

**Performance Metrics**:
- CPU usage should remain <80%
- Memory usage should not increase beyond allocated limits
- Network bandwidth within ISP limits
- All streams maintain target quality
- No frame drops or significant latency increase

#### F2. Control Session Load
**Objective**: Test multiple concurrent control sessions

**Test Matrix**:
| Concurrent Sessions | Expected Performance | CPU Usage | Memory Usage |
|--------------------|---------------------|-----------|--------------|
| 1 session | Excellent (<50ms latency) | <20% | <500MB |
| 3 sessions | Good (<100ms latency) | <40% | <1GB |
| 5 sessions | Acceptable (<200ms latency) | <60% | <2GB |
| 10 sessions | Degraded (>200ms latency) | <80% | <4GB |

#### F3. Database Performance
**Objective**: Verify database handles audit logging volume

**Load Generation**:
```sql
-- Generate test audit data
INSERT INTO audit_logs (event_type, user_id, device_id, timestamp)
SELECT 
    'test_event_' || (random() * 10)::int,
    'user_' || (random() * 100)::int,
    'device_' || (random() * 50)::int,
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000);

-- Test query performance
EXPLAIN ANALYZE SELECT * FROM audit_logs 
WHERE event_type = 'control_session_started' 
AND timestamp > NOW() - interval '1 day';
```

**Performance Targets**:
- Insert 1000 audit logs/second
- Query response <100ms for recent data
- Query response <1s for historical data
- Database size growth predictable

### G. Security & Compliance Tests

#### G1. Access Control Validation
**Objective**: Verify no unauthorized access possible

**Test Cases**:
1. **Unauthenticated Access**: Try API calls without tokens → Should fail
2. **Token Manipulation**: Modify JWT tokens → Should fail validation  
3. **Role Escalation**: Regular user tries admin actions → Should be denied
4. **Cross-Device Access**: User A tries to control User B's device → Should be denied
5. **Expired Sessions**: Use expired session tokens → Should be rejected

#### G2. Data Protection
**Objective**: Verify sensitive data is properly protected

**Encryption Test**:
```powershell
# Check database connections use SSL
$connectionString = "server=localhost;database=rika_db;sslmode=require"

# Check NATS uses TLS
nats-server --tls --tlscert=server.crt --tlskey=server.key

# Check LiveKit uses WSS
# Verify LIVEKIT_URL starts with "wss://"
```

**Data Masking Test**:
```sql
-- Verify sensitive fields are masked in logs
SELECT details FROM audit_logs WHERE event_type = 'authentication';
-- Should not contain plain-text passwords
```

#### G3. Audit Trail Completeness
**Objective**: Verify all actions are properly logged

**Audit Completeness Checklist**:
- [ ] User logins/logouts logged
- [ ] Device linking/unlinking logged  
- [ ] Control requests logged
- [ ] Control approvals/denials logged
- [ ] Control sessions start/end logged
- [ ] Input events logged (sampled, not every keystroke)
- [ ] Stream sessions start/end logged
- [ ] Policy violations logged
- [ ] System errors logged

**Log Integrity Test**:
```sql
-- Check for log tampering
SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() + interval '1 hour';
-- Should be 0 (no future timestamps)

SELECT COUNT(*) FROM audit_logs WHERE details IS NULL;
-- Should be minimal (only certain event types)
```

### H. Error Handling & Recovery Tests

#### H1. Service Failure Recovery
**Objective**: Test system resilience to component failures

**Core API Failure Test**:
1. Stop Core API service
2. Verify Atlas UI shows connection error
3. Desktop agents should queue messages (if NATS configured for persistence)
4. Restart Core API
5. Verify system resumes normal operation
6. Check no data loss occurred

**NATS Failure Test**:
1. Stop NATS service
2. Verify components detect disconnection
3. Try to start new control session → Should fail gracefully
4. Restart NATS
5. Verify components reconnect automatically
6. Test normal operations resume

**Database Failure Test**:
1. Stop PostgreSQL
2. Verify API returns appropriate errors
3. Check no service crashes occur
4. Restart PostgreSQL
5. Verify automatic reconnection
6. Test data integrity maintained

#### H2. Network Failure Scenarios
**Objective**: Test system behavior under network issues

**Partial Network Loss**:
1. Block NATS traffic via firewall
2. Verify control sessions fail gracefully
3. Check appropriate error messages shown
4. Restore network
5. Verify automatic recovery

**High Latency Simulation**:
```powershell
# Use NetLimiter or similar to add 500ms latency
# Test control session quality
# Verify timeout handling
# Check user experience remains acceptable
```

#### H3. Data Corruption Scenarios
**Objective**: Test handling of corrupted data

**Invalid Message Test**:
```json
// Send malformed NATS message
{
  "type": "invalid_control_input",
  "malformed": "missing required fields"
}
```

**Database Consistency Test**:
```sql
-- Create orphaned control session (no matching request)
INSERT INTO control_sessions (session_id, device_id, requester, expires_at)
VALUES ('orphan-session', 'device-1', 'test-user', NOW() + interval '1 hour');

-- Verify system handles gracefully
```

## 📊 Test Results Documentation

### Test Report Template
```
# Phase 2.5 Test Report
Date: [Date]
Version: [Version]
Tester: [Name]

## Summary
- Total Tests: [Number]
- Passed: [Number] 
- Failed: [Number]
- Blocked: [Number]

## Test Results by Category
### A. Health & Connectivity: [Pass/Fail]
### B. Authentication & Authorization: [Pass/Fail] 
### C. Streaming Tests: [Pass/Fail]
### D. Remote Control Tests: [Pass/Fail]
### E. n8n Workflow Tests: [Pass/Fail]
### F. Performance & Load Tests: [Pass/Fail]
### G. Security & Compliance Tests: [Pass/Fail]
### H. Error Handling & Recovery Tests: [Pass/Fail]

## Failed Tests
[List of failed tests with details]

## Performance Metrics
- Average control latency: [ms]
- Stream quality achieved: [resolution/fps]
- Concurrent sessions supported: [number]
- System resource usage: CPU [%], Memory [GB]

## Recommendations
[List of recommended fixes or improvements]
```

### Automated Testing Script
```powershell
# Complete automated test runner
param(
    [string[]]$TestCategories = @("A","B","C","D","E","F","G","H"),
    [string]$OutputFile = "test-results.json"
)

$results = @{}

foreach ($category in $TestCategories) {
    Write-Host "Running Category $category tests..."
    
    switch ($category) {
        "A" { $results[$category] = Test-HealthConnectivity }
        "B" { $results[$category] = Test-Authentication }
        "C" { $results[$category] = Test-Streaming }
        "D" { $results[$category] = Test-RemoteControl }
        "E" { $results[$category] = Test-N8nWorkflow }
        "F" { $results[$category] = Test-Performance }
        "G" { $results[$category] = Test-Security }
        "H" { $results[$category] = Test-ErrorHandling }
    }
}

$results | ConvertTo-Json -Depth 3 | Out-File $OutputFile
Write-Host "Test results saved to $OutputFile"
```

This comprehensive test suite ensures Phase 2.5 meets all functional, performance, and security requirements before production deployment.