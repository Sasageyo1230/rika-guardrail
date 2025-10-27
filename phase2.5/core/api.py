# core/api.py
"""
Rika Core API Service - Phase 2.5
Enhanced with LiveKit streaming and secure remote control
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
import asyncpg
import asyncio
import nats
import json
import uuid
import secrets
import os
from dotenv import load_dotenv
import logging
from livekit import api
import requests
import hashlib

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Rika Core API", version="2.5.0", description="Enhanced with streaming and remote control")

# CORS middleware - configured for UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core")
NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")
TOKEN_EXPIRY_MINUTES = int(os.getenv("TOKEN_EXPIRY_MINUTES", "5"))

# Phase 2.5: LiveKit Configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_WS_URL = os.getenv("LIVEKIT_WS_URL", "ws://localhost:7880")

# Phase 2.5: Control Configuration
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/rika-control-approval")
POLICY_FILE = os.getenv("POLICY_FILE", "./policy.json")

# Global connections
db_pool = None
nc = None

# ==================== Models ====================

# Phase 1 & 2 Models (existing)
class EnrollRequest(BaseModel):
    device_name: str = Field(..., description="Friendly name for the device")
    device_type: str = Field(..., description="Type: desktop, mobile, tablet, etc")

class EnrollResponse(BaseModel):
    token: str
    expires_at: datetime
    enrollment_url: str

class CompleteEnrollRequest(BaseModel):
    token: str
    fingerprint: str = Field(..., description="Unique device fingerprint")

class CompleteEnrollResponse(BaseModel):
    device_id: str
    credentials: Dict[str, str]
    nats_subjects: List[str]

class DeviceHeartbeat(BaseModel):
    device_id: str
    current_app: str
    window_title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class DevicePresence(BaseModel):
    device_id: str
    name: str
    type: str
    last_seen: datetime
    last_active_app: Optional[str]
    status: str
    linked: bool = False
    link_mode: Optional[str] = None
    link_expires_at: Optional[datetime] = None
    gestures_enabled: bool = False
    # Phase 2.5: Control status
    control_status: Optional[str] = None  # pending, active, revoked
    control_expires_at: Optional[datetime] = None

class BlackoutRequest(BaseModel):
    device_id: str
    reason: Optional[str] = "Manual blackout triggered"

class LinkRequest(BaseModel):
    device_id: str
    mode: Literal["view", "extend", "control"] = Field(..., description="Link mode")
    ttl_minutes: Optional[int] = Field(default=30, ge=10, le=60, description="Time to live in minutes")
    gestures: bool = Field(default=False, description="Enable gesture controls")

class UnlinkRequest(BaseModel):
    device_id: Optional[str] = Field(default=None, description="Device ID to unlink, or None for all")

class DeviceLink(BaseModel):
    device_id: str
    device_name: str
    mode: str
    gestures_enabled: bool
    expires_at: datetime
    updated_at: datetime

class HandsOnRequest(BaseModel):
    device_id: str
    enabled: bool = Field(..., description="Enable or disable hands-on mode")

# ==================== Phase 2.5: New Models ====================

class ControlRequest(BaseModel):
    device_id: str
    ttl_minutes: int = Field(default=15, ge=5, le=30, description="Control session TTL in minutes")
    reason: Optional[str] = Field(default="Remote assistance", description="Reason for control request")

class ControlResponse(BaseModel):
    request_id: str
    status: str
    expires_at: datetime
    approval_url: str

class ControlApproval(BaseModel):
    request_id: str
    approved: bool = Field(..., description="Whether to approve or deny")
    approver: Optional[str] = Field(default="system", description="Who approved this request")

class ControlRevoke(BaseModel):
    device_id: str
    reason: Optional[str] = Field(default="Manual revoke", description="Reason for revocation")

class StreamInfo(BaseModel):
    device_id: str
    device_name: str
    room_name: str
    participant_token: str
    viewer_token: str
    ws_url: str
    expires_at: datetime

class ControlInputEvent(BaseModel):
    device_id: str
    event_type: Literal["mouse_move", "mouse_click", "mouse_scroll", "key_press", "key_release"]
    payload: Dict[str, Any]

# ==================== Database ====================

async def init_db():
    """Initialize database connection pool and create tables"""
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    
    # Create tables if they don't exist (Phase 1 & 2 tables)
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                fingerprint VARCHAR(255) UNIQUE NOT NULL,
                last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_active_app VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS enrollment_tokens (
                token VARCHAR(255) PRIMARY KEY,
                device_name VARCHAR(255) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                payload JSONB DEFAULT '{}',
                device_id UUID REFERENCES devices(id) ON DELETE SET NULL
            )
        ''')
        
        # Phase 2: Device links table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS device_links (
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                mode VARCHAR(20) NOT NULL CHECK (mode IN ('view', 'extend', 'control')),
                gestures_enabled BOOLEAN DEFAULT false,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS hands_on_sessions (
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                enabled BOOLEAN DEFAULT false,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id)
            )
        ''')
        
        # Phase 2.5: Control requests and sessions
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS control_requests (
                request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                requester VARCHAR(255) DEFAULT 'atlas-ui',
                reason TEXT,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied', 'expired')),
                ttl_minutes INTEGER NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP WITH TIME ZONE,
                approver VARCHAR(255),
                revoked_at TIMESTAMP WITH TIME ZONE
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS control_sessions (
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                request_id UUID REFERENCES control_requests(request_id),
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked')),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id)
            )
        ''')
        
        # Phase 2.5: Audit logs for enhanced security
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type VARCHAR(100) NOT NULL,
                device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
                user_id VARCHAR(255),
                ip_address INET,
                user_agent TEXT,
                payload JSONB DEFAULT '{}',
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_devices_fingerprint ON devices(fingerprint)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_device_links_expires ON device_links(expires_at)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_control_requests_device ON control_requests(device_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_control_sessions_device ON control_sessions(device_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC)')
        
    logger.info("Database initialized successfully with Phase 2.5 enhancements")

# ==================== NATS ====================

async def init_nats():
    """Initialize NATS connection"""
    global nc
    nc = await nats.connect(NATS_URL)
    logger.info(f"Connected to NATS at {NATS_URL}")

async def publish_event(subject: str, data: dict):
    """Publish event to NATS"""
    if nc:
        await nc.publish(subject, json.dumps(data).encode())
        logger.info(f"Published to {subject}: {data}")

# ==================== Policy System ====================

def load_policy():
    """Load policy configuration"""
    try:
        if os.path.exists(POLICY_FILE):
            with open(POLICY_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default policy
            return {
                "streaming": {"enabled": True, "max_concurrent": 5},
                "control": {"enabled": True, "require_approval": True, "max_ttl_minutes": 30},
                "overseer": {"enabled": False, "endpoint": "http://localhost:9999/policy"}
            }
    except Exception as e:
        logger.error(f"Failed to load policy: {e}")
        return {"streaming": {"enabled": False}, "control": {"enabled": False}}

def check_policy_capability(capability: str, device_id: str = None) -> bool:
    """Check if capability is allowed by policy"""
    policy = load_policy()
    
    if capability == "streaming":
        return policy.get("streaming", {}).get("enabled", False)
    elif capability == "control":
        return policy.get("control", {}).get("enabled", False)
    
    return False

# ==================== LiveKit Integration ====================

def create_livekit_token(room_name: str, participant_name: str, can_publish: bool = False):
    """Create LiveKit access token"""
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit not configured")
    
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    
    if can_publish:
        token.with_grants(api.VideoGrants(
            room=room_name,
            room_join=True,
            can_publish=True,
            can_subscribe=True
        ))
    else:
        token.with_grants(api.VideoGrants(
            room=room_name,
            room_join=True,
            can_publish=False,
            can_subscribe=True
        ))
    
    return token.to_jwt()

# ==================== Background Tasks ====================

async def cleanup_expired_sessions():
    """Clean up expired links and control sessions"""
    while True:
        try:
            async with db_pool.acquire() as conn:
                now = datetime.utcnow()
                
                # Clean up expired links (from Phase 2)
                expired_links = await conn.fetch('''
                    SELECT device_id FROM device_links WHERE expires_at <= $1
                ''', now)
                
                if expired_links:
                    await conn.execute('DELETE FROM device_links WHERE expires_at <= $1', now)
                    for link in expired_links:
                        await publish_event("link.removed", {
                            "device_id": str(link['device_id']),
                            "reason": "TTL expired",
                            "timestamp": now.isoformat()
                        })
                
                # Clean up expired control requests
                expired_requests = await conn.fetch('''
                    UPDATE control_requests SET status = 'expired' 
                    WHERE status = 'pending' AND expires_at <= $1
                    RETURNING request_id, device_id
                ''', now)
                
                # Clean up expired control sessions
                expired_sessions = await conn.fetch('''
                    UPDATE control_sessions SET status = 'expired'
                    WHERE status = 'active' AND expires_at <= $1
                    RETURNING device_id, request_id
                ''', now)
                
                for session in expired_sessions:
                    await publish_event("control.revoked", {
                        "device_id": str(session['device_id']),
                        "request_id": str(session['request_id']),
                        "reason": "TTL expired",
                        "timestamp": now.isoformat()
                    })
                
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# ==================== Startup/Shutdown ====================

app_start_time = datetime.utcnow()

@app.on_event("startup")
async def startup():
    global app_start_time
    app_start_time = datetime.utcnow()
    await init_db()
    await init_nats()
    # Start background cleanup task
    asyncio.create_task(cleanup_expired_sessions())
    logger.info("Rika Core API Phase 2.5 started successfully on port 5317")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if nc:
        await nc.close()
    logger.info("Rika Core API shut down")

# ==================== Health Check ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Rika Core API",
        "status": "operational",
        "version": "2.5.0",
        "phase": "Streaming & Remote Control",
        "timestamp": datetime.utcnow()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check NATS
    nats_status = "healthy" if nc and not nc.is_closed else "disconnected"
    
    # Check LiveKit configuration
    livekit_status = "configured" if LIVEKIT_API_KEY and LIVEKIT_API_SECRET else "not_configured"
    
    # Check policy
    policy = load_policy()
    policy_status = "loaded" if policy else "error"
    
    return {
        "status": "healthy" if all(s in ["healthy", "configured", "loaded"] for s in [db_status, nats_status, livekit_status, policy_status]) else "degraded",
        "database": db_status,
        "nats": nats_status,
        "livekit": livekit_status,
        "policy": policy_status,
        "timestamp": datetime.utcnow()
    }

@app.get("/selfcheck")
async def self_check():
    """Comprehensive self-check of all components and active states"""
    components = {}
    warnings = []
    active_links = []
    
    # Check Database in detail
    try:
        async with db_pool.acquire() as conn:
            # Test basic connectivity
            await conn.fetchval("SELECT 1")
            
            # Count records in key tables
            control_count = await conn.fetchval("SELECT COUNT(*) FROM control_requests")
            session_count = await conn.fetchval("SELECT COUNT(*) FROM control_sessions WHERE status = 'active'")
            audit_count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs")
            
            # Get active device links
            links = await conn.fetch("""
                SELECT device_id, link_mode, link_expires_at, gestures_enabled
                FROM device_links 
                WHERE link_expires_at > NOW()
                ORDER BY link_expires_at DESC
                LIMIT 10
            """)
            active_links = [dict(link) for link in links] if links else []
            
            components["database"] = {
                "status": "healthy",
                "control_requests": control_count,
                "active_sessions": session_count,
                "audit_logs": audit_count,
                "active_links": len(active_links)
            }
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
        warnings.append(f"Database issue: {e}")
    
    # Check NATS in detail
    try:
        if nc and not nc.is_closed:
            components["nats"] = {
                "status": "healthy",
                "connected": True,
                "server": NATS_URL.split('@')[-1] if '@' in NATS_URL else NATS_URL
            }
        else:
            components["nats"] = {"status": "disconnected"}
            warnings.append("NATS not connected")
    except Exception as e:
        components["nats"] = {"status": "error", "error": str(e)}
        warnings.append(f"NATS issue: {e}")
    
    # Check MinIO
    try:
        minio_url = os.getenv("MINIO_URL", "http://localhost:9000")
        response = requests.get(f"{minio_url}/minio/health/live", timeout=5)
        if response.status_code == 200:
            components["minio"] = {"status": "healthy", "url": minio_url}
        else:
            components["minio"] = {"status": "degraded", "code": response.status_code}
            warnings.append(f"MinIO returned {response.status_code}")
    except Exception as e:
        components["minio"] = {"status": "unreachable", "error": str(e)}
        warnings.append(f"MinIO unreachable: {e}")
    
    # Check LiveKit
    if LIVEKIT_API_KEY and LIVEKIT_API_SECRET:
        components["livekit"] = {
            "status": "configured",
            "has_key": True,
            "has_secret": True,
            "url": LIVEKIT_URL
        }
    else:
        components["livekit"] = {"status": "not_configured"}
        warnings.append("LiveKit credentials missing")
    
    # Check n8n webhook
    n8n_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/rika-control-approval")
    try:
        # Just check if n8n is reachable
        n8n_base = n8n_url.split('/webhook')[0]
        response = requests.get(f"{n8n_base}/healthz", timeout=2)
        components["n8n"] = {"status": "reachable", "url": n8n_base}
    except:
        components["n8n"] = {"status": "unreachable", "url": n8n_base}
        warnings.append("n8n webhook endpoint unreachable")
    
    # Overall status
    critical_components = ["database", "nats"]
    overall_status = "healthy"
    
    for comp in critical_components:
        if comp in components and components[comp].get("status") != "healthy":
            overall_status = "unhealthy"
            break
    
    if overall_status == "healthy" and warnings:
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow(),
        "components": components,
        "active_links": active_links,
        "warnings": warnings,
        "version": "2.5.0",
        "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds() if 'app_start_time' in globals() else 0
    }

# ==================== Phase 2.5: Stream Management ====================

@app.get("/streams", response_model=List[StreamInfo])
async def get_streams():
    """Get LiveKit streaming info for linked devices in extend/view modes"""
    if not check_policy_capability("streaming"):
        raise HTTPException(status_code=403, detail="Streaming not allowed by policy")
    
    async with db_pool.acquire() as conn:
        # Get devices linked in view or extend mode
        streaming_devices = await conn.fetch('''
            SELECT dl.device_id, d.name, dl.mode, dl.expires_at
            FROM device_links dl
            JOIN devices d ON dl.device_id = d.id
            WHERE dl.mode IN ('view', 'extend') AND dl.expires_at > $1
        ''', datetime.utcnow())
        
        streams = []
        for device in streaming_devices:
            device_id = str(device['device_id'])
            room_name = f"rika-{device_id}"
            
            try:
                # Create participant token (for the device to publish)
                participant_token = create_livekit_token(
                    room_name=room_name,
                    participant_name=f"device-{device_id}",
                    can_publish=True
                )
                
                # Create viewer token (for Atlas UI to view)
                viewer_token = create_livekit_token(
                    room_name=room_name,
                    participant_name=f"viewer-{secrets.token_hex(4)}",
                    can_publish=False
                )
                
                streams.append(StreamInfo(
                    device_id=device_id,
                    device_name=device['name'],
                    room_name=room_name,
                    participant_token=participant_token,
                    viewer_token=viewer_token,
                    ws_url=LIVEKIT_WS_URL,
                    expires_at=device['expires_at']
                ))
                
            except Exception as e:
                logger.error(f"Failed to create LiveKit tokens for device {device_id}: {e}")
        
        return streams

# ==================== Phase 2.5: Control Management ====================

@app.post("/control/request", response_model=ControlResponse)
async def request_control(request: ControlRequest):
    """Request remote control access for a device"""
    if not check_policy_capability("control"):
        raise HTTPException(status_code=403, detail="Control not allowed by policy")
    
    async with db_pool.acquire() as conn:
        # Check if device exists and is linked in control mode
        device_link = await conn.fetchrow('''
            SELECT dl.device_id, d.name 
            FROM device_links dl
            JOIN devices d ON dl.device_id = d.id
            WHERE dl.device_id = $1 AND dl.mode = 'control' AND dl.expires_at > $2
        ''', uuid.UUID(request.device_id), datetime.utcnow())
        
        if not device_link:
            raise HTTPException(status_code=400, detail="Device must be linked in control mode")
        
        # Check for existing pending request
        existing = await conn.fetchrow('''
            SELECT request_id FROM control_requests 
            WHERE device_id = $1 AND status = 'pending'
        ''', uuid.UUID(request.device_id))
        
        if existing:
            raise HTTPException(status_code=409, detail="Control request already pending for this device")
        
        # Create control request
        request_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(minutes=request.ttl_minutes)
        
        await conn.execute('''
            INSERT INTO control_requests (request_id, device_id, reason, ttl_minutes, expires_at)
            VALUES ($1, $2, $3, $4, $5)
        ''', request_id, uuid.UUID(request.device_id), request.reason, request.ttl_minutes, expires_at)
        
        # Log audit event
        await conn.execute('''
            INSERT INTO audit_logs (event_type, device_id, payload)
            VALUES ('control_requested', $1, $2)
        ''', uuid.UUID(request.device_id), json.dumps({
            "request_id": str(request_id),
            "reason": request.reason,
            "ttl_minutes": request.ttl_minutes
        }))
    
    # Send to n8n for approval
    approval_url = f"rika://control/approve?request_id={request_id}"
    
    try:
        if N8N_WEBHOOK_URL:
            requests.post(N8N_WEBHOOK_URL, json={
                "request_id": str(request_id),
                "device_id": request.device_id,
                "device_name": device_link['name'],
                "reason": request.reason,
                "ttl_minutes": request.ttl_minutes,
                "expires_at": expires_at.isoformat(),
                "approval_url": approval_url
            }, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send n8n webhook: {e}")
    
    # Publish control request event
    await publish_event("control.requested", {
        "request_id": str(request_id),
        "device_id": request.device_id,
        "device_name": device_link['name'],
        "reason": request.reason,
        "ttl_minutes": request.ttl_minutes,
        "expires_at": expires_at.isoformat()
    })
    
    return ControlResponse(
        request_id=str(request_id),
        status="pending",
        expires_at=expires_at,
        approval_url=approval_url
    )

@app.post("/control/approve")
async def approve_control(approval: ControlApproval):
    """Approve or deny a control request"""
    async with db_pool.acquire() as conn:
        # Get control request
        request_record = await conn.fetchrow('''
            SELECT cr.*, d.name as device_name
            FROM control_requests cr
            JOIN devices d ON cr.device_id = d.id
            WHERE cr.request_id = $1 AND cr.status = 'pending'
        ''', uuid.UUID(approval.request_id))
        
        if not request_record:
            raise HTTPException(status_code=404, detail="Control request not found or already processed")
        
        # Update request status
        new_status = 'approved' if approval.approved else 'denied'
        await conn.execute('''
            UPDATE control_requests 
            SET status = $1, approved_at = $2, approver = $3
            WHERE request_id = $4
        ''', new_status, datetime.utcnow(), approval.approver, uuid.UUID(approval.request_id))
        
        device_id = str(request_record['device_id'])
        
        if approval.approved:
            # Create active control session
            session_expires = datetime.utcnow() + timedelta(minutes=request_record['ttl_minutes'])
            
            await conn.execute('''
                INSERT INTO control_sessions (device_id, request_id, expires_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (device_id) DO UPDATE SET
                    request_id = EXCLUDED.request_id,
                    expires_at = EXCLUDED.expires_at,
                    status = 'active',
                    created_at = CURRENT_TIMESTAMP
            ''', request_record['device_id'], uuid.UUID(approval.request_id), session_expires)
            
            # Publish control granted event
            await publish_event("control.granted", {
                "request_id": approval.request_id,
                "device_id": device_id,
                "device_name": request_record['device_name'],
                "approver": approval.approver,
                "expires_at": session_expires.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Control approved for device {device_id} by {approval.approver}")
        else:
            # Publish control denied event
            await publish_event("control.denied", {
                "request_id": approval.request_id,
                "device_id": device_id,
                "device_name": request_record['device_name'],
                "approver": approval.approver,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Log audit event
        await conn.execute('''
            INSERT INTO audit_logs (event_type, device_id, user_id, payload)
            VALUES ('control_approval', $1, $2, $3)
        ''', request_record['device_id'], approval.approver, json.dumps({
            "request_id": approval.request_id,
            "approved": approval.approved
        }))
    
    return {"status": f"control_{new_status}", "request_id": approval.request_id}

@app.post("/control/revoke")
async def revoke_control(revoke: ControlRevoke):
    """Revoke active control session"""
    async with db_pool.acquire() as conn:
        # Get active control session
        session = await conn.fetchrow('''
            SELECT cs.*, d.name as device_name, cr.request_id
            FROM control_sessions cs
            JOIN devices d ON cs.device_id = d.id
            JOIN control_requests cr ON cs.request_id = cr.request_id
            WHERE cs.device_id = $1 AND cs.status = 'active'
        ''', uuid.UUID(revoke.device_id))
        
        if not session:
            raise HTTPException(status_code=404, detail="No active control session found")
        
        # Revoke session
        await conn.execute('''
            UPDATE control_sessions SET status = 'revoked'
            WHERE device_id = $1 AND status = 'active'
        ''', uuid.UUID(revoke.device_id))
        
        await conn.execute('''
            UPDATE control_requests SET revoked_at = CURRENT_TIMESTAMP
            WHERE request_id = $1
        ''', session['request_id'])
        
        # Log audit event
        await conn.execute('''
            INSERT INTO audit_logs (event_type, device_id, payload)
            VALUES ('control_revoked', $1, $2)
        ''', uuid.UUID(revoke.device_id), json.dumps({
            "reason": revoke.reason,
            "request_id": str(session['request_id'])
        }))
    
    # Publish control revoked event
    await publish_event("control.revoked", {
        "device_id": revoke.device_id,
        "device_name": session['device_name'],
        "request_id": str(session['request_id']),
        "reason": revoke.reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "control_revoked", "device_id": revoke.device_id}

@app.post("/control/input")
async def send_control_input(input_event: ControlInputEvent):
    """Send input event to controlled device"""
    async with db_pool.acquire() as conn:
        # Verify active control session
        session = await conn.fetchrow('''
            SELECT * FROM control_sessions 
            WHERE device_id = $1 AND status = 'active' AND expires_at > $2
        ''', uuid.UUID(input_event.device_id), datetime.utcnow())
        
        if not session:
            raise HTTPException(status_code=403, detail="No active control session")
    
    # Send input event via NATS
    await publish_event(f"control.input.{input_event.device_id}", {
        "type": input_event.event_type,
        "payload": input_event.payload,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "input_sent"}

# ==================== Enhanced Presence (with control status) ====================

@app.get("/presence", response_model=List[DevicePresence])
async def get_presence():
    """Get all devices and their status including control sessions"""
    async with db_pool.acquire() as conn:
        devices = await conn.fetch('''
            SELECT 
                d.id, d.name, d.type, d.last_seen, d.last_active_app, d.status,
                dl.mode, dl.gestures_enabled, dl.expires_at as link_expires_at, dl.updated_at,
                cs.status as control_status, cs.expires_at as control_expires_at
            FROM devices d
            LEFT JOIN device_links dl ON d.id = dl.device_id AND dl.expires_at > $1
            LEFT JOIN control_sessions cs ON d.id = cs.device_id AND cs.status = 'active' AND cs.expires_at > $1
            ORDER BY d.last_seen DESC
        ''', datetime.utcnow())
        
        return [
            DevicePresence(
                device_id=str(device['id']),
                name=device['name'],
                type=device['type'],
                last_seen=device['last_seen'],
                last_active_app=device['last_active_app'],
                status=device['status'],
                linked=device['mode'] is not None,
                link_mode=device['mode'],
                link_expires_at=device['link_expires_at'],
                gestures_enabled=device['gestures_enabled'] or False,
                control_status=device['control_status'],
                control_expires_at=device['control_expires_at']
            )
            for device in devices
        ]

# ==================== Phase 1 & 2 Endpoints (keep existing functionality) ====================
# [Include all existing endpoints from Phase 2]

# ==================== Blackout (Enhanced) ====================

@app.post("/blackout")
async def trigger_blackout(request: BlackoutRequest):
    """Enhanced blackout - also revokes all control sessions"""
    async with db_pool.acquire() as conn:
        # Revoke all active sessions
        await conn.execute('UPDATE sessions SET is_active = false WHERE is_active = true')
        
        # Remove all active links
        await conn.execute('DELETE FROM device_links WHERE expires_at > $1', datetime.utcnow())
        
        # Revoke all control sessions
        await conn.execute('UPDATE control_sessions SET status = \'revoked\' WHERE status = \'active\'')
        
        # Disable all hands-on sessions
        await conn.execute('UPDATE hands_on_sessions SET enabled = false WHERE enabled = true')
        
        # Update all devices to offline
        await conn.execute('UPDATE devices SET status = \'blackout\' WHERE status = \'active\'')
        
        # Log blackout event
        await conn.execute('''
            INSERT INTO audit_logs (event_type, device_id, payload)
            VALUES ('blackout_triggered', $1, $2)
        ''', uuid.UUID(request.device_id) if request.device_id else None,
            json.dumps({"reason": request.reason}))
    
    # Broadcast blackout event
    await publish_event("blackout", {
        "triggered_by": request.device_id,
        "reason": request.reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.warning(f"BLACKOUT triggered by device {request.device_id}: {request.reason}")
    
    return {
        "status": "blackout_activated",
        "affected_devices": "all",
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    import uvicorn
    # Run on port 5317 as specified in requirements
    uvicorn.run(app, host="0.0.0.0", port=5317, reload=True)