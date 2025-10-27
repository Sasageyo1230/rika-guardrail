# Fixing localhost:5317 - Core API Troubleshooting

## 🚨 Problem: API not accessible at http://localhost:5317

The Atlas UI works fine at http://localhost:5173, but API calls fail because the Core API isn't running on port 5317.

## ✅ Quick Diagnosis

**Run the diagnostic tool first:**
```powershell
cd C:\Users\ebrig\rika-core\phase2.5
.\scripts\diagnose.ps1
```

**Expected output (healthy system):**
```
✅ Port 5317 accessible
✅ Health endpoint responds - Status: healthy  
✅ Selfcheck endpoint responds - Status: healthy
   ✅ database: healthy
   ✅ nats: healthy
   ✅ minio: healthy
   ✅ livekit: configured
✅ UI .env file exists - API URL: http://localhost:5317
✅ PostgreSQL port accessible - Port 5433
✅ Database query successful
✅ Phase 2.5 tables present
```

## 🔧 Solution 1: Start Core API

**Copy-paste command:**
```powershell
cd C:\Users\ebrig\rika-core\phase2.5\core
.\start-core.ps1
```

**Expected output:**
```
Starting Rika Core API on port 5317...
Found Python: Python 3.11.5

Starting Core API with:
  Host: 0.0.0.0
  Port: 5317
  Auto-reload: Enabled

API will be available at:
  http://localhost:5317
  http://localhost:5317/docs (Swagger UI)
  http://localhost:5317/health
  http://localhost:5317/selfcheck

INFO:     Uvicorn running on http://0.0.0.0:5317 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Rika Core API Phase 2.5 started successfully on port 5317
INFO:     Application startup complete.
```

## 🔧 Solution 2: Port Conflict Resolution

**If you see "Port 5317 already in use":**

### Option A: Kill conflicting process
```powershell
# Find what's using the port
Get-NetTCPConnection -LocalPort 5317 | ForEach-Object {
    Get-Process -Id $_.OwningProcess
}

# Kill the process (replace XXXX with actual PID)
Stop-Process -Id XXXX -Force

# Start Core API
.\core\start-core.ps1
```

### Option B: Use alternative port
```powershell
# Start API on port 5318 instead
cd core
python -m uvicorn api:app --host 0.0.0.0 --port 5318 --reload

# Update UI configuration
cd ..\ui
# Edit .env file, change:
# VITE_API_BASE_URL=http://localhost:5318
```

## 🔧 Solution 3: Python/Dependencies Issue

**If Python is missing or dependencies fail:**

```powershell
# Check Python
python --version

# If not found, install from Microsoft Store:
start ms-windows-store://pdp/?ProductId=9NRWMJP3717K

# Install dependencies
cd C:\Users\ebrig\rika-core\phase2.5
.\install-python.bat
```

## 🔧 Solution 4: Database/Infrastructure Issue

**If database is unreachable:**

```powershell
# Start all infrastructure services
cd C:\Users\ebrig\rika-core
docker-compose up -d postgres nats minio n8n

# Wait 30 seconds, then check
docker-compose ps

# Should show all services as healthy
```

## 🧪 Verification Tests

**Test 1: API Health**
```powershell
Invoke-WebRequest http://localhost:5317/health
```
**Expected:** `200 OK` with `{"status":"healthy"}`

**Test 2: API Self-Check**
```powershell
Invoke-RestMethod http://localhost:5317/selfcheck
```
**Expected:** JSON with component status

**Test 3: CORS Test**
```powershell
# Should NOT show CORS errors in browser console
# Open: http://localhost:5173
# Check Network tab - API calls should succeed
```

**Test 4: UI API Connection**
```powershell
# Open browser dev tools, run:
# fetch('/api/presence').then(r => r.json()).then(console.log)
# Should show device list without CORS errors
```

## 🐛 Common Issues and Fixes

### Issue: "Connection refused"
**Fix:** Core API not running
```powershell
.\core\start-core.ps1
```

### Issue: "CORS policy" errors in browser
**Fix:** Check API CORS configuration
- API should allow `http://localhost:5173`
- Check browser network tab for actual error

### Issue: "Module not found" Python errors  
**Fix:** Install dependencies
```powershell
pip install fastapi uvicorn asyncpg asyncio-nats-client
```

### Issue: "Database connection failed"
**Fix:** Start PostgreSQL
```powershell
cd C:\Users\ebrig\rika-core
docker-compose up -d postgres
```

### Issue: API works but UI shows "Network Error"
**Fix:** Check UI environment
```powershell
# Verify ui/.env contains:
cat ui\.env
# Should show: VITE_API_BASE_URL=http://localhost:5317
```

## ✅ Success Checklist

After fixes, you should see:

- [ ] ✅ `http://localhost:5317/health` returns 200 OK
- [ ] ✅ `http://localhost:5317/selfcheck` shows all components healthy
- [ ] ✅ Atlas UI at `http://localhost:5173` loads without errors
- [ ] ✅ Browser network tab shows successful API calls (not CORS errors)
- [ ] ✅ Device list populates in Atlas UI
- [ ] ✅ No red errors in browser console related to API

## 🔄 Automated Fix

**Run diagnostic tool with auto-fix:**
```powershell
.\scripts\diagnose.ps1 -AutoFix
```

This will automatically:
- Kill conflicting processes
- Start Core API if needed
- Create missing .env files
- Start infrastructure services

---

**Still having issues?** Run `.\scripts\diagnose.ps1` and check the output for specific error messages.