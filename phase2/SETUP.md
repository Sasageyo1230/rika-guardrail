# Phase 2 Setup Guide - Step-by-Step Installation

This guide provides detailed, beginner-friendly setup instructions for Phase 2 of the Rika Project.

## 🔧 Prerequisites Checklist

- [ ] **Phase 1 Working**
  - Core API responding on `http://localhost:8000`
  - Desktop agent enrolling and sending heartbeats
  - Database with device records
  - NATS messaging functional

- [ ] **Phase 0 Docker Stack Healthy**
  - PostgreSQL on port 5433
  - NATS on port 4222
  - **MinIO on port 9000** (required for Phase 2)

- [ ] **Additional Software**
  - Python 3.9+ with pip
  - Node.js 18+ with npm
  - Windows camera (for gesture recognition)

## 📋 Step-by-Step Installation

### Step 1: Verify Prerequisites

```powershell
# Check Phase 0 services
cd C:\Users\YourName\rika-core
docker-compose ps

# Should show ALL services including MinIO as "Up"
# If MinIO is missing, update your docker-compose.yml from Phase 0

# Test Phase 1 Core API
curl http://localhost:8000/health
# Should return {"status": "healthy", ...}

# Test existing agent
cd phase1\agent-desktop
python agent.py
# Should enroll and send heartbeats (Ctrl+C to stop)
```

**Expected Output:**
```
Name                   State    Ports
rika-postgres         Up       0.0.0.0:5433->5432/tcp
rika-nats            Up       0.0.0.0:4222->4222/tcp
rika-minio           Up       0.0.0.0:9000->9000/tcp
...
```

### Step 2: Setup Enhanced Core API

```powershell
cd C:\Users\YourName\rika-core\phase2\core

# Install new dependencies (OpenCV, MediaPipe, MinIO)
pip install -r requirements.txt
```

**If pip install fails:**
```powershell
# Update pip first
python -m pip install --upgrade pip

# Install problematic packages individually
pip install opencv-python==4.8.1.78
pip install mediapipe==0.10.8
pip install minio==7.2.0

# Then install the rest
pip install -r requirements.txt
```

**Configure environment:**
```powershell
# Copy configuration template
copy .env.example .env

# Edit .env file
notepad .env
```

**Required .env settings:**
```bash
# Database and NATS (same as Phase 1)
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
TOKEN_EXPIRY_MINUTES=5

# MinIO storage (new in Phase 2)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=rikaadmin
MINIO_SECRET_KEY=RikaMinIO2025SecureStorage
MINIO_BUCKET=rika-screenshots
```

**Setup MinIO storage:**
```powershell
# This creates the bucket and sets up cleanup policies
python minio_setup.py
```

**Expected Output:**
```
==================================================
🗄️ Rika MinIO Setup - Phase 2
==================================================

1. Testing MinIO connectivity...
✅ MinIO connectivity test passed

2. Setting up bucket and policies...
✅ Created bucket: rika-screenshots
✅ Lifecycle policies configured:
   - Thumbnails: 48 hour TTL
   - Gestures: 7 day TTL

3. Getting storage statistics...
   Thumbnails: 0 files, 0 bytes
   Gestures: 0 files, 0 bytes
   Total: 0 files, 0 bytes

✅ MinIO setup completed successfully!
```

**Start the enhanced Core API:**
```powershell
python api.py
```

**Verify it's working:**
- Core API: `http://localhost:8000/docs`
- New endpoints should be visible: `/link`, `/unlink`, `/links`, `/hands-on`
- Health check: `http://localhost:8000/health`

**Keep this terminal open.**

### Step 3: Setup Enhanced Desktop Agent

**Open a NEW PowerShell window:**

```powershell
cd C:\Users\YourName\rika-core\phase2\agent-desktop

# Install enhanced dependencies
pip install -r requirements.txt
```

**If OpenCV/MediaPipe installation fails:**
```powershell
# Try installing with conda if available
conda install opencv
conda install -c conda-forge mediapipe

# Or use pre-compiled wheels
pip install --only-binary=all opencv-python mediapipe
```

**Configure environment:**
```powershell
copy .env.example .env
notepad .env
```

**Required .env settings:**
```bash
CORE_API_URL=http://localhost:8000
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=rikaadmin
MINIO_SECRET_KEY=RikaMinIO2025SecureStorage
MINIO_BUCKET=rika-screenshots
```

**Start enhanced desktop agent:**
```powershell
python agent.py
```

**Expected Output:**
```
==================================================
🤖 Rika Desktop Agent v2 - Phase 2
==================================================
✅ Loaded saved credentials for device desktop_HOSTNAME_USER_...
✅ Connected to MinIO at localhost:9000
✅ Connected to NATS
📡 Subscribed to control channels

💚 Agent running... Press Ctrl+C to stop
   Hotkeys: Ctrl+Shift+R (blackout), Ctrl+Shift+H (hands-on)

💓 Heartbeat sent - App: explorer.exe
```

**Keep this terminal open.**

### Step 4: Setup Atlas Dashboard

**Open a THIRD PowerShell window:**

```powershell
cd C:\Users\YourName\rika-core\phase2\ui

# Install Node.js dependencies
npm install
```

**If npm install fails:**
```powershell
# Clear npm cache
npm cache clean --force

# Try with different registry
npm install --registry https://registry.npmjs.org/

# Or install dependencies individually
npm install react react-dom vite @vitejs/plugin-react
npm install axios lucide-react date-fns @tanstack/react-query
npm install tailwindcss autoprefixer postcss
```

**Configure environment:**
```powershell
copy .env.example .env
notepad .env
```

**Required .env setting:**
```bash
VITE_API_URL=http://localhost:8000
```

**Start Atlas Dashboard:**
```powershell
npm run dev
```

**Expected Output:**
```
  VITE v4.5.0  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.1.100:3000/
  ➜  press h to show help
```

**Open Atlas Dashboard:** `http://localhost:3000`

### Step 5: Test the Complete System

#### Test 1: Verify Atlas Dashboard
1. Atlas should load showing your desktop device
2. Device should show as "online" with green status
3. Recent activity should show current app
4. Global controls should be visible in sidebar

**If Atlas shows "Loading..." forever:**
- Check Core API is running on port 8000
- Check .env has correct VITE_API_URL
- Check browser dev tools for CORS errors

#### Test 2: Link Device in View Mode
1. Click "Link" button on your device card
2. Select "View" mode, 30 minutes TTL
3. Enable "Gesture Controls" checkbox
4. Click "Link Device"
5. Device card should update to show linked status
6. Thumbnail placeholder should appear

**Expected behavior in agent terminal:**
```
🔗 Device linked in view mode
   Gestures enabled: true
   Expires at: 2025-01-15T11:30:00.000Z
📸 Starting thumbnail capture loop
📸 Thumbnail uploaded: thumbnails/device-id/latest.jpg
```

#### Test 3: Activate Hands-On Mode
1. In Atlas, click "Hands On" button on linked device
2. Or in agent terminal, press `Ctrl+Shift+H`
3. Camera should activate (you may see security prompt)
4. Agent should show gesture recognition starting

**Expected behavior:**
```
👋 Hands-on mode enabled
👋 Starting gesture recognition loop
```

#### Test 4: Test Gestures
1. Make sure hands-on mode is active
2. Position yourself in front of camera
3. Try these gestures:
   - **Make a fist**: Should see "👊 Grab gesture detected"
   - **Open your hand**: Should see "🤚 Throw gesture detected"
   - **Swipe down with index/middle fingers**: Should see "👇 Swipe down gesture - triggering blackout"

**Note:** Gesture recognition requires good lighting and clear hand visibility.

#### Test 5: Test Global Controls
1. In Atlas sidebar, click "Unlink All Devices"
2. Verify device becomes unlinked
3. Re-link the device
4. Click "🚨 EMERGENCY BLACKOUT"
5. All agents should shut down immediately

## ✅ Verification Checklist

After setup, verify these work:

### Core API (Phase 2)
- [ ] `http://localhost:8000/health` shows healthy status
- [ ] `http://localhost:8000/docs` shows new Phase 2 endpoints
- [ ] `http://localhost:8000/presence` shows devices with link status
- [ ] `http://localhost:8000/links` returns empty array (no links yet)

### Atlas Dashboard
- [ ] `http://localhost:3000` loads without errors
- [ ] Shows enrolled devices from Phase 1
- [ ] Device status updates in real-time
- [ ] Link modal opens and closes correctly
- [ ] Global controls are visible

### Enhanced Desktop Agent
- [ ] Starts without errors and connects to all services
- [ ] Shows MinIO connection success
- [ ] Responds to linking events from Atlas
- [ ] New hotkey `Ctrl+Shift+H` works
- [ ] Camera activates for hands-on mode

### MinIO Storage
- [ ] MinIO UI accessible at `http://localhost:9000` (if configured)
- [ ] Bucket `rika-screenshots` exists
- [ ] Thumbnails upload during view mode
- [ ] Cleanup script runs without errors

### Complete Integration
- [ ] Link device through Atlas → agent receives event
- [ ] View mode → thumbnails appear in MinIO
- [ ] Hands-on mode → camera activates
- [ ] Gesture recognition → console shows detections
- [ ] Unlink → agent stops activities
- [ ] Blackout → all components shut down

## 🔧 Common Issues & Solutions

### "pip install opencv-python fails"
```powershell
# Try with pre-compiled wheels only
pip install --only-binary=all opencv-python

# Or use conda if available
conda install -c conda-forge opencv

# Or install older version
pip install opencv-python==4.7.0.72
```

### "npm install fails with network errors"
```powershell
# Use different npm registry
npm config set registry https://registry.npmjs.org/

# Clear cache and retry
npm cache clean --force
npm install
```

### "MinIO connection failed"
```powershell
# Check MinIO container is running
docker-compose ps | findstr minio

# Check MinIO is accessible
curl http://localhost:9000/minio/health/live

# Reset MinIO data if needed
docker-compose down
docker volume rm rika-core_minio_data
docker-compose up -d
```

### "Atlas shows no devices"
1. Check Core API is running: `http://localhost:8000/presence`
2. Verify agent enrolled successfully in Phase 1
3. Check CORS errors in browser dev tools
4. Confirm .env VITE_API_URL is correct

### "Camera won't activate for gestures"
1. Check camera permissions in Windows Settings
2. Close other apps using camera (Zoom, Teams, etc.)
3. Try pressing `Ctrl+Shift+H` to toggle hands-on mode
4. Check agent terminal for MediaPipe errors

### "Gesture recognition doesn't work"
1. Ensure good lighting
2. Position hands clearly in camera view
3. Make distinct gestures (closed fist vs open hand)
4. Check MediaPipe installation: `pip show mediapipe`

### "Thumbnails not uploading"
1. Check MinIO credentials in agent .env
2. Verify bucket exists: `python minio_setup.py`
3. Check agent terminal for MinIO errors
4. Ensure device is linked in "view" mode

## 🧪 Advanced Testing

### Test TTL Expiry
```powershell
# Link device with 1 minute TTL
# Wait 61 seconds
# Verify automatic unlink occurs
# Check agent stops thumbnail uploads
```

### Test Cleanup Script
```powershell
cd phase2/core

# Create some test data by linking/unlinking
# Run cleanup to see it working
python cleanup_script.py

# Should show statistics and cleanup results
```

### Test Multiple Devices
```powershell
# If you have Android agent or second Windows machine:
# Enroll multiple devices
# Link multiple in view mode  
# See all thumbnails in MinIO
# Test unlink all affects all devices
```

### Load Testing
```powershell
# Link device in view mode
# Let run for 10 minutes
# Check MinIO storage growth
# Verify cleanup policies working
# Monitor system resources
```

## 📊 Monitoring & Maintenance

### Regular Health Checks
```powershell
# Check API health
curl http://localhost:8000/health

# Check storage usage
cd phase2/core
python minio_setup.py

# Run cleanup
python cleanup_script.py
```

### Log Monitoring
- **Core API**: Console output shows link/unlink events
- **Desktop Agent**: Shows linking status in heartbeat
- **Atlas Dashboard**: Browser dev tools for client errors
- **MinIO**: Object creation/deletion in bucket

### Performance Monitoring
- **Database**: Query `SELECT COUNT(*) FROM device_links;`
- **Storage**: Check MinIO bucket size growth
- **Network**: Monitor NATS message frequency
- **System**: CPU usage during gesture recognition

## 🎯 Success Indicators

You've successfully completed Phase 2 setup when:

1. **Atlas Dashboard loads and shows devices with correct status**
2. **Can link/unlink devices and see real-time status changes**
3. **View mode uploads thumbnails that you can verify in MinIO**
4. **Hands-on mode activates camera and detects basic gestures**
5. **Global blackout shuts down all components immediately**
6. **TTL countdown works and auto-expires links**
7. **Cleanup script runs without errors and shows statistics**

**🎉 Congratulations! Phase 2 is now fully operational with Atlas & Linking system.**

## 📞 Getting Additional Help

If you encounter issues not covered here:
1. Check the main Phase 2 README.md for detailed architecture
2. Review error messages carefully - they often indicate exactly what's wrong
3. Test components individually before testing integration
4. Use cleanup script to reset system state if needed
5. Verify Phase 1 still works before troubleshooting Phase 2 issues

## 🚀 What's Next?

With Phase 2 working, you can:
- Experiment with different linking modes and TTL values
- Monitor storage usage patterns
- Plan Phase 3 enhancements (WebRTC, LiveKit, voice commands)
- Integrate additional device types or platforms
- Build custom automation on top of the Atlas API