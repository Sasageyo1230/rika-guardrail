# Rika Phase 3.3 Quick Start Guide

## Complete Windows PowerShell 5.1 Compatible Solution

**✅ ZERO venv activation references**  
**✅ Auto-detects Python entrypoints (main.py, api.py, app.py)**  
**✅ Sets correct API URL (VITE_API_BASE_URL=http://localhost:5317)**  
**✅ PowerShell 5.1 compatible (single-child Join-Path only)**  

---

## Scripts Created

| Script | Purpose | Size |
|--------|---------|------|
| **setup.ps1** | Project setup & dependency installation | 9,417 bytes |
| **start-dev.ps1** | Development server startup | 6,674 bytes |
| **start-prod.ps1** | Production server startup | 6,413 bytes |
| **test.ps1** | Service health checks | 5,372 bytes |
| **diagnose.ps1** | System validation | 4,785 bytes |

---

## Single-Line Command

```powershell
cd C:\Users\ebrig\rika-core; if (-not $env:VIRTUAL_ENV) { .\.venv\Scripts\Activate.ps1 }; cd .\phase3.3\scripts; .\run-diagnostic.bat; .\setup.ps1; .\start-dev.ps1
```

---

## What Each Script Does

### 🚀 setup.ps1
- **NO venv activation** (assumes environment already active)
- Creates required directories (logs, data, config, temp)
- Installs Python requirements with `python -m pip`
- Configures UI with VITE_API_BASE_URL=http://localhost:5317
- Auto-detects service entrypoints (main.py, api.py, app.py)
- Shows service discovery results

### 🎯 start-dev.ps1
- Starts development servers with auto-reload
- **NO venv activation** (uses existing environment)
- Auto-detects Python modules for each service
- Starts services on designated ports:
  - Core API: 5317
  - Overseer: 5319
  - Great Sage: 5320
  - Research Vault: 5321
  - Atlas UI: 5173
- Opens browser to Atlas UI automatically

### 🏭 start-prod.ps1
- Starts production servers in background
- Logs all output to individual log files
- **NO venv activation** 
- Hidden window mode for clean deployment

### 🔍 test.ps1
- Health checks for all running services
- Tests standard endpoints (/health, /status, /)
- Provides pass/fail summary with statistics
- Exit codes for CI/CD integration

### 🔧 diagnose.ps1
- Validates PowerShell 5.1 compatibility
- Scans entire repository for Activate.ps1 references
- Verifies all required scripts exist
- Checks tool versions (Node.js, Python, Git)
- Confirms directory structure

---

## Key Features

### ✅ Zero Activation Issues
- No `Activate.ps1` calls anywhere in main scripts
- Assumes user has already activated their environment
- Warns if no virtual environment detected

### ✅ PowerShell 5.1 Compatible
- Uses single-child `Join-Path` only
- Avoids modern PowerShell syntax
- Compatible with Windows 10 default PowerShell

### ✅ Auto-Detection
- Automatically finds Python entrypoints
- Falls back gracefully if not found
- Provides helpful hints for missing files

### ✅ Service Ports
- Core API: 5317 (main API endpoint)
- Overseer: 5319
- Great Sage: 5320  
- Research Vault: 5321
- Atlas UI: 5173 (Vite dev server)

---

## Validation Results

```
==== Script Verification ====
[OK] setup.ps1 exists 
[OK] start-dev.ps1 exists 
[OK] start-prod.ps1 exists 
[OK] test.ps1 exists 
[OK] diagnose.ps1 exists 

==== Activation Reference Check ====
[PASS] No Activate.ps1 references found in scripts

==== Summary ====
All 5 PowerShell scripts created successfully
No venv activation references in main scripts  
Scripts are Windows PowerShell 5.1 compatible
Ready to use Phase 3.3 scripts
```

---

## Next Steps

1. **Run the single-line command above**
2. **Or step by step:**
   ```powershell
   cd C:\Users\ebrig\rika-core\phase3.3\scripts
   .\setup.ps1          # Setup project
   .\start-dev.ps1      # Start development
   .\test.ps1           # Verify services
   ```

3. **Access services:**
   - Atlas UI: http://localhost:5173
   - Core API: http://localhost:5317
   - API Docs: http://localhost:5317/docs

**🎉 Phase 3.3 is ready to roll!**