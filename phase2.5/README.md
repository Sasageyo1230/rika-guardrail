# Rika Project - Phase 2.5: Streaming & Remote Control

## 🎯 Overview

Phase 2.5 extends the Rika Project with two critical capabilities:
- **EXTEND/VIEW Mode**: LiveKit-powered screen streaming with watermarks and consent
- **CONTROL Mode**: Secure remote input (mouse/keyboard) with approval workflows and TTL

Built on Phase 2's solid foundation (Atlas + Linking + Thumbnails + Gestures), this phase adds enterprise-grade remote access while maintaining security and compliance.

## 🚀 Quick Start (Copy & Paste Ready)

### Prerequisites
- Phase 2 running successfully
- Windows 10/11 with PowerShell
- Python 3.9+, Node.js 18+, PostgreSQL 13+
- LiveKit Cloud account (free tier works)

### 1. Setup LiveKit Account
```powershell
# Get your LiveKit credentials at https://cloud.livekit.io
# Save these for step 3
$LIVEKIT_URL = "wss://your-project.livekit.cloud"
$LIVEKIT_API_KEY = "your-api-key"
$LIVEKIT_SECRET_KEY = "your-secret-key"
```

### 2. Install Dependencies
```powershell
# Core API dependencies
cd C:\rika-core\phase2.5\core
pip install livekit-api==0.5.0 asyncio-nats-client==0.11.5

# Desktop Agent dependencies  
cd ..\agent-desktop
pip install livekit==0.9.0 pynput==1.7.6 pillow==10.0.0

# Atlas UI dependencies
cd ..\ui
npm install livekit-client@1.15.0 @livekit/components-react@1.4.0
```

### 3. Configure Environment
```powershell
# Create Phase 2.5 environment file
cd C:\rika-core\phase2.5
@"
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_SECRET_KEY=your-secret-key

# NATS Configuration  
NATS_URL=nats://localhost:4222
NATS_USER=rika-user
NATS_PASS=rika-secure-password

# n8n Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/rika-control-approval
N8N_ADMIN_EMAIL=admin@company.com
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Security
AUDIT_LOG_RETENTION_DAYS=90
MAX_CONTROL_SESSIONS=5
MAX_STREAM_QUALITY=1080p
"@ | Out-File -FilePath .env -Encoding utf8
```

### 4. Database Migration
```powershell
cd C:\rika-core\phase2.5\core

# Create Phase 2.5 tables
python -c @"
import asyncio
import asyncpg
from api import DATABASE_URL

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Control requests table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS control_requests (
            id SERIAL PRIMARY KEY,
            request_id VARCHAR(50) UNIQUE NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            requester VARCHAR(100) NOT NULL,
            reason TEXT,
            ttl_minutes INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            approved_at TIMESTAMP,
            approved_by VARCHAR(100),
            expires_at TIMESTAMP
        )
    ''')
    
    # Control sessions table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS control_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(50) UNIQUE NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            requester VARCHAR(100) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL,
            last_activity TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Audit logs table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            user_id VARCHAR(100),
            device_id VARCHAR(50),
            session_id VARCHAR(50),
            details JSONB,
            ip_address INET,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    await conn.close()
    print("Phase 2.5 database migration completed!")

asyncio.run(migrate())
"@
```

### 5. Start Services
```powershell
# Terminal 1: Start enhanced Core API
cd C:\rika-core\phase2.5\core
python api.py

# Terminal 2: Start NATS server
nats-server --config nats.conf

# Terminal 3: Start n8n (if not already running)
cd C:\n8n
n8n start

# Terminal 4: Start enhanced Desktop Agent
cd C:\rika-core\phase2.5\agent-desktop
python agent.py

# Terminal 5: Start enhanced Atlas UI
cd C:\rika-core\phase2.5\ui
npm run dev
```

## 📋 Testing Your Setup

### Test 1: Basic Streaming
1. Open Atlas Dashboard (http://localhost:5173)
2. Link a device in **VIEW** mode
3. Click "Start Stream" → "View Stream"
4. ✅ You should see live screen sharing with watermark

### Test 2: Remote Control Request
1. Link a device in **CONTROL** mode  
2. Click "Request Control"
3. Fill TTL (15 min) and reason
4. ✅ Check n8n executions for approval workflow
5. ✅ Approve via Telegram/email link
6. ✅ "Control" button should become active

### Test 3: Security Features
1. During control session, check consent banner on target screen
2. Try exceeding TTL - session should auto-terminate
3. Check audit logs in database
4. ✅ All security features working

## 🏗️ Architecture Overview

```
Atlas Dashboard (React + LiveKit Client)
            ↕ HTTP + WebSocket
        Core API (FastAPI + PostgreSQL)
            ↕ NATS Messaging  
        Desktop Agent (Python + LiveKit + pynput)
            ↕ Webhook
        n8n Approval Workflow
```

### Key Components

**🎮 Atlas Dashboard** (`ui/`)
- `StreamViewer.tsx`: LiveKit streaming with remote control overlay
- `ControlRequestModal.tsx`: Secure control request form with TTL slider
- `DeviceCard.tsx`: Enhanced device cards showing streaming/control status
- `App.tsx`: Updated main dashboard with Phase 2.5 features

**🔧 Core API** (`core/api.py`)
- `/control/request`: Create control request → trigger n8n approval
- `/control/approve`: Handle approval webhook from n8n  
- `/control/input`: Relay input events to desktop agent via NATS
- `/streams`: Manage LiveKit streaming sessions and tokens

**🖥️ Desktop Agent** (`agent-desktop/agent.py`)
- `LiveKitStreamer`: Screen capture → LiveKit room publishing
- `ConsentBanner`: On-screen notifications during control sessions
- `RemoteControlHandler`: Process input events via pynput injection
- `WatermarkOverlay`: Security watermarks on streams

**🔄 n8n Workflow** (`n8n/rika-control-approval-flow.json`)
- Webhook trigger from Core API control requests
- Telegram/Email notifications with approval buttons
- 5-minute timeout with auto-deny
- Callback handling to approve/deny requests

## 📖 Detailed Documentation

### Core Features

#### LiveKit Streaming (EXTEND/VIEW)
- **Screen Capture**: Full desktop or application window streaming
- **WebRTC**: Low-latency streaming via LiveKit infrastructure  
- **Watermarks**: Configurable security overlays
- **Consent**: On-screen banners showing streaming status
- **Quality**: Adaptive bitrate (720p/1080p) based on bandwidth

#### Remote Control (CONTROL)
- **Input Injection**: Mouse movement, clicks, keyboard input via pynput
- **Approval Workflow**: n8n-powered approval with email/Telegram notifications
- **TTL Management**: 5-30 minute sessions with automatic cleanup
- **Security**: Consent banners, audit logging, session monitoring
- **Real-time**: NATS messaging for low-latency input events

### Security Model

#### Approval Process
1. User requests control access with reason and TTL
2. Core API creates request → sends webhook to n8n
3. n8n sends approval notification to admin via Telegram/Email
4. Admin approves/denies within 5 minutes (auto-deny if timeout)
5. n8n sends callback to Core API with decision
6. Control session activated with automatic expiration

#### Audit & Compliance
- All control sessions logged with timestamps, users, reasons
- Input events logged (mouse/keyboard activity)
- Session duration tracking and automatic cleanup
- Policy enforcement (max sessions, quality limits)
- Watermarks and consent for legal compliance

#### TTL & Resource Management
- Control sessions: 5-30 minutes maximum
- Streaming sessions: Configurable quality limits
- Concurrent session limits per device/user
- Automatic cleanup on expiration or disconnection

### Configuration Files

#### Policy Configuration (`core/config/policies.json`)
```json
{
  "control_policies": {
    "max_concurrent_sessions": 5,
    "max_session_duration_minutes": 30,
    "approval_required": true,
    "approval_timeout_minutes": 5,
    "allowed_input_types": ["mouse", "keyboard"],
    "audit_all_sessions": true
  },
  "stream_policies": {
    "max_quality": "1080p",
    "max_fps": 30,
    "watermark_required": true,
    "consent_banner_required": true,
    "max_concurrent_streams": 10
  }
}
```

#### NATS Configuration (`nats.conf`)
```
port: 4222
http_port: 8222

accounts: {
  RIKA: {
    users: [
      {user: rika-core, password: core-password}
      {user: rika-agent, password: agent-password}
      {user: rika-ui, password: ui-password}
    ]
  }
}

jetstream: {
  store_dir: "./nats-data"
  max_memory_store: 1GB
}
```

## 🔧 Troubleshooting

### Common Issues

#### "LiveKit connection failed"
```powershell
# Check LiveKit credentials
$env:LIVEKIT_URL; $env:LIVEKIT_API_KEY; $env:LIVEKIT_SECRET_KEY

# Test LiveKit connectivity
curl -X POST "$env:LIVEKIT_URL/twirp/livekit.RoomService/ListRooms" `
  -H "Authorization: Bearer $(livekit-cli token create --api-key $env:LIVEKIT_API_KEY --api-secret $env:LIVEKIT_SECRET_KEY)"
```

#### "Control request not appearing in n8n"
```powershell
# Check n8n webhook URL
curl -X POST http://localhost:5678/webhook/rika-control-approval `
  -H "Content-Type: application/json" `
  -d '{"test": "webhook connectivity"}'

# Check n8n execution logs in UI
```

#### "NATS connection errors"
```powershell
# Check NATS server status
nats-server --signal status

# Test NATS connectivity
nats pub rika.test "hello world"
nats sub rika.test
```

#### "Input events not working"
- Ensure Desktop Agent running as Administrator (required for input injection)
- Check antivirus isn't blocking pynput
- Verify control session is active (check consent banner)

### Performance Tuning

#### Streaming Quality
```python
# In agent-desktop/agent.py, adjust streaming settings
STREAM_CONFIG = {
    "width": 1920,      # Lower for better performance
    "height": 1080,     
    "fps": 30,          # Reduce to 15-20 for slower connections
    "bitrate": 2000000, # 2Mbps, adjust based on bandwidth
}
```

#### Input Latency
```python
# In core/api.py, adjust NATS message timeout
NATS_TIMEOUT = 100  # milliseconds, lower = faster but less reliable
```

### Logs & Monitoring

#### Core API Logs
```powershell
# Enable debug logging
$env:LOG_LEVEL = "DEBUG"
cd C:\rika-core\phase2.5\core
python api.py
```

#### Desktop Agent Logs
```powershell
cd C:\rika-core\phase2.5\agent-desktop
python agent.py --verbose
```

#### Database Queries
```sql
-- Check recent control requests
SELECT * FROM control_requests ORDER BY created_at DESC LIMIT 10;

-- Check active sessions
SELECT * FROM control_sessions WHERE status = 'active';

-- Check audit logs
SELECT * FROM audit_logs WHERE event_type = 'control_session_started' 
ORDER BY timestamp DESC LIMIT 20;
```

## 🔒 Production Deployment

### Security Hardening
1. **Use TLS everywhere**: NATS, PostgreSQL, LiveKit, n8n webhooks
2. **Network isolation**: VPN/firewall rules for component communication
3. **Credential rotation**: Regular rotation of API keys and passwords
4. **Audit monitoring**: Set up alerts for suspicious activity
5. **Compliance**: Review audit logs regularly, maintain retention policies

### Scaling Considerations
- **Load balancing**: Multiple Core API instances behind load balancer
- **Database**: PostgreSQL read replicas for audit log queries
- **NATS clustering**: NATS cluster for high availability
- **LiveKit**: Enterprise LiveKit deployment for production traffic

## 📞 Support

### Getting Help
- Check logs in each component directory
- Review n8n execution logs for approval workflow issues
- Test individual components in isolation
- Verify environment variables and configuration files

### Common Commands
```powershell
# Restart all services quickly
cd C:\rika-core\phase2.5
.\scripts\restart-all.ps1

# Check service health
curl http://localhost:8000/health        # Core API
curl http://localhost:5173/              # Atlas UI  
nats-server --signal status             # NATS

# View real-time logs
Get-Content -Path "core\logs\api.log" -Wait        # Core API
Get-Content -Path "agent-desktop\logs\agent.log" -Wait  # Desktop Agent
```

This completes the Phase 2.5 implementation! 🎉

The system now provides secure, enterprise-grade remote access capabilities while maintaining the user-friendly approach established in Phase 2.