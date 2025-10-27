# 🚀 Rika Core Phase 0 - Complete Setup Guide for Windows

## ✅ Requirement Checklist

### 1. ✅ **Docker Compose File** 
- **Status:** COMPLETE
- **Location:** `docker-compose.yml`
- **Services Included:**
  - ✅ PostgreSQL (Port 5432)
  - ✅ Qdrant (Ports 6333/6334)
  - ✅ NATS (Ports 4222/8222)
  - ✅ LiveKit (Ports 7880/7881)
  - ✅ n8n (Port 5678)
  - ✅ MinIO (Ports 9000/9001)
  - ✅ Keycloak (Port 8080)
  - ✅ Backup service (automated)

### 2. ✅ **Environment Configuration**
- **Status:** COMPLETE
- **Files:**
  - `.env.example` - Template with safe defaults
  - `.env` - Your configured copy (created from template)

### 3. ✅ **Installation Instructions**
- **Status:** COMPLETE
- **Location:** `docs/setup.md`

#### Quick Install Steps:
```bash
# 1. Install Docker Desktop from https://docker.com
# 2. Enable WSL2 in Docker Desktop settings
# 3. Navigate to project:
cd C:\Users\ebrig\rika-core

# 4. Copy environment file:
copy .env.example .env

# 5. Edit passwords in .env:
notepad .env

# 6. Start everything:
docker-compose up -d
```

### 4. ✅ **Service Verification Commands**
- **Status:** COMPLETE

```bash
# PostgreSQL
docker exec -it rika-postgres psql -U rika_admin -d rika_core -c "SELECT version();"

# Qdrant
curl http://localhost:6333/readyz

# NATS
curl http://localhost:8222/varz

# LiveKit
curl http://localhost:7880/

# n8n (browser)
start http://localhost:5678

# MinIO
curl http://localhost:9000/minio/health/live
start http://localhost:9001

# Keycloak
curl http://localhost:8080/health/ready
start http://localhost:8080
```

### 5. ✅ **Backup System**
- **Status:** COMPLETE
- **Scripts:**
  - `backup-windows.ps1` - Windows PowerShell backup
  - `restore-windows.ps1` - Windows PowerShell restore
  - `scripts/backup.sh` - Linux/Docker backup
  - `scripts/restore.sh` - Linux/Docker restore

#### Backup Commands:
```powershell
# Create backup
.\backup-windows.ps1

# List backups
.\restore-windows.ps1 -ListOnly

# Restore from backup
.\restore-windows.ps1
```

### 6. ✅ **Release Versioning**
- **Status:** COMPLETE
- **File:** `release.lock.json`
- **Current Version:** 0.1.0
- **Format:** Semantic versioning with component tracking

### 7. ✅ **Directory Structure**
- **Status:** COMPLETE

```
rika-core/
├── docker-compose.yml          ✅ Main stack configuration
├── .env                        ✅ Your environment variables
├── .env.example               ✅ Template environment
├── .gitignore                 ✅ Git ignore rules
├── release.lock.json          ✅ Version tracking
├── backup-windows.ps1         ✅ Windows backup script
├── restore-windows.ps1        ✅ Windows restore script
├── README.md                  ✅ Quick start guide
├── COMPLETE-SETUP-GUIDE.md    ✅ This file
├── configs/                   ✅ Service configurations
│   ├── keycloak/
│   ├── n8n/
│   ├── livekit/
│   │   └── livekit.yaml
│   └── nats/
├── data/                      ✅ Persistent data volumes
│   ├── postgres/
│   ├── qdrant/
│   ├── minio/
│   ├── keycloak/
│   ├── n8n/
│   └── nats/
├── backups/                   ✅ Local backup storage
│   └── .gitkeep
├── scripts/                   ✅ Automation scripts
│   ├── backup.sh
│   ├── restore.sh
│   └── init/
│       ├── init-postgres.sql
│       └── init-minio.sh
└── docs/                      ✅ Documentation
    └── setup.md
```

### 8. ✅ **Migration Guide**
- **Status:** COMPLETE

#### To Migrate to Another Computer:

1. **On Current Windows PC:**
```powershell
# Create final backup
.\backup-windows.ps1

# Zip entire folder
Compress-Archive -Path C:\Users\ebrig\rika-core -DestinationPath rika-core-migration.zip
```

2. **On New Computer (Proxmox/Unraid/etc):**
```bash
# Extract archive
unzip rika-core-migration.zip

# Navigate to folder
cd rika-core

# Start services
docker-compose up -d

# Restore data if needed
./scripts/restore.sh
```

## 🎯 Current Status Summary

| Component | Status | Verification |
|-----------|--------|--------------|
| Docker Compose | ✅ Complete | All 7 services defined |
| Environment | ✅ Complete | .env created from template |
| PostgreSQL | ✅ Running | Database initialized |
| Qdrant | ✅ Running | Vector DB ready |
| NATS | ✅ Running | Messaging active |
| LiveKit | ✅ Running | WebRTC ready |
| n8n | ✅ Running | Workflows accessible |
| MinIO | ✅ Running | Object storage ready |
| Keycloak | ✅ Running | Auth service ready |
| Backups | ✅ Working | PowerShell scripts tested |
| Documentation | ✅ Complete | All guides present |

## 🔧 Common Operations

### Start Everything
```powershell
docker-compose up -d
```

### Stop Everything
```powershell
docker-compose down
```

### View Logs
```powershell
docker-compose logs -f [service-name]
```

### Restart Service
```powershell
docker-compose restart [service-name]
```

### Update Services
```powershell
docker-compose pull
docker-compose up -d --force-recreate
```

## 📝 What Each Service Does

1. **PostgreSQL** - Stores application state, workflow data, and metadata
2. **Qdrant** - Stores vector embeddings for AI memory and similarity search
3. **NATS** - Handles real-time messaging between services
4. **LiveKit** - Provides WebRTC for video/audio streaming
5. **n8n** - Visual workflow automation and approval gates
6. **MinIO** - S3-compatible storage for files and backups
7. **Keycloak** - Authentication and device enrollment

## 🎉 Phase 0 Complete!

Your Rika Core foundation is:
- ✅ Fully containerized
- ✅ Data persisted in volumes
- ✅ Backup system operational
- ✅ Ready for migration
- ✅ All services accessible locally

**Next Phase:** Deploy Rika agent framework on top of this infrastructure.