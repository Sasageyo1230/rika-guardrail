# Rika Phase 1 - Complete Implementation Guide

**Phase 1** of the Rika Project builds upon the working Phase 0 Docker stack with Core API, agents, and real-time messaging capabilities.

## 🎯 Phase 1 Deliverables

✅ **Core API Service (FastAPI)** - Device enrollment, heartbeat, presence, blackout endpoints
✅ **Database Schemas** - PostgreSQL tables for devices, sessions, tokens, and logs  
✅ **NATS Messaging** - Event-driven architecture with pub/sub messaging
✅ **Desktop Agent (Windows)** - System monitoring with hotkeys and NATS integration
✅ **Android Agent (Skeleton)** - Mobile companion app with Material 3 UI

## 📁 Project Structure

```
rika-core/phase1/
├── core/                       # Core API Service
│   ├── api.py                  # FastAPI application with all endpoints
│   ├── nats_example.py         # NATS publisher/subscriber demo
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Configuration template
├── agent-desktop/              # Windows Desktop Agent  
│   ├── agent.py               # Main agent application
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Configuration template
└── agent-android/             # Android Agent (Kotlin)
    ├── build.gradle.kts       # Android project configuration
    ├── app/src/main/          # Android application source
    └── README.md              # Android-specific setup guide
```

## 🚀 Quick Start Guide

### Prerequisites
- Phase 0 Docker stack running successfully (PostgreSQL, NATS, etc.)
- Python 3.9+ installed on Windows
- Android Studio (for mobile agent)

### 1. Start Phase 0 Services

Ensure your Docker Compose stack from Phase 0 is running:
```bash
cd rika-core
docker-compose up -d
```

Verify services:
- PostgreSQL: `localhost:5433`
- NATS: `localhost:4222`  
- pgAdmin: `http://localhost:5050`

### 2. Setup Core API

```bash
cd phase1/core
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run the API server
python api.py
```

Core API will be available at: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### 3. Setup Desktop Agent

```bash
cd phase1/agent-desktop
pip install -r requirements.txt

# Copy and configure environment  
cp .env.example .env
# Update CORE_API_URL if needed

# Run the agent
python agent.py
```

The agent will:
- Auto-enroll with Core API
- Send heartbeats every 5 seconds
- Listen for NATS control messages
- Register hotkey: **Ctrl+Shift+R** for emergency blackout

### 4. Test NATS Messaging

```bash
cd phase1/core
python nats_example.py
# Choose option 3 to run both subscriber and publisher
```

This demonstrates the event-driven messaging system between components.

### 5. Setup Android Agent (Optional)

1. Open `phase1/agent-android/` in Android Studio
2. Update `DEFAULT_CORE_API_URL` in `RikaRepository.kt` to your PC's IP
3. Build and install the APK
4. Grant required permissions
5. Start the agent service

## 🔧 Configuration Details

### Core API Configuration (.env)
```bash
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
TOKEN_EXPIRY_MINUTES=5
NATS_USER=rika_nats
NATS_PASSWORD=NatsMsg2025RikaCore789
```

### Desktop Agent Configuration (.env)
```bash
CORE_API_URL=http://localhost:8000
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
```

### Android Agent Configuration
Edit `RikaRepository.kt`:
```kotlin
private const val DEFAULT_CORE_API_URL = "http://192.168.1.100:8000"
```
Replace `192.168.1.100` with your PC's actual IP address.

## 🏗️ API Endpoints

### Device Enrollment
```
POST /enroll
POST /enroll/complete
```

### Monitoring
```
POST /heartbeat
GET /presence  
GET /health
```

### Control
```
POST /blackout
```

## 📊 Database Schema

The Core API automatically creates these tables:

- **devices** - Enrolled device information
- **sessions** - Active device sessions with tokens
- **enrollment_tokens** - Temporary enrollment tokens
- **logs** - System activity logging

## 🔄 NATS Message Flow

### Subjects Used:
- `presence.updated` - Device status changes
- `handoff.requested` - Cross-device handoffs  
- `control.granted` - Device control transfers
- `blackout` - Emergency shutdown events
- `device.{device_id}.control` - Device-specific commands

### Example Messages:
```json
{
  "subject": "blackout",
  "data": {
    "triggered_by": "desktop-001",
    "reason": "Manual blackout via hotkey",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

## 🧪 Testing the System

### 1. Verify Core API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/presence
```

### 2. Test Device Enrollment
Start the desktop agent and watch the enrollment process:
```
🔐 Starting device enrollment...
✅ Got enrollment token: 1a2b3c4d...
✅ Device enrolled successfully!
   Device ID: desktop_HOSTNAME_USER_20250115103045
```

### 3. Monitor NATS Messages
Run the NATS example in subscriber mode and then trigger actions:
- Start desktop agent (see enrollment events)
- Press Ctrl+Shift+R (see blackout events)  
- Check presence endpoint (see heartbeat data)

### 4. Test Android Integration
- Install Android app
- Verify enrollment in Core API
- Check presence endpoint shows both devices

## ⚠️ Troubleshooting

### Core API Issues
- **Database connection failed**: Check PostgreSQL is running on port 5433
- **NATS connection failed**: Verify NATS credentials and port 4222
- **Import errors**: Run `pip install -r requirements.txt`

### Desktop Agent Issues  
- **Enrollment failed**: Check Core API is running on localhost:8000
- **Module not found**: Install requirements with `pip install -r requirements.txt`
- **Permission denied**: Run as administrator for hotkey registration

### Android Agent Issues
- **Network errors**: Update Core API URL to your PC's IP address
- **Build failures**: Ensure Android Studio and SDK are properly installed
- **Service won't start**: Grant all required permissions in Settings

### NATS Issues
- **Connection refused**: Check NATS container is running
- **Authentication failed**: Verify credentials match docker-compose.yml
- **Messages not received**: Ensure subjects match exactly (case-sensitive)

## 🔐 Security Notes

- All agent communications use session tokens
- Tokens expire after 5 minutes (configurable)
- Device fingerprinting prevents impersonation
- Blackout events immediately terminate all sessions
- All API endpoints validate device ownership

## 🚧 Development Notes

### Adding New Features
1. Add database schema in `api.py` `init_db()`
2. Create API endpoints with proper validation
3. Add NATS event publishing for real-time updates
4. Update agents to handle new message types
5. Test with NATS example script

### Code Structure
- **api.py**: Single-file FastAPI app with all endpoints and database logic
- **agent.py**: Windows agent with asyncio event loop and hotkey support
- **nats_example.py**: Testing tool for message flow validation

## 📋 Next Steps (Future Phases)

Phase 1 provides the foundation for:
- Advanced cross-device handoffs
- Voice command integration  
- Biometric authentication
- Screen sharing capabilities
- AI-powered automation
- Mobile device control
- Smart home integration

## 🎉 Success Criteria

You have successfully completed Phase 1 when:
- [ ] Core API responds to health checks
- [ ] Desktop agent enrolls and sends heartbeats
- [ ] NATS messages flow between components
- [ ] Blackout hotkey triggers system-wide shutdown
- [ ] Presence endpoint shows all connected devices
- [ ] Android agent (if setup) appears in device list

**Phase 1 Complete! 🚀**

Your Rika system now has a working API, database, messaging, and agent foundation ready for advanced features in future phases.