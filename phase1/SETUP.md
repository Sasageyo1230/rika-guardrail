# Phase 1 Setup - Step by Step Guide

This guide provides detailed setup instructions for Phase 1 of the Rika Project.

## 🔧 Prerequisites Checklist

- [ ] **Phase 0 Docker Stack Running**
  - PostgreSQL on port 5433
  - NATS on port 4222  
  - All services healthy in `docker-compose ps`

- [ ] **Python 3.9+ Installed**
  - Check: `python --version`
  - Windows: Download from python.org
  - Add to PATH during installation

- [ ] **Git Available**
  - Check: `git --version`

## 📋 Step-by-Step Installation

### Step 1: Verify Phase 0 Services

```powershell
# Navigate to your Phase 0 directory
cd C:\Users\YourName\rika-core

# Check if services are running
docker-compose ps

# Should show all services as "Up" or "healthy"
# If not running:
docker-compose up -d
```

**Expected Output:**
```
Name                   State    Ports
rika-postgres         Up       0.0.0.0:5433->5432/tcp
rika-nats            Up       0.0.0.0:4222->4222/tcp
...
```

### Step 2: Install Core API

```powershell
# Navigate to Core API directory
cd phase1\core

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env

# Edit .env file (use notepad or your preferred editor)
notepad .env
```

**Configure .env file:**
```bash
DATABASE_URL=postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
TOKEN_EXPIRY_MINUTES=5
NATS_USER=rika_nats
NATS_PASSWORD=NatsMsg2025RikaCore789
```

**Start Core API:**
```powershell
python api.py
```

**Verify Core API is Working:**
- Open browser to `http://localhost:8000/docs`
- Test health endpoint: `http://localhost:8000/health`

Keep this terminal open. The API needs to stay running.

### Step 3: Install Desktop Agent

**Open a NEW PowerShell window:**

```powershell
# Navigate to Desktop Agent directory  
cd C:\Users\YourName\rika-core\phase1\agent-desktop

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env

# The default .env should work, but verify:
notepad .env
```

**Configure .env file:**
```bash
CORE_API_URL=http://localhost:8000
NATS_URL=nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222
```

**Start Desktop Agent:**
```powershell
python agent.py
```

**Expected Output:**
```
==================================================
🤖 Rika Desktop Agent v0
==================================================
🔐 Starting device enrollment...
✅ Got enrollment token: a1b2c3d4...
✅ Device enrolled successfully!
   Device ID: desktop_HOSTNAME_USER_20250115103045
   NATS subjects: {...}
✅ Connected to NATS
📡 Subscribed to control channels
⌨️ Hotkey registered: Ctrl+Shift+R for blackout

💚 Agent running... Press Ctrl+C to stop
   Hotkey: Ctrl+Shift+R to trigger blackout

💓 Heartbeat sent - App: explorer.exe
```

### Step 4: Test System Integration

**Test 1: Check Device Presence**
- Open browser to `http://localhost:8000/presence`
- Should show your enrolled desktop device

**Test 2: Test NATS Messaging**

Open a third PowerShell window:
```powershell
cd C:\Users\YourName\rika-core\phase1\core
python nats_example.py
```

Choose option `1` (Subscriber) to listen for messages.

In the Desktop Agent window, press `Ctrl+Shift+R` to trigger blackout. You should see the blackout message in the NATS subscriber.

**Test 3: Verify Database**
- Open pgAdmin: `http://localhost:5050`
- Login with credentials from your Phase 0 .env
- Navigate to `rika_core` database
- Check tables: devices, sessions, enrollment_tokens, logs

### Step 5: Android Agent (Optional)

**Prerequisites:**
- Android Studio installed
- Android device or emulator

**Steps:**
1. Open Android Studio
2. Open project: `phase1/agent-android/`
3. Edit `app/src/main/java/com/rika/agent/data/RikaRepository.kt`
4. Update `DEFAULT_CORE_API_URL` to your PC's IP:
   ```kotlin
   private const val DEFAULT_CORE_API_URL = "http://192.168.1.100:8000"
   ```
   (Replace 192.168.1.100 with your actual IP)
5. Build and run the app
6. Grant all requested permissions
7. Tap "Start Agent"

## ✅ Verification Checklist

After setup, verify these work:

### Core API Verification
- [ ] `http://localhost:8000/health` returns `{"status": "healthy"}`
- [ ] `http://localhost:8000/docs` shows Swagger UI
- [ ] `http://localhost:8000/presence` shows enrolled devices

### Desktop Agent Verification  
- [ ] Agent starts without errors
- [ ] Device enrollment completes successfully
- [ ] Heartbeats send every 5 seconds
- [ ] Hotkey `Ctrl+Shift+R` triggers blackout
- [ ] Agent reconnects if Core API restarts

### NATS Messaging Verification
- [ ] NATS example can connect and publish messages
- [ ] Blackout hotkey publishes to `blackout` subject
- [ ] Messages appear in subscriber console

### Database Verification
- [ ] Tables created automatically: devices, sessions, enrollment_tokens, logs
- [ ] Device appears in `devices` table
- [ ] Active session in `sessions` table
- [ ] Heartbeat activity in `logs` table

### Android Agent Verification (if installed)
- [ ] App builds and installs successfully
- [ ] Device enrollment works from mobile
- [ ] Appears in presence endpoint alongside desktop
- [ ] Emergency blackout button functions

## 🔧 Troubleshooting Common Issues

### "Module not found" errors
```powershell
# Ensure you're in the right directory and install requirements
pip install -r requirements.txt

# If still failing, try:
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Core API won't start
- Check if port 8000 is already in use
- Verify PostgreSQL is running on port 5433
- Check .env file has correct database credentials

### Desktop Agent enrollment fails
- Ensure Core API is running first
- Check firewall isn't blocking localhost:8000
- Verify .env has correct CORE_API_URL

### NATS connection errors
- Check NATS container is running in Docker
- Verify credentials in .env match docker-compose.yml
- Ensure port 4222 is accessible

### Android app network errors
- Update Core API URL to your PC's actual IP address
- Ensure both devices are on same network
- Check Windows Firewall allows incoming connections on port 8000

### Database connection issues
- Verify PostgreSQL container is healthy: `docker-compose ps`
- Check if database exists: Connect via pgAdmin
- Try recreating database: `docker-compose down` then `docker-compose up -d`

## 🎯 Success Indicators

You've successfully completed Phase 1 setup when:

1. **Core API Dashboard**: Shows green health status
2. **Desktop Agent Console**: Shows regular heartbeat messages  
3. **NATS Subscriber**: Receives messages when you trigger blackout
4. **Presence Endpoint**: Lists your enrolled device(s)
5. **Database Tables**: Contain device and session data

**🎉 Congratulations! Phase 1 is now fully operational.**

## 📞 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Review log output for specific error messages
4. Ensure Phase 0 Docker services are healthy
5. Try restarting components in order: Core API → Desktop Agent → Tests

## 🚀 Next Steps

With Phase 1 working, you can:
- Explore the API documentation at `http://localhost:8000/docs`
- Experiment with NATS messaging patterns
- Build custom integrations using the enrollment and heartbeat APIs
- Plan advanced features for future phases