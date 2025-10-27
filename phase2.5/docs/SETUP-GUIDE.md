# Rika Phase 2.5 - Complete Setup Guide

## 🎯 Step-by-Step Installation

This guide assumes you have Rika Phase 2 running successfully. We'll add Phase 2.5 capabilities on top of your existing setup.

## Pre-Installation Checklist

- [ ] Phase 2 working (Atlas Dashboard shows linked devices)
- [ ] PowerShell 5.1+ (Windows 10/11)
- [ ] Python 3.9+ with pip
- [ ] Node.js 18+ with npm
- [ ] PostgreSQL 13+ running
- [ ] Admin rights on target machines

## Step 1: LiveKit Account Setup

### 1.1 Create LiveKit Cloud Account
```powershell
# Open browser and create free account
Start-Process "https://cloud.livekit.io"
```

1. Sign up for free LiveKit Cloud account
2. Create new project: "Rika-Phase2.5"
3. Copy your credentials:
   - **API URL**: `wss://rika-phase25-xxxxx.livekit.cloud`
   - **API Key**: `APIxxxxxxxxxxxxx`
   - **Secret Key**: `secretxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 1.2 Test LiveKit Connection
```powershell
# Save credentials temporarily
$LIVEKIT_URL = "wss://your-project.livekit.cloud"
$LIVEKIT_API_KEY = "your-api-key"  
$LIVEKIT_SECRET_KEY = "your-secret-key"

# Test connection (should return empty rooms list)
curl -X POST "$LIVEKIT_URL/twirp/livekit.RoomService/ListRooms" `
  -H "Authorization: Bearer test"
```

## Step 2: Install Phase 2.5 Dependencies

### 2.1 Core API Dependencies
```powershell
cd C:\rika-core\phase2.5\core

# Install new Python packages
pip install livekit-api==0.5.0
pip install asyncio-nats-client==0.11.5
pip install pillow==10.0.0

# Verify installation
python -c "import livekit; import nats; import PIL; print('Dependencies OK')"
```

### 2.2 Desktop Agent Dependencies
```powershell
cd C:\rika-core\phase2.5\agent-desktop

# Install streaming and control packages
pip install livekit==0.9.0
pip install pynput==1.7.6
pip install pillow==10.0.0

# Test pynput (requires admin rights)
# Run PowerShell as Administrator, then:
python -c "from pynput import mouse, keyboard; print('pynput OK')"
```

### 2.3 Atlas UI Dependencies
```powershell
cd C:\rika-core\phase2.5\ui

# Install LiveKit React components
npm install livekit-client@1.15.0
npm install @livekit/components-react@1.4.0
npm install lucide-react@0.263.1
npm install date-fns@2.30.0

# Verify installation
npm list | Select-String "livekit"
```

## Step 3: NATS Messaging Setup

### 3.1 Install NATS Server
```powershell
# Download NATS server
$natsUrl = "https://github.com/nats-io/nats-server/releases/download/v2.9.22/nats-server-v2.9.22-windows-amd64.zip"
Invoke-WebRequest -Uri $natsUrl -OutFile "nats-server.zip"

# Extract to C:\nats
Expand-Archive -Path "nats-server.zip" -DestinationPath "C:\nats"
$env:PATH += ";C:\nats"

# Test NATS installation
nats-server --version
```

### 3.2 Configure NATS Server
```powershell
# Create NATS config
cd C:\rika-core\phase2.5

@"
# NATS Configuration for Rika Phase 2.5
port: 4222
http_port: 8222

# Basic authentication
accounts: {
  RIKA: {
    users: [
      {user: rika-core, password: core-secure-123}
      {user: rika-agent, password: agent-secure-456} 
      {user: rika-ui, password: ui-secure-789}
    ]
  }
}

# JetStream for message persistence
jetstream: {
  store_dir: "./nats-data"
  max_memory_store: 512MB
  max_file_store: 1GB
}

# Logging
log_file: "./logs/nats.log"
debug: false
trace: false
"@ | Out-File -FilePath "nats.conf" -Encoding utf8
```

### 3.3 Start NATS Server
```powershell
# Start NATS in background
cd C:\rika-core\phase2.5
Start-Process -FilePath "nats-server" -ArgumentList "--config nats.conf" -WindowStyle Hidden

# Verify NATS is running
netstat -an | Select-String "4222"
# Should show: TCP    0.0.0.0:4222    0.0.0.0:0    LISTENING
```

## Step 4: Database Migration

### 4.1 Create Phase 2.5 Tables
```powershell
cd C:\rika-core\phase2.5\core

# Create migration script
@"
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rika:password@localhost/rika_db')

async def create_phase25_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print('Creating control_requests table...')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS control_requests (
                id SERIAL PRIMARY KEY,
                request_id VARCHAR(50) UNIQUE NOT NULL,
                device_id VARCHAR(50) NOT NULL,
                requester VARCHAR(100) NOT NULL,
                reason TEXT,
                ttl_minutes INTEGER NOT NULL DEFAULT 15,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW(),
                approved_at TIMESTAMP,
                approved_by VARCHAR(100),
                expires_at TIMESTAMP,
                n8n_execution_id VARCHAR(50)
            );
            CREATE INDEX IF NOT EXISTS idx_control_requests_device_id ON control_requests(device_id);
            CREATE INDEX IF NOT EXISTS idx_control_requests_status ON control_requests(status);
        ''')
        
        print('Creating control_sessions table...')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS control_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                device_id VARCHAR(50) NOT NULL,
                requester VARCHAR(100) NOT NULL,
                request_id VARCHAR(50) REFERENCES control_requests(request_id),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT NOW(),
                terminated_at TIMESTAMP,
                termination_reason VARCHAR(100)
            );
            CREATE INDEX IF NOT EXISTS idx_control_sessions_device_id ON control_sessions(device_id);
            CREATE INDEX IF NOT EXISTS idx_control_sessions_status ON control_sessions(status);
        ''')
        
        print('Creating audit_logs table...')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(100),
                device_id VARCHAR(50),
                session_id VARCHAR(50),
                details JSONB,
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_device_id ON audit_logs(device_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        ''')
        
        print('Creating stream_sessions table...')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS stream_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                device_id VARCHAR(50) NOT NULL,
                room_name VARCHAR(100) NOT NULL,
                requester VARCHAR(100) NOT NULL,
                quality VARCHAR(20) DEFAULT '720p',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                terminated_at TIMESTAMP,
                viewer_count INTEGER DEFAULT 0,
                bandwidth_mbps DECIMAL(5,2)
            );
            CREATE INDEX IF NOT EXISTS idx_stream_sessions_device_id ON stream_sessions(device_id);
            CREATE INDEX IF NOT EXISTS idx_stream_sessions_status ON stream_sessions(status);
        ''')
        
        print('Phase 2.5 database migration completed successfully!')
        
    except Exception as e:
        print(f'Migration failed: {e}')
        raise
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(create_phase25_tables())
"@ | Out-File -FilePath "migrate.py" -Encoding utf8

# Run migration
python migrate.py
```

### 4.2 Verify Database Tables
```powershell
# Connect to PostgreSQL and verify tables
psql -U rika -d rika_db -c "\dt"

# Should show new tables:
# control_requests, control_sessions, audit_logs, stream_sessions
```

## Step 5: n8n Workflow Configuration

### 5.1 Import Phase 2.5 Workflow
```powershell
# Start n8n if not already running
cd C:\n8n
Start-Process -FilePath "n8n" -ArgumentList "start" -WindowStyle Hidden

# Wait for n8n to start, then open browser
Start-Sleep -Seconds 10
Start-Process "http://localhost:5678"
```

1. In n8n UI, go to **Workflows** → **Import from File**
2. Upload `C:\rika-core\phase2.5\n8n\rika-control-approval-flow.json`
3. Configure webhook URL: `http://localhost:5678/webhook/rika-control-approval`
4. **Activate** the workflow

### 5.2 Configure Telegram Bot (Optional)
```powershell
# Create Telegram bot
Start-Process "https://t.me/BotFather"

# Follow BotFather instructions:
# /newbot -> "Rika Control Bot" -> get token
# /mybots -> select bot -> Bot Settings -> Group Privacy -> Turn off

# Get your chat ID
Start-Process "https://t.me/userinfobot"
# Send /start to get your chat ID
```

Update n8n workflow with Telegram credentials:
1. Edit "Send Telegram Notification" node
2. Add bot token and chat ID
3. Save and activate workflow

### 5.3 Test n8n Integration
```powershell
# Test webhook
curl -X POST http://localhost:5678/webhook/rika-control-approval `
  -H "Content-Type: application/json" `
  -d '{"test": "workflow test", "device_id": "test-device"}'

# Check n8n executions tab for successful test run
```

## Step 6: Environment Configuration

### 6.1 Create Phase 2.5 Environment File
```powershell
cd C:\rika-core\phase2.5

@"
# Phase 2.5 Configuration
# LiveKit Settings
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_SECRET_KEY=your-secret-key

# NATS Settings
NATS_URL=nats://localhost:4222
NATS_USER=rika-core
NATS_PASS=core-secure-123

# Database (inherits from Phase 2)
DATABASE_URL=postgresql://rika:password@localhost/rika_db

# n8n Integration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/rika-control-approval
N8N_ADMIN_EMAIL=admin@company.com

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Security Settings
AUDIT_LOG_RETENTION_DAYS=90
MAX_CONTROL_SESSIONS=5
MAX_STREAM_QUALITY=1080p
CONTROL_APPROVAL_TIMEOUT_MINUTES=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/phase25.log
"@ | Out-File -FilePath ".env" -Encoding utf8
```

### 6.2 Update with Your Actual Values
```powershell
# Edit the .env file with your LiveKit credentials
notepad C:\rika-core\phase2.5\.env

# Replace placeholder values:
# - LIVEKIT_URL with your actual LiveKit URL
# - LIVEKIT_API_KEY with your API key  
# - LIVEKIT_SECRET_KEY with your secret key
# - TELEGRAM_BOT_TOKEN (if using Telegram)
# - TELEGRAM_CHAT_ID (if using Telegram)
```

## Step 7: Service Startup Scripts

### 7.1 Create Startup Script
```powershell
cd C:\rika-core\phase2.5

@"
# Phase 2.5 Service Startup Script
param([string]`$Action = "start")

`$services = @(
    @{Name="NATS"; Path="C:\rika-core\phase2.5"; Command="nats-server --config nats.conf"}
    @{Name="Core API"; Path="C:\rika-core\phase2.5\core"; Command="python api.py"}
    @{Name="Desktop Agent"; Path="C:\rika-core\phase2.5\agent-desktop"; Command="python agent.py"}  
    @{Name="Atlas UI"; Path="C:\rika-core\phase2.5\ui"; Command="npm run dev"}
)

if (`$Action -eq "start") {
    Write-Host "Starting Phase 2.5 services..."
    foreach (`$service in `$services) {
        Write-Host "Starting `$(`$service.Name)..."
        cd `$service.Path
        Start-Process -FilePath "powershell" -ArgumentList "-Command", "`$(`$service.Command)" -WindowStyle Minimized
        Start-Sleep -Seconds 2
    }
    Write-Host "All services started! Check http://localhost:5173"
}

if (`$Action -eq "stop") {
    Write-Host "Stopping Phase 2.5 services..."
    Get-Process -Name "nats-server", "python", "node" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "All services stopped."
}

if (`$Action -eq "status") {
    Write-Host "Checking service status..."
    @("NATS:4222", "Core API:8000", "Atlas UI:5173") | ForEach-Object {
        `$service, `$port = `$_.Split(":")
        `$result = Test-NetConnection -ComputerName localhost -Port `$port -InformationLevel Quiet
        Write-Host "`$service : `$(if(`$result){'Running'}else{'Stopped'})"
    }
}
"@ | Out-File -FilePath "start-phase25.ps1" -Encoding utf8

# Make script executable
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 7.2 Start All Services
```powershell
# Start Phase 2.5 services
cd C:\rika-core\phase2.5
.\start-phase25.ps1 start

# Check service status
.\start-phase25.ps1 status
```

## Step 8: Verification Tests

### 8.1 Service Health Check
```powershell
# Test Core API
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "2.5.0"}

# Test Atlas UI
curl http://localhost:5173
# Expected: HTML page loads

# Test NATS
netstat -an | Select-String "4222"
# Expected: LISTENING on port 4222
```

### 8.2 Database Connectivity
```powershell
cd C:\rika-core\phase2.5\core
python -c @"
import asyncio
import asyncpg
import os

async def test_db():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    count = await conn.fetchval('SELECT COUNT(*) FROM control_requests')
    print(f'Database connected! Control requests: {count}')
    await conn.close()

asyncio.run(test_db())
"@
```

### 8.3 LiveKit Connectivity  
```powershell
cd C:\rika-core\phase2.5\core
python -c @"
import os
from livekit import api

lk_api = api.LiveKitAPI(
    os.getenv('LIVEKIT_URL'),
    os.getenv('LIVEKIT_API_KEY'), 
    os.getenv('LIVEKIT_SECRET_KEY')
)

# Test room creation
try:
    rooms = lk_api.room.list_rooms(api.ListRoomsRequest())
    print(f'LiveKit connected! Rooms: {len(rooms.rooms)}')
except Exception as e:
    print(f'LiveKit error: {e}')
"@
```

## Step 9: First Phase 2.5 Test

### 9.1 Test Streaming (VIEW Mode)
1. Open Atlas Dashboard: `http://localhost:5173`
2. Ensure a device shows as "active" (green status)
3. Click **"Link"** → select **"View"** mode → **"Link Device"**
4. Click **"Start Stream"** button on the linked device
5. Click **"View Stream"** 
6. ✅ **Expected**: Live screen stream opens with watermark

### 9.2 Test Control Request (CONTROL Mode)
1. Unlink the device from previous test
2. Click **"Link"** → select **"Control"** mode → **"Link Device"**  
3. Click **"Request Control"** button
4. Fill form: TTL = 15 minutes, Reason = "Testing Phase 2.5"
5. Click **"Request Control Access"**
6. ✅ **Expected**: 
   - Status changes to "Approval Pending..."
   - n8n workflow executes (check n8n UI)
   - Notification sent (email/Telegram if configured)

### 9.3 Test Approval Process
1. Go to n8n UI: `http://localhost:5678`
2. Check **Executions** tab for recent workflow run
3. Click the execution to see approval link
4. Click **"Approve"** button in the execution
5. Return to Atlas Dashboard
6. ✅ **Expected**: 
   - Status changes to "Control Active"  
   - Consent banner appears on target screen
   - **"Control"** button becomes clickable

### 9.4 Test Remote Control
1. Click **"Control"** button on approved device
2. Try moving mouse in the stream viewer
3. Try clicking in the stream viewer
4. ✅ **Expected**:
   - Mouse cursor moves on target screen
   - Clicks register on target screen
   - Red control overlay visible in viewer

## Step 10: Production Checklist

### 10.1 Security Hardening
- [ ] Change default NATS passwords
- [ ] Enable TLS for all services  
- [ ] Set up firewall rules
- [ ] Configure audit log monitoring
- [ ] Test session TTL enforcement

### 10.2 Monitoring Setup
- [ ] Set up log rotation
- [ ] Configure health check alerts
- [ ] Monitor database growth
- [ ] Set up LiveKit usage tracking
- [ ] Test backup procedures

### 10.3 Documentation
- [ ] Update network diagrams
- [ ] Document approval workflow
- [ ] Create user training materials
- [ ] Test disaster recovery procedures

## 🎉 Congratulations!

Phase 2.5 is now fully operational! You have:

- ✅ LiveKit streaming with security watermarks
- ✅ Remote control with approval workflows  
- ✅ n8n automation for approvals
- ✅ NATS messaging for real-time communication
- ✅ Comprehensive audit logging
- ✅ TTL-based session management

Your Rika system now provides enterprise-grade remote access capabilities while maintaining security and compliance requirements.

## Next Steps

1. **User Training**: Train team members on new capabilities
2. **Policy Configuration**: Customize policies in `core/config/policies.json`  
3. **Integration**: Connect with existing ITSM/ticketing systems
4. **Scaling**: Plan for production load and redundancy
5. **Monitoring**: Set up alerting and dashboard monitoring

## Support & Troubleshooting

If you encounter issues:
1. Check service status: `.\start-phase25.ps1 status`
2. Review logs in each component directory
3. Test individual components in isolation
4. Verify environment variables and credentials
5. Check firewall and network connectivity

The Phase 2.5 system is designed to be robust and self-healing, but monitoring the health checks and logs will help you maintain optimal performance.