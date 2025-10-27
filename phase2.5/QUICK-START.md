# 🚀 Phase 2.5 Quick Start Guide

## Your Current Status
- ✅ Infrastructure running (PostgreSQL, NATS, n8n)
- ✅ Database tables created
- ✅ LiveKit account created
- ✅ n8n workflow file located
- ⚠️ Python dependencies need fixing

## Step 1: Configure LiveKit

Update `.env` file with your LiveKit credentials:

```bash
# Edit the file: C:\Users\ebrig\rika-core\phase2.5\.env
LIVEKIT_URL=wss://your-project-xxxxx.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx  
LIVEKIT_SECRET_KEY=secret-xxxxxxxxxxxxx
```

## Step 2: Import n8n Workflow

1. Open n8n: http://localhost:5678
2. Click **Workflows** → **Import from File**
3. Select file: `C:\Users\ebrig\rika-core\phase2.5\n8n\rika-control-approval-flow.json`
4. Click **Import** then **Activate**

## Step 3: Python Installation (Try These Options)

### Option A: Simple Batch File
```batch
cd C:\Users\ebrig\rika-core\phase2.5
install-python.bat
```

### Option B: Install Python from Microsoft Store
1. Open Microsoft Store
2. Search for "Python 3.11" or "Python 3.12"
3. Click Install
4. Then run the batch file above

### Option C: Manual Essential Packages Only
```batch
pip install fastapi uvicorn
pip install pynput
```

## Step 4: Start What You Can

### Start the UI (No Python Required!)
```batch
cd C:\Users\ebrig\rika-core\phase2.5\ui
npm run dev
```

Open: http://localhost:5173

### If Python Works, Also Start:
```batch
# Terminal 1 - Core API
cd C:\Users\ebrig\rika-core\phase2.5\core
python api.py

# Terminal 2 - Desktop Agent (Run as Administrator)
cd C:\Users\ebrig\rika-core\phase2.5\agent-desktop
python agent.py
```

## What You Can Test Right Now

Even without Python, you can:
1. **View the Atlas Dashboard UI** at http://localhost:5173
2. **See the enhanced device cards** with streaming/control buttons
3. **View the control request modal** interface
4. **Browse the stream viewer** component

## Troubleshooting Python

If `pip install` fails, try:

1. **Check Python version**: `python --version`
2. **Upgrade pip**: `python -m pip install --upgrade pip`
3. **Install with user flag**: `pip install --user fastapi`
4. **Use Python directly**: `python -m pip install fastapi`

## Working Services Right Now

- 🟢 **PostgreSQL**: http://localhost:5050 (pgAdmin)
- 🟢 **NATS**: http://localhost:8222 (Monitor)
- 🟢 **n8n**: http://localhost:5678 (Workflows)
- 🟢 **UI**: http://localhost:5173 (After npm run dev)

## Files You Need

- **n8n Workflow**: `C:\Users\ebrig\rika-core\phase2.5\n8n\rika-control-approval-flow.json`
- **Environment Config**: `C:\Users\ebrig\rika-core\phase2.5\.env`
- **Python Install Helper**: `C:\Users\ebrig\rika-core\phase2.5\install-python.bat`

## Success Checklist

- [ ] LiveKit credentials added to .env
- [ ] n8n workflow imported and activated
- [ ] UI running at http://localhost:5173
- [ ] Python dependencies installed (optional for full functionality)
- [ ] Core API running (requires Python)
- [ ] Desktop Agent running (requires Python + Admin)

You're very close! Focus on getting the UI running first, then tackle Python.