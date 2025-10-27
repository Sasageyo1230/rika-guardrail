# phase3/overseer/overseer.py
"""
Rika Overseer - Independent Policy Gatekeeper
Provides tamper-evident audit logs and approval workflows
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
import asyncio
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core')
MINIO_URL = os.getenv('MINIO_URL', 'http://localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'rika_minio_admin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'MinioStorage2025RikaS3Obj')
N8N_WEBHOOK_URL = os.getenv('N8N_OVERSEER_WEBHOOK', 'http://localhost:5678/webhook/overseer-approval')

# FastAPI setup
app = FastAPI(
    title="Rika Overseer",
    version="3.0.0",
    description="Independent policy gatekeeper with tamper-evident audit"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db_pool = None
policy_data = None
audit_chain = []

# ============= Models =============

class CapabilityCheck(BaseModel):
    capability: str = Field(..., description="Capability being requested")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context data")
    requester: str = Field(..., description="Who is requesting")
    device_id: Optional[str] = None
    session_id: Optional[str] = None

class PolicyDecision(BaseModel):
    decision: Literal["allow", "deny", "review"] = Field(..., description="Policy decision")
    reason: str = Field(..., description="Reason for decision")
    request_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    conditions: List[str] = Field(default_factory=list)

class ApprovalRequest(BaseModel):
    request_id: str
    approved: bool
    approver: str
    notes: Optional[str] = None

class AuditEntry(BaseModel):
    event_type: str
    requester: str
    capability: str
    decision: str
    reason: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prev_hash: Optional[str] = None
    record_hash: Optional[str] = None

# ============= Policy Engine =============

def load_policy() -> Dict[str, Any]:
    """Load policy from JSON file"""
    global policy_data
    
    policy_file = Path("policy.json")
    if not policy_file.exists():
        # Create default policy
        default_policy = {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "capabilities": {
                "remote_control": {
                    "default": "review",
                    "conditions": {
                        "business_hours_only": True,
                        "max_sessions": 3,
                        "max_duration_minutes": 30
                    },
                    "allowlist": [],
                    "denylist": []
                },
                "model_change": {
                    "default": "review",
                    "conditions": {
                        "require_eval": True,
                        "require_approval": True
                    }
                },
                "data_access": {
                    "default": "allow",
                    "conditions": {
                        "audit_required": True
                    }
                },
                "system_config": {
                    "default": "deny",
                    "conditions": {
                        "admin_only": True
                    }
                }
            },
            "offline_mode": {
                "enable_emergency_override": True,
                "max_offline_hours": 24
            },
            "audit": {
                "retention_days": 90,
                "snapshot_frequency": "daily",
                "tamper_detection": True
            }
        }
        
        with open(policy_file, 'w') as f:
            json.dump(default_policy, f, indent=2, default=str)
        
        policy_data = default_policy
    else:
        with open(policy_file, 'r') as f:
            policy_data = json.load(f)
    
    return policy_data

def evaluate_capability(capability: str, context: Dict[str, Any], requester: str) -> PolicyDecision:
    """Evaluate capability request against policy"""
    policy = load_policy()
    
    # Get capability config
    cap_config = policy.get("capabilities", {}).get(capability, {"default": "deny"})
    default_decision = cap_config.get("default", "deny")
    conditions = cap_config.get("conditions", {})
    allowlist = cap_config.get("allowlist", [])
    denylist = cap_config.get("denylist", [])
    
    # Check denylist first
    if requester in denylist:
        return PolicyDecision(
            decision="deny",
            reason=f"Requester {requester} is in denylist for {capability}"
        )
    
    # Check allowlist
    if requester in allowlist:
        return PolicyDecision(
            decision="allow",
            reason=f"Requester {requester} is in allowlist for {capability}"
        )
    
    # Apply conditions
    decision_reasons = []
    
    # Business hours check
    if conditions.get("business_hours_only", False):
        now = datetime.utcnow()
        if now.weekday() >= 5 or now.hour < 9 or now.hour > 17:  # Weekend or outside 9-5
            if default_decision == "allow":
                default_decision = "review"
                decision_reasons.append("Outside business hours")
    
    # Session limits
    if capability == "remote_control":
        max_sessions = conditions.get("max_sessions", 999)
        active_sessions = context.get("active_sessions", 0)
        if active_sessions >= max_sessions:
            return PolicyDecision(
                decision="deny",
                reason=f"Maximum concurrent sessions ({max_sessions}) exceeded"
            )
    
    # Duration limits  
    if capability == "remote_control":
        max_duration = conditions.get("max_duration_minutes", 60)
        requested_duration = context.get("ttl_minutes", 15)
        if requested_duration > max_duration:
            return PolicyDecision(
                decision="deny",
                reason=f"Requested duration ({requested_duration}min) exceeds maximum ({max_duration}min)"
            )
    
    # Model change requirements
    if capability == "model_change":
        if conditions.get("require_eval", False) and not context.get("eval_passed", False):
            return PolicyDecision(
                decision="deny",
                reason="Model change requires evaluation to pass"
            )
    
    # Default decision
    reason = f"Default policy for {capability}: {default_decision}"
    if decision_reasons:
        reason += f" ({'; '.join(decision_reasons)})"
    
    return PolicyDecision(
        decision=default_decision,
        reason=reason
    )

# ============= Audit System =============

def calculate_hash(data: str) -> str:
    """Calculate SHA-256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()

async def create_audit_entry(
    event_type: str,
    requester: str, 
    capability: str,
    decision: str,
    reason: str,
    context: Dict[str, Any] = None
) -> str:
    """Create tamper-evident audit entry"""
    
    entry = AuditEntry(
        event_type=event_type,
        requester=requester,
        capability=capability,
        decision=decision,
        reason=reason,
        context=context or {}
    )
    
    # Get previous hash
    prev_hash = None
    if audit_chain:
        prev_hash = audit_chain[-1].record_hash
    entry.prev_hash = prev_hash
    
    # Calculate this entry's hash
    entry_data = f"{entry.event_type}|{entry.requester}|{entry.capability}|{entry.decision}|{entry.reason}|{entry.timestamp.isoformat()}|{prev_hash}"
    entry.record_hash = calculate_hash(entry_data)
    
    # Add to chain
    audit_chain.append(entry)
    
    # Store in database
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO overseer_audit (
                    event_type, requester, capability, decision, reason,
                    context, timestamp, prev_hash, record_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                entry.event_type, entry.requester, entry.capability,
                entry.decision, entry.reason, json.dumps(entry.context),
                entry.timestamp, entry.prev_hash, entry.record_hash
            )
    except Exception as e:
        logging.error(f"Failed to store audit entry: {e}")
    
    return entry.record_hash

# ============= API Endpoints =============

@app.post("/check", response_model=PolicyDecision)
async def check_capability(request: CapabilityCheck, background_tasks: BackgroundTasks):
    """Check if capability is allowed by policy"""
    
    decision = evaluate_capability(request.capability, request.context, request.requester)
    
    # Create audit entry
    background_tasks.add_task(
        create_audit_entry,
        "capability_check",
        request.requester,
        request.capability,
        decision.decision,
        decision.reason,
        request.context
    )
    
    # If decision is "review", trigger approval workflow
    if decision.decision == "review":
        request_id = f"overseer_{uuid.uuid4().hex[:12]}"
        decision.request_id = request_id
        decision.expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Store pending request
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO overseer_requests (
                        request_id, capability, requester, context, 
                        status, expires_at
                    ) VALUES ($1, $2, $3, $4, 'pending', $5)
                """, request_id, request.capability, request.requester,
                     json.dumps(request.context), decision.expires_at)
        except Exception as e:
            logging.error(f"Failed to store request: {e}")
        
        # Trigger n8n workflow
        background_tasks.add_task(trigger_approval_workflow, request_id, request)
    
    return decision

@app.post("/approve")
async def approve_request(request: ApprovalRequest, background_tasks: BackgroundTasks):
    """Approve or deny a pending request"""
    
    try:
        async with db_pool.acquire() as conn:
            # Get request details
            req_data = await conn.fetchrow("""
                SELECT * FROM overseer_requests 
                WHERE request_id = $1 AND status = 'pending'
            """, request.request_id)
            
            if not req_data:
                raise HTTPException(status_code=404, detail="Request not found or already processed")
            
            # Check if expired
            if req_data['expires_at'] < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Request has expired")
            
            # Update status
            new_status = "approved" if request.approved else "denied"
            await conn.execute("""
                UPDATE overseer_requests 
                SET status = $1, approved_by = $2, approved_at = NOW(), notes = $3
                WHERE request_id = $4
            """, new_status, request.approver, request.notes, request.request_id)
            
            # Create audit entry
            background_tasks.add_task(
                create_audit_entry,
                "request_approved" if request.approved else "request_denied",
                request.approver,
                req_data['capability'],
                new_status,
                f"Manual approval by {request.approver}" + (f": {request.notes}" if request.notes else ""),
                json.loads(req_data['context'])
            )
            
            return {
                "status": "success",
                "request_id": request.request_id,
                "decision": new_status
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit/{audit_id}")
async def get_audit_entry(audit_id: str):
    """Get specific audit entry"""
    
    try:
        async with db_pool.acquire() as conn:
            entry = await conn.fetchrow("""
                SELECT * FROM overseer_audit WHERE record_hash = $1
            """, audit_id)
            
            if not entry:
                raise HTTPException(status_code=404, detail="Audit entry not found")
            
            return dict(entry)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    policy = load_policy()
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "policy_version": policy.get("version", "unknown"),
        "audit_entries": len(audit_chain),
        "timestamp": datetime.utcnow()
    }

@app.get("/policy")
async def get_policy():
    """Get current policy configuration"""
    return load_policy()

@app.get("/audit/chain/verify")
async def verify_audit_chain():
    """Verify audit chain integrity"""
    
    try:
        async with db_pool.acquire() as conn:
            entries = await conn.fetch("""
                SELECT * FROM overseer_audit 
                ORDER BY timestamp ASC
            """)
            
            chain_valid = True
            last_hash = None
            invalid_entries = []
            
            for entry in entries:
                # Verify hash chain
                if last_hash != entry['prev_hash']:
                    chain_valid = False
                    invalid_entries.append(entry['record_hash'])
                
                # Verify entry hash
                entry_data = f"{entry['event_type']}|{entry['requester']}|{entry['capability']}|{entry['decision']}|{entry['reason']}|{entry['timestamp'].isoformat()}|{entry['prev_hash']}"
                expected_hash = calculate_hash(entry_data)
                
                if expected_hash != entry['record_hash']:
                    chain_valid = False
                    invalid_entries.append(entry['record_hash'])
                
                last_hash = entry['record_hash']
            
            return {
                "chain_valid": chain_valid,
                "total_entries": len(entries),
                "invalid_entries": invalid_entries,
                "last_hash": last_hash,
                "verified_at": datetime.utcnow()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= Background Tasks =============

async def trigger_approval_workflow(request_id: str, request: CapabilityCheck):
    """Trigger n8n approval workflow"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(N8N_WEBHOOK_URL, json={
                "request_id": request_id,
                "capability": request.capability,
                "requester": request.requester,
                "context": request.context,
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }, timeout=10)
    except Exception as e:
        logging.error(f"Failed to trigger approval workflow: {e}")

async def daily_snapshot():
    """Create daily snapshot of audit chain"""
    while True:
        try:
            # Wait for next midnight
            now = datetime.utcnow()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            wait_seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Create snapshot
            async with db_pool.acquire() as conn:
                entries = await conn.fetch("""
                    SELECT * FROM overseer_audit 
                    WHERE timestamp >= $1 AND timestamp < $2
                    ORDER BY timestamp ASC
                """, now.replace(hour=0, minute=0, second=0, microsecond=0), tomorrow)
                
                snapshot = {
                    "date": now.date().isoformat(),
                    "entries_count": len(entries),
                    "entries": [dict(entry) for entry in entries],
                    "chain_verification": await verify_audit_chain(),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # TODO: Upload to MinIO
                # This would normally upload the snapshot to MinIO for tamper-evident storage
                
                logging.info(f"Daily audit snapshot created: {len(entries)} entries")
                
        except Exception as e:
            logging.error(f"Error creating daily snapshot: {e}")
            await asyncio.sleep(3600)  # Retry in 1 hour

# ============= Startup/Shutdown =============

@app.on_event("startup")
async def startup():
    global db_pool
    
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        # Create tables
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS overseer_requests (
                    id SERIAL PRIMARY KEY,
                    request_id VARCHAR(50) UNIQUE NOT NULL,
                    capability VARCHAR(100) NOT NULL,
                    requester VARCHAR(100) NOT NULL,
                    context JSONB,
                    status VARCHAR(20) DEFAULT 'pending',
                    expires_at TIMESTAMP,
                    approved_by VARCHAR(100),
                    approved_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS overseer_audit (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    requester VARCHAR(100),
                    capability VARCHAR(100),
                    decision VARCHAR(20),
                    reason TEXT,
                    context JSONB,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    prev_hash VARCHAR(64),
                    record_hash VARCHAR(64) UNIQUE NOT NULL
                )
            """)
        
        # Load existing audit chain
        async with db_pool.acquire() as conn:
            entries = await conn.fetch("""
                SELECT * FROM overseer_audit 
                ORDER BY timestamp ASC
            """)
            
            for entry in entries:
                audit_entry = AuditEntry(
                    event_type=entry['event_type'],
                    requester=entry['requester'],
                    capability=entry['capability'],
                    decision=entry['decision'],
                    reason=entry['reason'],
                    context=json.loads(entry['context']) if entry['context'] else {},
                    timestamp=entry['timestamp'],
                    prev_hash=entry['prev_hash'],
                    record_hash=entry['record_hash']
                )
                audit_chain.append(audit_entry)
        
        # Start background tasks
        asyncio.create_task(daily_snapshot())
        
        logging.info(f"Rika Overseer started - loaded {len(audit_chain)} audit entries")
        
    except Exception as e:
        logging.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5319, reload=True)