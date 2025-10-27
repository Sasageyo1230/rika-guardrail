# Rika Phase 2 - Atlas & Linking System

**Phase 2** introduces the Atlas Dashboard and device linking system with minimal UI (10/90 input/output split). Devices run in background heartbeat mode, but can be explicitly "linked" to enable screen sharing, extended screens, remote control, and gesture commands.

## 🎯 Phase 2 Deliverables

✅ **Core API Expansion** - Link/unlink endpoints, TTL management, hands-on mode
✅ **Database Schema Updates** - Device links, hands-on sessions, automatic cleanup
✅ **Agent Behavior Updates** - View mode thumbnails, control mode, gesture recognition
✅ **Atlas Dashboard** - React UI for device management and linking
✅ **Hands-On Mode** - MediaPipe gesture recognition with grab, throw, swipe actions
✅ **MinIO Storage** - Automated thumbnail storage with lifecycle policies

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Atlas UI      │    │   Core API      │    │   MinIO Store   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (S3-compat)   │
│   Port 3000     │    │   Port 8000     │    │   Port 9000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                        ▲
         │                        │ NATS Events
         │                        ▼
         │              ┌─────────────────┐
         │              │   NATS Server   │
         │              │   Port 4222     │
         │              └─────────────────┘
         │                        ▲
         │                        │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ Desktop     │    │  Android    │    │   Other     │
    │ Agent       │◄──►│  Agent      │◄──►│   Agents    │
    │ (Windows)   │    │ (Mobile)    │    │   (Future)  │
    └─────────────┘    └─────────────┘    └─────────────┘
```

## 📁 Project Structure

```
rika-core/phase2/
├── core/                           # Core API Service (Phase 2)
│   ├── api.py                      # Enhanced FastAPI with linking endpoints
│   ├── minio_setup.py             # MinIO bucket setup and policies
│   ├── cleanup_script.py          # Automated cleanup and maintenance
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Configuration template
├── agent-desktop/                  # Enhanced Desktop Agent
│   ├── agent.py                   # Windows agent with linking & gestures
│   ├── requirements.txt           # Python dependencies (+ OpenCV, MediaPipe)
│   └── .env.example               # Configuration template
├── agent-android/                  # Enhanced Android Agent
│   └── app/src/main/              # Android agent with linking support
├── ui/                            # Atlas Dashboard (React)
│   ├── src/
│   │   ├── App.tsx               # Main dashboard application
│   │   ├── services/api.ts       # API client for Core API
│   │   └── components/           # UI components
│   ├── package.json              # Node.js dependencies
│   └── .env.example              # Configuration template
└── README.md                     # This file
```

## 🚀 Quick Start Guide

### Prerequisites
- Phase 1 completed and working (Core API, agents, database)
- Phase 0 Docker stack running (PostgreSQL, NATS, MinIO)
- Node.js 18+ for Atlas Dashboard
- Python 3.9+ with OpenCV/MediaPipe support

### 1. Start Phase 0 Services

Ensure your Docker Compose stack is running:
```powershell
cd rika-core
docker-compose up -d

# Verify services
docker-compose ps
```

### 2. Setup Enhanced Core API

```powershell
cd phase2/core
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
# Edit .env with your credentials

# Setup MinIO storage
python minio_setup.py

# Run the enhanced API server
python api.py
```

**New API Endpoints:**
- `POST /link` - Link device with mode and TTL
- `POST /unlink` - Unlink device(s)
- `GET /links` - List active links
- `POST /hands-on` - Toggle gesture mode

### 3. Setup Enhanced Desktop Agent

```powershell
cd phase2/agent-desktop
pip install -r requirements.txt

# Copy configuration
copy .env.example .env
# Update MINIO_* settings if needed

# Run enhanced agent
python agent.py
```

**New Features:**
- **View Mode**: Captures thumbnails every 5s → MinIO
- **Control Mode**: Enables remote input injection
- **Hands-On Mode**: MediaPipe gesture recognition
- **Hotkeys**: Ctrl+Shift+H for hands-on toggle

### 4. Setup Atlas Dashboard

```powershell
cd phase2/ui
npm install

# Copy configuration
copy .env.example .env
# Update VITE_API_URL if needed

# Start development server
npm run dev
```

**Atlas Dashboard**: `http://localhost:3000`
- Device grid with link status
- Link modal with mode/TTL/gestures
- Global controls (unlink all, blackout)
- Real-time updates every 5 seconds

### 5. Test the System

#### Test Device Linking:
1. Open Atlas Dashboard: `http://localhost:3000`
2. Ensure desktop agent is online and visible
3. Click "Link" on your device card
4. Select "View" mode, 30 minutes TTL, enable gestures
5. Click "Link Device"
6. Verify device shows as linked with thumbnail uploads

#### Test Hands-On Mode:
1. In Atlas, click "Hands On" on a linked device
2. Or press `Ctrl+Shift+H` in desktop agent
3. Camera should activate for gesture recognition
4. Try gestures:
   - **Closed fist** (grab): Detected and logged
   - **Open hand** (throw): Triggers handoff logic
   - **Swipe down**: Triggers blackout event

#### Test Global Controls:
1. Click "Unlink All Devices" in Atlas sidebar
2. Click "🚨 EMERGENCY BLACKOUT" to test system shutdown
3. Verify all agents receive blackout event and shut down

## 🔧 Configuration Details

### Core API Environment (.env)
```bash
# Database and NATS (from Phase 1)
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
TOKEN_EXPIRY_MINUTES=5

# MinIO Storage (Phase 2)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=rikaadmin
MINIO_SECRET_KEY=RikaMinIO2025SecureStorage
MINIO_BUCKET=rika-screenshots
```

### Desktop Agent Environment (.env)
```bash
# Core API connection
CORE_API_URL=http://localhost:8000
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222

# MinIO for thumbnails
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=rikaadmin
MINIO_SECRET_KEY=RikaMinIO2025SecureStorage
MINIO_BUCKET=rika-screenshots
```

### Atlas Dashboard Environment (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## 📊 New Database Schema (Phase 2)

### device_links
```sql
CREATE TABLE device_links (
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    mode VARCHAR(20) CHECK (mode IN ('view', 'extend', 'control')),
    gestures_enabled BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id)
);
```

### hands_on_sessions  
```sql
CREATE TABLE hands_on_sessions (
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT false,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id)
);
```

## 🔄 Linking Modes Explained

### 1. View Mode
- **Purpose**: Live monitoring with minimal overhead
- **Behavior**: Captures screenshot thumbnails every 5 seconds
- **Storage**: Uploads to MinIO as `thumbnails/{device_id}/latest.jpg`
- **UI**: Shows thumbnail in Atlas device card
- **Cleanup**: Automatic 48-hour TTL, keeps last 10 per device

### 2. Extend Mode (Skeleton)
- **Purpose**: Use device as extended display
- **Behavior**: Would integrate with LiveKit for full streaming
- **Current**: Shows placeholder message
- **Future**: Real-time screen casting and input forwarding

### 3. Control Mode (Skeleton)
- **Purpose**: Remote input injection
- **Behavior**: Enables mouse/keyboard control via API
- **Current**: Shows enabled status
- **Future**: WebRTC for low-latency remote control

## 👋 Hands-On Mode & Gestures

### Gesture Recognition
- **Library**: MediaPipe Hands
- **Camera**: Device primary camera
- **Processing**: Real-time hand landmark detection

### Supported Gestures:
- **Grab (Closed Fist)**: Prepare for handoff action
- **Throw (Open Hand)**: Execute handoff to nearest linked device  
- **Swipe Down**: Immediate blackout trigger

### Voice Integration (Future):
- "Rika, Hands On Mode" → Toggle gesture recognition
- "Rika, Link Desktop" → Link device in view mode
- "Rika, Blackout" → Emergency shutdown

## 🗄️ Storage & Cleanup

### MinIO Lifecycle Policies:
- **Thumbnails**: 48-hour automatic deletion
- **Gestures**: 7-day automatic deletion (future recordings)
- **Per-device limit**: Keep only last 10 thumbnails

### Automated Cleanup Script:
```powershell
cd phase2/core
python cleanup_script.py
```

**Cleanup Tasks:**
- Remove expired device links
- Delete old inactive sessions (30+ days)
- Clean up old log entries (7+ days)  
- Enforce per-device thumbnail limits
- Generate system statistics

### Storage Monitoring:
```powershell
# Check MinIO bucket contents
python minio_setup.py

# Run cleanup and see stats
python cleanup_script.py
```

## 🔐 Security & TTL Management

### Link TTL (Time to Live):
- **Range**: 10-60 minutes (configurable in Atlas UI)
- **Enforcement**: Automatic database cleanup every 30 seconds
- **Events**: Publishes `link.removed` on expiry
- **Behavior**: Agents stop linking activities when TTL expires

### Session Management:
- **Blackout**: Immediately revokes all sessions and links
- **Link Expiry**: Graceful shutdown of linking activities
- **Hands-On**: Separate toggle, requires active link

### Data Protection:
- **Thumbnails**: Automatic cleanup prevents accumulation
- **Credentials**: Never logged or exposed in UI
- **Fingerprints**: Device identification, not tracking

## 🧪 Testing Scenarios

### 1. Link Lifecycle Test
```powershell
# Terminal 1: Start Core API
cd phase2/core
python api.py

# Terminal 2: Start Desktop Agent
cd phase2/agent-desktop
python agent.py

# Terminal 3: Start Atlas Dashboard
cd phase2/ui
npm run dev
```

**Steps:**
1. Open `http://localhost:3000`
2. Link desktop device in "view" mode, 15 minutes
3. Verify thumbnails appear in Atlas
4. Wait for TTL expiry, verify auto-unlink
5. Re-link in "control" mode with gestures
6. Test hands-on mode activation

### 2. Storage Test
```powershell
# Check initial state
cd phase2/core
python minio_setup.py

# Let agent run with view mode for 5 minutes
# Check storage accumulation

# Run cleanup
python cleanup_script.py

# Verify cleanup worked
python minio_setup.py
```

### 3. Gesture Test
```powershell
# Link device with gestures enabled
# Press Ctrl+Shift+H to activate hands-on mode
# Try gestures in front of camera:
# - Make fist → See "Grab gesture detected"
# - Open hand → See "Throw gesture detected"  
# - Swipe down → Triggers blackout
```

### 4. Multi-Device Test
```powershell
# If you have Android agent setup:
# 1. Link both desktop and Android in view mode
# 2. See both thumbnails in Atlas
# 3. Test unlink all → Both should unlink
# 4. Test blackout → Both agents should shut down
```

## ⚠️ Troubleshooting

### Core API Issues
- **Database errors**: Check PostgreSQL container is healthy
- **MinIO errors**: Verify MinIO container and credentials
- **Link cleanup not working**: Check background task is running

### Agent Issues  
- **Thumbnail upload fails**: Check MinIO connectivity and bucket exists
- **Gesture recognition fails**: Verify camera access and MediaPipe install
- **Link events not received**: Check NATS connection and subscription

### Atlas Dashboard Issues
- **API calls fail**: Check VITE_API_URL points to correct Core API
- **Real-time updates stop**: Check if Core API is reachable
- **Link modal errors**: Verify device exists and is online

### Storage Issues
- **Thumbnails accumulating**: Run cleanup script manually
- **MinIO out of space**: Check lifecycle policies are active
- **Upload permissions**: Verify MinIO credentials and bucket access

## 📈 Performance Notes

### Resource Usage:
- **View Mode**: ~100KB per thumbnail, 5s interval = ~720KB/hour per device
- **Gesture Recognition**: ~10-15% CPU when active, camera dependent
- **Atlas Dashboard**: Polls every 5s, minimal bandwidth
- **Database**: Links table stays small with TTL cleanup

### Scaling Considerations:
- **10 devices**: ~7MB/hour thumbnails, manageable
- **100 devices**: ~70MB/hour, monitor storage closely
- **Cleanup frequency**: Increase if dealing with many short-lived links

## 🚧 Known Limitations (Phase 2)

### Current Skeleton Features:
- **Extend Mode**: Shows placeholder, no real LiveKit integration
- **Control Mode**: Shows status, no actual input injection
- **Android Gestures**: No MediaPipe integration yet
- **Voice Commands**: Not implemented

### Future Enhancements (Phase 3+):
- WebRTC for low-latency control mode
- LiveKit integration for extend mode
- Mobile gesture recognition
- Cross-device handoff automation
- Biometric authentication
- Smart home integration

## ✅ Success Criteria

Phase 2 is working correctly when:

### Core Functionality:
- [ ] Atlas Dashboard loads and shows devices
- [ ] Can link/unlink devices through UI
- [ ] TTL countdown shows and auto-expires
- [ ] Global blackout shuts down all agents

### Linking Modes:
- [ ] View mode uploads thumbnails to MinIO
- [ ] Control mode shows as enabled
- [ ] Hands-on mode activates camera
- [ ] Gesture recognition detects basic poses

### Storage & Cleanup:
- [ ] MinIO bucket created with lifecycle policies
- [ ] Thumbnails overwrite latest.jpg per device
- [ ] Cleanup script removes expired data
- [ ] Storage stats show current usage

### Agent Integration:
- [ ] Agents respond to link/unlink events
- [ ] Heartbeats include linking status
- [ ] Hotkeys work for hands-on toggle
- [ ] Graceful shutdown on blackout

**🎉 Phase 2 Complete! You now have a working Atlas & Linking system ready for advanced features in Phase 3.**

## 📞 Getting Help

If you encounter issues:
1. Check Phase 1 is working correctly first
2. Verify all Phase 0 services are healthy
3. Review configuration files match examples
4. Check logs for specific error messages
5. Test components individually before integration
6. Use cleanup script to reset system state if needed