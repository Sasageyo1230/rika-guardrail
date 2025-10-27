# Rika Core Phase 0 - Setup Guide

## Prerequisites

### Windows Requirements
- Windows 10/11 Pro or Enterprise (for Docker Desktop)
- WSL2 enabled (for Linux containers)
- Docker Desktop installed and running
- At least 16GB RAM (32GB recommended)
- 50GB free disk space
- PowerShell or Windows Terminal

### Software Installation

1. **Install WSL2** (if not already installed):
```powershell
# Run as Administrator
wsl --install
wsl --set-default-version 2
```

2. **Install Docker Desktop**:
   - Download from: https://www.docker.com/products/docker-desktop/
   - Enable WSL2 backend during installation
   - Start Docker Desktop and ensure it's running

3. **Install Docker Compose** (usually included with Docker Desktop):
```bash
docker --version
docker-compose --version
```

## Step-by-Step Setup Instructions

### 1. Clone or Create Project Directory

```powershell
# Navigate to your desired location
cd C:\Users\%USERNAME%

# If you've downloaded the files:
cd rika-core

# Or create fresh:
mkdir rika-core
cd rika-core
```

### 2. Configure Environment Variables

```powershell
# Copy the example environment file
copy .env.example .env

# Edit .env with your preferred editor
notepad .env
# OR
code .env  # If you have VS Code
```

**IMPORTANT: Change ALL passwords in .env file!**

Key variables to update:
- `POSTGRES_PASSWORD`
- `NATS_PASSWORD`
- `LIVEKIT_API_SECRET`
- `N8N_BASIC_AUTH_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`

### 3. Set Permissions for Scripts (WSL/Git Bash)

```bash
# If using WSL or Git Bash
chmod +x scripts/*.sh
chmod +x scripts/init/*.sh
```

### 4. Pull Docker Images (Offline Preparation)

```powershell
# Pull all images while connected to internet
docker-compose pull

# This downloads all services defined in docker-compose.yml
# Total download size: ~3-4GB
```

### 5. Start the Stack

```powershell
# Start all services in detached mode
docker-compose up -d

# Or start with logs visible
docker-compose up

# To start specific services only
docker-compose up -d postgres qdrant nats
```

### 6. Verify Services are Running

```powershell
# Check all containers are running
docker-compose ps

# Check logs for any service
docker-compose logs postgres
docker-compose logs keycloak
```

## Service Access URLs

Once running, access services at:

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **PostgreSQL** | `localhost:5432` | User: `rika_admin` / Pass: (from .env) |
| **Qdrant** | `http://localhost:6333` | No auth (dashboard) |
| **NATS Monitor** | `http://localhost:8222` | User: `rika_nats` / Pass: (from .env) |
| **LiveKit** | `http://localhost:7880` | API Key/Secret from .env |
| **n8n** | `http://localhost:5678` | User: `rika_n8n` / Pass: (from .env) |
| **MinIO Console** | `http://localhost:9001` | User: `rika_minio_admin` / Pass: (from .env) |
| **Keycloak** | `http://localhost:8080` | User: `rika_keycloak` / Pass: (from .env) |

## Test Plan - Verify Each Service

### Test 1: PostgreSQL Database
```powershell
# Test connection
docker exec -it rika-postgres psql -U rika_admin -d rika_core -c "SELECT version();"

# Check tables were created
docker exec -it rika-postgres psql -U rika_admin -d rika_core -c "\dt rika_core.*"
```
✅ Expected: PostgreSQL version displayed and tables listed

### Test 2: Qdrant Vector Database
```powershell
# Check health
curl http://localhost:6333/readyz

# Check collections
curl http://localhost:6333/collections
```
✅ Expected: `{"status":"ok"}` and empty collections list

### Test 3: NATS Messaging
```powershell
# Check monitoring page
curl http://localhost:8222/varz
```
✅ Expected: JSON with NATS server information

### Test 4: LiveKit WebRTC
```powershell
# Check health
curl http://localhost:7880/
```
✅ Expected: LiveKit server response

### Test 5: n8n Workflows
```powershell
# Open browser to http://localhost:5678
# Login with credentials from .env
```
✅ Expected: n8n login page appears, can login

### Test 6: MinIO Object Storage
```powershell
# Check health
curl http://localhost:9000/minio/health/live

# Access console at http://localhost:9001
```
✅ Expected: Health check passes, console accessible

### Test 7: Keycloak Authentication
```powershell
# Check health
curl http://localhost:8080/health/ready

# Access admin console at http://localhost:8080
```
✅ Expected: `{"status":"UP"}` and admin console loads

### Test 8: Backup System
```powershell
# Test backup script (from WSL or Git Bash)
docker exec -it rika-backup /scripts/backup.sh

# Or trigger manually
docker-compose run --rm backup /scripts/backup.sh
```
✅ Expected: Backup completes, files created in `./backups/`

## Common Operations

### Stop All Services
```powershell
docker-compose down
```

### Stop and Remove All Data (CAUTION!)
```powershell
docker-compose down -v
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 keycloak
```

### Restart a Service
```powershell
docker-compose restart n8n
```

### Update Services
```powershell
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate
```

### Manual Backup
```powershell
# Run backup script
docker-compose exec backup /scripts/backup.sh

# Or from host (requires WSL/bash)
./scripts/backup.sh
```

### Restore from Backup
```powershell
# Interactive restore
./scripts/restore.sh

# List available backups
./scripts/restore.sh --list
```

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"
**Solution:**
```powershell
# Ensure Docker Desktop is running
# Check Docker service
docker version

# Restart Docker Desktop from system tray
```

### Issue: "Port already in use"
**Solution:**
```powershell
# Find process using port (e.g., 5432)
netstat -ano | findstr :5432

# Change port in .env file
# Then recreate containers
docker-compose down
docker-compose up -d
```

### Issue: "Insufficient memory"
**Solution:**
1. Open Docker Desktop settings
2. Go to Resources > Advanced
3. Increase Memory limit to at least 8GB
4. Apply & Restart

### Issue: "Container keeps restarting"
**Solution:**
```powershell
# Check logs
docker-compose logs [service-name]

# Check resource usage
docker stats

# Increase health check timeouts in docker-compose.yml
```

### Issue: "Permission denied on scripts"
**Solution:**
```bash
# From WSL or Git Bash
chmod +x scripts/*.sh
dos2unix scripts/*.sh  # If line ending issues
```

## Migration to Production VM/NAS

When ready to migrate to Proxmox/Unraid:

1. **Backup current state:**
```bash
./scripts/backup.sh
```

2. **Copy entire rika-core directory to new host:**
```bash
# Via SCP
scp -r rika-core/ user@proxmox-host:/path/to/destination/

# Or create tar archive
tar -czf rika-core-backup.tar.gz rika-core/
```

3. **On new host:**
```bash
# Extract if using tar
tar -xzf rika-core-backup.tar.gz

# Navigate to directory
cd rika-core

# Update .env with new host-specific settings
nano .env

# Start services
docker-compose up -d
```

4. **Restore data:**
```bash
./scripts/restore.sh
```

## Security Checklist

- [ ] Changed all default passwords in .env
- [ ] .env file is NOT committed to git
- [ ] Firewall configured (Windows Defender/other)
- [ ] Services bound to localhost only (not 0.0.0.0)
- [ ] Backup encryption enabled (for production)
- [ ] SSL certificates configured (for production)
- [ ] Keycloak realm properly configured
- [ ] MinIO access keys rotated
- [ ] Database connections use SSL (for production)

## Maintenance Schedule

**Daily:**
- Automated backups run at 2 AM (configurable)

**Weekly:**
- Check disk usage: `docker system df`
- Review logs for errors
- Verify backup integrity

**Monthly:**
- Update Docker images
- Clean old backups
- Review and rotate credentials
- Check for security updates

## Next Steps

After Phase 0 is running:

1. **Configure Keycloak:**
   - Create Rika realm
   - Set up client applications
   - Configure device enrollment

2. **Set up n8n Workflows:**
   - Import base workflows
   - Configure webhook endpoints
   - Set up approval gates

3. **Initialize Qdrant Collections:**
   - Create memory collection
   - Set up vector indices
   - Configure similarity metrics

4. **Configure NATS Streams:**
   - Create JetStream configurations
   - Set up subjects and consumers
   - Configure retention policies

5. **Prepare for Rika Core:**
   - Deploy agent framework
   - Configure state management
   - Set up monitoring

## Support & Documentation

- Docker Compose: https://docs.docker.com/compose/
- PostgreSQL: https://www.postgresql.org/docs/
- Qdrant: https://qdrant.tech/documentation/
- NATS: https://docs.nats.io/
- LiveKit: https://docs.livekit.io/
- n8n: https://docs.n8n.io/
- MinIO: https://docs.min.io/
- Keycloak: https://www.keycloak.org/documentation

---

**Version:** 0.1.0  
**Last Updated:** 2025-01-08  
**Phase:** 0 - Foundation