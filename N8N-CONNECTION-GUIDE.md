# 🔗 Connect Local n8n to Rika Core Docker Services

## Overview
Since you have n8n running locally, here's how to connect it to your Docker infrastructure services.

## Service Connection Details

### 🗄️ **PostgreSQL Database**
**Use this for storing workflow data, agent states, etc.**

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `rika_core`
- **Username:** `rika_admin`
- **Password:** `RikaPostgres2025SecureDB`
- **SSL Mode:** `disable` (local development)

**n8n Setup:**
1. In n8n, create a new "PostgreSQL" credential
2. Fill in the connection details above
3. Test the connection

**Example Connection String:**
```
postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5432/rika_core
```

### 🔍 **Qdrant Vector Database**
**Use this for AI memory, embeddings, and similarity search**

- **Host:** `http://localhost:6333`
- **API Key:** None (local development)
- **Collection Management:** http://localhost:6333/dashboard

**n8n Setup:**
1. Use "HTTP Request" node
2. Base URL: `http://localhost:6333`
3. Common endpoints:
   - GET `/collections` - List collections
   - POST `/collections/{name}` - Create collection
   - PUT `/collections/{name}/points` - Insert vectors

**Example n8n HTTP Request:**
```json
{
  "method": "GET",
  "url": "http://localhost:6333/collections",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 📨 **NATS Messaging**
**Use this for agent communication and event streaming**

- **Host:** `localhost`
- **Port:** `4222`
- **Username:** `rika_nats`
- **Password:** `NatsMsg2025RikaCore789`
- **Monitor:** http://localhost:8222

**n8n Setup:**
1. Use "NATS" trigger node (if available) or HTTP Request
2. Connection: `nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222`

### 🗃️ **MinIO Object Storage (S3-Compatible)**
**Use this for file storage, backups, model storage**

- **Endpoint:** `http://localhost:9000`
- **Access Key:** `rika_minio_admin`
- **Secret Key:** `MinioStorage2025RikaS3Obj`
- **Region:** `us-east-1` (default)
- **Console:** http://localhost:9001

**n8n Setup:**
1. Create "AWS S3" credential
2. Use custom endpoint: `http://localhost:9000`
3. Access Key: `rika_minio_admin`
4. Secret: `MinioStorage2025RikaS3Obj`
5. Region: `us-east-1`
6. Force path style: `true`

**Available Buckets:**
- `rika-backups` - System backups
- `rika-models` - AI models and weights
- `rika-media` - User media files
- `rika-artifacts` - Build artifacts
- `rika-temp` - Temporary files (auto-expire 7 days)

## 🔧 **Common n8n Workflows with Docker Services**

### **Workflow 1: Database Query → Vector Search**
```
1. PostgreSQL Node (Query agent states)
   ↓
2. HTTP Request (Search similar vectors in Qdrant)
   ↓
3. Set Node (Combine results)
```

### **Workflow 2: File Processing Pipeline**
```
1. Trigger (Webhook or Schedule)
   ↓
2. AWS S3 Node (Download file from MinIO)
   ↓
3. Function Node (Process file)
   ↓
4. AWS S3 Node (Upload result to MinIO)
   ↓
5. HTTP Request (Update metadata in PostgreSQL)
```

### **Workflow 3: Agent Communication**
```
1. NATS Trigger (Listen for agent messages)
   ↓
2. PostgreSQL Node (Update agent state)
   ↓
3. HTTP Request (Store embeddings in Qdrant)
   ↓
4. NATS Node (Send response message)
```

## 📊 **Service Health Checks in n8n**

Create a monitoring workflow:

### **Health Check Workflow**
```javascript
// PostgreSQL Health Check
const pgCheck = {
  "method": "POST",
  "url": "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5432/rika_core",
  "query": "SELECT 1 as health"
};

// Qdrant Health Check
const qdrantCheck = {
  "method": "GET", 
  "url": "http://localhost:6333/readyz"
};

// NATS Health Check
const natsCheck = {
  "method": "GET",
  "url": "http://localhost:8222/varz"
};

// MinIO Health Check
const minioCheck = {
  "method": "GET",
  "url": "http://localhost:9000/minio/health/live"
};
```

## 🚀 **Getting Started Steps**

### **1. Test Basic Connectivity**
1. Create a simple n8n workflow
2. Add HTTP Request node
3. Test each service health endpoint:
   - Qdrant: `GET http://localhost:6333/readyz`
   - NATS: `GET http://localhost:8222/varz`
   - MinIO: `GET http://localhost:9000/minio/health/live`

### **2. Set Up Credentials**
1. Go to n8n Settings → Credentials
2. Create credentials for each service:
   - PostgreSQL
   - AWS S3 (for MinIO)
   - HTTP credentials (for Qdrant/NATS if needed)

### **3. Create Your First Integration**
Start with a simple workflow:
```
Trigger → PostgreSQL (SELECT * FROM agent_states LIMIT 5) → Table Display
```

## 🛠️ **Troubleshooting**

### **Connection Issues:**
- Ensure Docker services are running: `docker-compose ps`
- Check service logs: `docker-compose logs [service-name]`
- Verify ports aren't blocked by Windows Firewall

### **Authentication Issues:**
- Double-check credentials from the updated `.env` file
- For PostgreSQL, ensure the database `rika_core` exists
- For MinIO, use the console at http://localhost:9001 to verify access

### **Network Issues:**
- All services are on `localhost` from your Windows perspective
- If using WSL2, ensure Docker Desktop has WSL2 integration enabled
- Services are on the `rika-net` network within Docker

## 📋 **Updated Credentials Summary**

| Service | Username | Password | Connection |
|---------|----------|----------|------------|
| **PostgreSQL** | `rika_admin` | `RikaPostgres2025SecureDB` | `localhost:5432` |
| **NATS** | `rika_nats` | `NatsMsg2025RikaCore789` | `localhost:4222` |
| **MinIO** | `rika_minio_admin` | `MinioStorage2025RikaS3Obj` | `localhost:9000` |
| **Qdrant** | - | - | `http://localhost:6333` |

Your local n8n can now act as the orchestration layer for your Docker-based Rika Core infrastructure! 🎉