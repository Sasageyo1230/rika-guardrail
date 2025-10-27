# Rika Overseer - Policy Gatekeeper

## Overview

The Overseer is an independent policy enforcement service that acts as a gatekeeper for sensitive operations. It provides:

- **Policy-based decision making** for capabilities
- **Tamper-evident audit logs** with hash chains
- **n8n integration** for approval workflows
- **Independent operation** from Core API

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core API      │    │    Overseer     │    │      n8n        │
│                 │───►│  (Port 5319)    │───►│   Workflows     │
│   Capability    │    │                 │    │                 │
│   Request       │    │ Policy Engine   │    │ Human Approval  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │    PostgreSQL       │
                    │   Audit Logs        │
                    │  (Hash Chained)     │
                    └─────────────────────┘
```

## Sequence Diagram

```
Core API          Overseer         n8n            Admin
   │                 │              │               │
   │─── POST /check ─┤              │               │
   │                 │              │               │
   │                 ├─ evaluate ───┤               │
   │                 ├─ audit log ──┤               │
   │                 │              │               │
   │                 │─── webhook ──┤               │
   │                 │              │── notify ────┤
   │                 │              │               │
   │◄── response ────┤              │               │
   │                 │              │               │
   │                 │              │◄── approve ──┤
   │                 │◄── callback ─┤               │
   │                 │              │               │
   │─── GET status ──┤              │               │
   │◄── approved ────┤              │               │
```

## Quick Start

### 1. Install Dependencies
```powershell
cd C:\Users\ebrig\rika-core\phase3\overseer
pip install -r requirements.txt
```

### 2. Configure Environment
```powershell
# Copy and edit configuration
cp .env.example .env
# Edit .env with your database URL and n8n webhook
```

### 3. Start Service
```powershell
.\start-overseer.ps1
```

### 4. Test Policy Check
```powershell
# Test capability check
Invoke-RestMethod -Uri "http://localhost:5319/check" -Method POST -Body (@{
    capability = "remote_control"
    requester = "test-user"
    context = @{
        device_id = "test-device"
        ttl_minutes = 15
    }
} | ConvertTo-Json) -ContentType "application/json"
```

## API Endpoints

### POST /check
Check if a capability is allowed by policy.

**Request:**
```json
{
  "capability": "remote_control",
  "requester": "user@company.com",
  "context": {
    "device_id": "laptop-001",
    "ttl_minutes": 15,
    "active_sessions": 1
  }
}
```

**Response:**
```json
{
  "decision": "review",
  "reason": "Default policy for remote_control: review",
  "request_id": "overseer_abc123",
  "expires_at": "2024-01-15T15:05:00Z"
}
```

### POST /approve
Approve or deny a pending request.

**Request:**
```json
{
  "request_id": "overseer_abc123",
  "approved": true,
  "approver": "admin@company.com",
  "notes": "Emergency maintenance approved"
}
```

### GET /audit/{audit_id}
Get specific audit entry by hash.

### GET /health
Service health check.

### GET /policy
Get current policy configuration.

### GET /audit/chain/verify
Verify audit chain integrity.

## Policy Configuration

The policy is stored in `policy.json`:

```json
{
  "version": "1.0.0",
  "capabilities": {
    "remote_control": {
      "default": "review",
      "conditions": {
        "business_hours_only": true,
        "max_sessions": 3,
        "max_duration_minutes": 30
      },
      "allowlist": ["admin@company.com"],
      "denylist": []
    },
    "model_change": {
      "default": "review",
      "conditions": {
        "require_eval": true,
        "require_approval": true
      }
    },
    "data_access": {
      "default": "allow",
      "conditions": {
        "audit_required": true
      }
    }
  }
}
```

### Policy Decisions

- **allow**: Capability granted immediately
- **deny**: Capability rejected immediately  
- **review**: Requires human approval via n8n

### Conditions

- `business_hours_only`: Only allow during weekdays 9-5 UTC
- `max_sessions`: Maximum concurrent sessions
- `max_duration_minutes`: Maximum session duration
- `require_eval`: Requires evaluation to pass
- `admin_only`: Only for admin users

## Audit System

### Tamper-Evident Logging

Each audit entry contains:
- Event details (capability, requester, decision)
- Previous entry hash (chain integrity)
- Current entry hash (tamper detection)
- Timestamp and context

### Hash Chain Verification

```powershell
# Verify audit chain integrity
Invoke-RestMethod -Uri "http://localhost:5319/audit/chain/verify"
```

### Daily Snapshots

The Overseer automatically creates daily snapshots of the audit chain and stores them in MinIO for long-term retention.

## Integration with Core API

The Core API should call Overseer before sensitive operations:

```python
# In Core API
async def check_permission(capability: str, context: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:5319/check", json={
            "capability": capability,
            "requester": "current_user",
            "context": context
        })
        return response.json()

# Before granting control
decision = await check_permission("remote_control", {
    "device_id": device_id,
    "ttl_minutes": ttl_minutes
})

if decision["decision"] == "deny":
    raise HTTPException(403, decision["reason"])
elif decision["decision"] == "review":
    # Store request_id, wait for approval
    return {"status": "pending", "request_id": decision["request_id"]}
```

## Monitoring

### Health Metrics
- Policy version
- Audit chain length  
- Recent decisions (allow/deny/review)
- Chain verification status

### Alerts
- Policy file changes
- Chain integrity violations
- High denial rates
- Failed approval notifications

## Security

### Threat Model
- **Policy tampering**: Prevented by file monitoring
- **Audit tampering**: Detected by hash chain verification
- **Bypass attempts**: All capabilities must go through Overseer
- **Approval bypass**: n8n workflow validates request IDs

### Best Practices
- Run Overseer on dedicated port (5319)
- Regular audit chain verification
- Monitor policy file changes
- Backup audit snapshots to external storage
- Use TLS in production

## Troubleshooting

### Common Issues

**Policy not loading**
- Check `policy.json` syntax
- Verify file permissions
- Check logs for JSON errors

**Audit chain invalid**
- Run chain verification
- Check for database corruption
- Review recent audit entries

**n8n workflow not triggering**
- Verify webhook URL in `.env`
- Check n8n service status
- Test webhook manually

**Database connection failed**  
- Verify DATABASE_URL
- Check PostgreSQL service
- Confirm credentials