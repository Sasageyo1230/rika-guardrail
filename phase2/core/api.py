# core/api.py
"""
Rika Core API Service - Phase 2
Handles device enrollment, presence tracking, control events, and device linking
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Rika Core API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core")
NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")
TOKEN_EXPIRY_MINUTES = int(os.getenv("TOKEN_EXPIRY_MINUTES", "5"))

# Global connections
db_pool = None
nc = None

# ==================== Models ====================

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

class BlackoutRequest(BaseModel):
    device_id: str
    reason: Optional[str] = "Manual blackout triggered"

# ==================== Phase 2 Models ====================

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

# ==================== Database ====================

async def init_db():
    """Initialize database connection pool and create tables"""
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    
    # Create tables if they don't exist
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
        
        # Phase 2: Hands-on mode tracking
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS hands_on_sessions (
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                enabled BOOLEAN DEFAULT false,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id)
            )
        ''')
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_devices_fingerprint ON devices(fingerprint)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_device_links_expires ON device_links(expires_at)')
        
    logger.info("Database initialized successfully")

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

# ==================== Background Tasks ====================

async def cleanup_expired_links():
    """Remove expired device links"""
    while True:
        try:
            async with db_pool.acquire() as conn:
                expired_links = await conn.fetch('''
                    SELECT device_id FROM device_links 
                    WHERE expires_at <= $1
                ''', datetime.utcnow())
                
                if expired_links:
                    device_ids = [str(link['device_id']) for link in expired_links]
                    
                    # Remove expired links
                    await conn.execute('''
                        DELETE FROM device_links WHERE expires_at <= $1
                    ''', datetime.utcnow())
                    
                    # Publish unlink events
                    for device_id in device_ids:
                        await publish_event("link.removed", {
                            "device_id": device_id,
                            "reason": "TTL expired",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    logger.info(f"Cleaned up {len(device_ids)} expired links")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired links: {e}")
        
        # Check every 30 seconds
        await asyncio.sleep(30)

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup():
    await init_db()
    await init_nats()
    # Start background cleanup task
    asyncio.create_task(cleanup_expired_links())
    logger.info("Rika Core API Phase 2 started successfully")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if nc:
        await nc.close()
    logger.info("Rika Core API shut down")

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Rika Core API",
        "status": "operational",
        "version": "2.0.0",
        "phase": "Atlas & Linking System",
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
    
    return {
        "status": "healthy" if db_status == "healthy" and nats_status == "healthy" else "degraded",
        "database": db_status,
        "nats": nats_status,
        "timestamp": datetime.utcnow()
    }

# ==================== Device Management (Phase 1) ====================

@app.post("/enroll", response_model=EnrollResponse)
async def enroll_device(request: EnrollRequest):
    """Generate a short-lived token for device enrollment"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO enrollment_tokens (token, device_name, device_type, expires_at)
            VALUES ($1, $2, $3, $4)
        ''', token, request.device_name, request.device_type, expires_at)
        
        # Log the enrollment request
        await conn.execute('''
            INSERT INTO logs (event_type, payload)
            VALUES ('enrollment_initiated', $1)
        ''', json.dumps({"device_name": request.device_name, "device_type": request.device_type}))
    
    # Publish enrollment event
    await publish_event("enrollment.initiated", {
        "device_name": request.device_name,
        "device_type": request.device_type,
        "expires_at": expires_at.isoformat()
    })
    
    enrollment_url = f"rika://enroll?token={token}"
    
    return EnrollResponse(
        token=token,
        expires_at=expires_at,
        enrollment_url=enrollment_url
    )

@app.post("/enroll/complete", response_model=CompleteEnrollResponse)
async def complete_enrollment(request: CompleteEnrollRequest):
    """Complete device enrollment with fingerprint"""
    async with db_pool.acquire() as conn:
        # Check if token is valid
        token_record = await conn.fetchrow('''
            SELECT * FROM enrollment_tokens
            WHERE token = $1 AND expires_at > $2 AND used = false
        ''', request.token, datetime.utcnow())
        
        if not token_record:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        # Check if fingerprint already exists
        existing = await conn.fetchrow('''
            SELECT id FROM devices WHERE fingerprint = $1
        ''', request.fingerprint)
        
        if existing:
            raise HTTPException(status_code=409, detail="Device already enrolled")
        
        # Create device
        device_id = await conn.fetchval('''
            INSERT INTO devices (name, type, fingerprint, status)
            VALUES ($1, $2, $3, 'active')
            RETURNING id
        ''', token_record['device_name'], token_record['device_type'], request.fingerprint)
        
        # Mark token as used
        await conn.execute('''
            UPDATE enrollment_tokens SET used = true WHERE token = $1
        ''', request.token)
        
        # Create session
        session_token = secrets.token_urlsafe(48)
        session_expires = datetime.utcnow() + timedelta(days=30)
        
        await conn.execute('''
            INSERT INTO sessions (device_id, token, expires_at)
            VALUES ($1, $2, $3)
        ''', device_id, session_token, session_expires)
        
        # Log enrollment completion
        await conn.execute('''
            INSERT INTO logs (event_type, device_id, payload)
            VALUES ('enrollment_completed', $1, $2)
        ''', device_id, json.dumps({"fingerprint": request.fingerprint}))
    
    # Publish enrollment completed event
    await publish_event("enrollment.completed", {
        "device_id": str(device_id),
        "device_name": token_record['device_name'],
        "device_type": token_record['device_type']
    })
    
    return CompleteEnrollResponse(
        device_id=str(device_id),
        credentials={
            "session_token": session_token,
            "nats_url": NATS_URL.replace(os.getenv("NATS_PASSWORD", ""), "***")
        },
        nats_subjects=[
            "presence.updated",
            "handoff.requested", 
            "control.granted",
            "blackout",
            "link.added",
            "link.removed",
            "hands_on.enabled",
            "hands_on.disabled",
            f"device.{device_id}.control"
        ]
    )

@app.get("/presence", response_model=List[DevicePresence])
async def get_presence():
    """Get all devices and their last active context including link status"""
    async with db_pool.acquire() as conn:
        devices = await conn.fetch('''
            SELECT 
                d.id, d.name, d.type, d.last_seen, d.last_active_app, d.status,
                dl.mode, dl.gestures_enabled, dl.expires_at, dl.updated_at
            FROM devices d
            LEFT JOIN device_links dl ON d.id = dl.device_id AND dl.expires_at > $1
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
                link_expires_at=device['expires_at'],
                gestures_enabled=device['gestures_enabled'] or False
            )
            for device in devices
        ]

@app.post("/heartbeat")
async def device_heartbeat(heartbeat: DeviceHeartbeat, background_tasks: BackgroundTasks):
    """Receive heartbeat from device"""
    async with db_pool.acquire() as conn:
        # Update device last seen and active app
        result = await conn.fetchrow('''
            UPDATE devices 
            SET last_seen = $1, last_active_app = $2, status = 'active'
            WHERE id = $3
            RETURNING name, type
        ''', datetime.utcnow(), heartbeat.current_app, uuid.UUID(heartbeat.device_id))
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Log heartbeat
        await conn.execute('''
            INSERT INTO logs (event_type, device_id, payload)
            VALUES ('heartbeat', $1, $2)
        ''', uuid.UUID(heartbeat.device_id), json.dumps({
            "current_app": heartbeat.current_app,
            "window_title": heartbeat.window_title,
            "metadata": heartbeat.metadata
        }))
    
    # Publish presence update in background
    background_tasks.add_task(
        publish_event,
        "presence.updated",
        {
            "device_id": heartbeat.device_id,
            "device_name": result['name'],
            "device_type": result['type'],
            "current_app": heartbeat.current_app,
            "window_title": heartbeat.window_title,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {"status": "ok", "timestamp": datetime.utcnow()}

@app.post("/blackout")
async def trigger_blackout(request: BlackoutRequest):
    """Broadcast blackout event and revoke all tokens"""
    async with db_pool.acquire() as conn:
        # Revoke all active sessions
        await conn.execute('''
            UPDATE sessions SET is_active = false WHERE is_active = true
        ''')
        
        # Remove all active links
        await conn.execute('''
            DELETE FROM device_links WHERE expires_at > $1
        ''', datetime.utcnow())
        
        # Disable all hands-on sessions
        await conn.execute('''
            UPDATE hands_on_sessions SET enabled = false WHERE enabled = true
        ''')
        
        # Update all devices to offline
        await conn.execute('''
            UPDATE devices SET status = 'blackout' WHERE status = 'active'
        ''')
        
        # Log blackout event
        await conn.execute('''
            INSERT INTO logs (event_type, device_id, payload)
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

# ==================== Phase 2: Linking System ====================

@app.post("/link")
async def link_device(request: LinkRequest):
    """Link a device with specified mode and TTL"""
    expires_at = datetime.utcnow() + timedelta(minutes=request.ttl_minutes)
    
    async with db_pool.acquire() as conn:
        # Check if device exists
        device = await conn.fetchrow('''
            SELECT id, name, type FROM devices WHERE id = $1 AND status = 'active'
        ''', uuid.UUID(request.device_id))
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found or not active")
        
        # Insert or update link
        await conn.execute('''
            INSERT INTO device_links (device_id, mode, gestures_enabled, expires_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (device_id) DO UPDATE SET
                mode = EXCLUDED.mode,
                gestures_enabled = EXCLUDED.gestures_enabled, 
                expires_at = EXCLUDED.expires_at,
                updated_at = EXCLUDED.updated_at
        ''', uuid.UUID(request.device_id), request.mode, request.gestures, expires_at, datetime.utcnow())
        
        # Log link event
        await conn.execute('''
            INSERT INTO logs (event_type, device_id, payload)
            VALUES ('device_linked', $1, $2)
        ''', uuid.UUID(request.device_id), json.dumps({
            "mode": request.mode,
            "gestures": request.gestures,
            "ttl_minutes": request.ttl_minutes
        }))
    
    # Publish link event
    await publish_event("link.added", {
        "device_id": request.device_id,
        "device_name": device['name'],
        "device_type": device['type'],
        "mode": request.mode,
        "gestures_enabled": request.gestures,
        "expires_at": expires_at.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "status": "linked",
        "device_id": request.device_id,
        "mode": request.mode,
        "gestures_enabled": request.gestures,
        "expires_at": expires_at
    }

@app.post("/unlink")
async def unlink_device(request: UnlinkRequest):
    """Unlink one device or all devices"""
    async with db_pool.acquire() as conn:
        if request.device_id:
            # Unlink specific device
            unlinked = await conn.fetchrow('''
                DELETE FROM device_links 
                WHERE device_id = $1
                RETURNING device_id
            ''', uuid.UUID(request.device_id))
            
            if not unlinked:
                raise HTTPException(status_code=404, detail="Device not linked")
            
            # Get device info for event
            device = await conn.fetchrow('''
                SELECT name, type FROM devices WHERE id = $1
            ''', uuid.UUID(request.device_id))
            
            # Publish unlink event
            await publish_event("link.removed", {
                "device_id": request.device_id,
                "device_name": device['name'],
                "device_type": device['type'],
                "reason": "Manual unlink",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Log unlink event
            await conn.execute('''
                INSERT INTO logs (event_type, device_id, payload)
                VALUES ('device_unlinked', $1, $2)
            ''', uuid.UUID(request.device_id), json.dumps({"reason": "Manual unlink"}))
            
            return {"status": "unlinked", "device_id": request.device_id}
        
        else:
            # Unlink all devices
            linked_devices = await conn.fetch('''
                SELECT dl.device_id, d.name, d.type 
                FROM device_links dl
                JOIN devices d ON dl.device_id = d.id
            ''')
            
            await conn.execute('DELETE FROM device_links')
            
            # Publish unlink events for all devices
            for device in linked_devices:
                await publish_event("link.removed", {
                    "device_id": str(device['device_id']),
                    "device_name": device['name'],
                    "device_type": device['type'],
                    "reason": "Unlink all",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Log bulk unlink
            await conn.execute('''
                INSERT INTO logs (event_type, payload)
                VALUES ('all_devices_unlinked', $1)
            ''', json.dumps({"count": len(linked_devices)}))
            
            return {"status": "all_unlinked", "count": len(linked_devices)}

@app.get("/links", response_model=List[DeviceLink])
async def get_links():
    """Get all currently linked devices"""
    async with db_pool.acquire() as conn:
        links = await conn.fetch('''
            SELECT 
                dl.device_id, d.name, dl.mode, dl.gestures_enabled, 
                dl.expires_at, dl.updated_at
            FROM device_links dl
            JOIN devices d ON dl.device_id = d.id
            WHERE dl.expires_at > $1
            ORDER BY dl.updated_at DESC
        ''', datetime.utcnow())
        
        return [
            DeviceLink(
                device_id=str(link['device_id']),
                device_name=link['name'],
                mode=link['mode'],
                gestures_enabled=link['gestures_enabled'],
                expires_at=link['expires_at'],
                updated_at=link['updated_at']
            )
            for link in links
        ]

# ==================== Phase 2: Hands On Mode ====================

@app.post("/hands-on")
async def toggle_hands_on_mode(request: HandsOnRequest):
    """Enable or disable hands-on gesture mode for a device"""
    async with db_pool.acquire() as conn:
        # Check if device exists and is linked
        device = await conn.fetchrow('''
            SELECT d.name, d.type, dl.mode
            FROM devices d
            LEFT JOIN device_links dl ON d.id = dl.device_id AND dl.expires_at > $2
            WHERE d.id = $1 AND d.status = 'active'
        ''', uuid.UUID(request.device_id), datetime.utcnow())
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found or not active")
        
        if not device['mode']:
            raise HTTPException(status_code=400, detail="Device must be linked to use hands-on mode")
        
        # Update or insert hands-on session
        await conn.execute('''
            INSERT INTO hands_on_sessions (device_id, enabled, started_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (device_id) DO UPDATE SET
                enabled = EXCLUDED.enabled,
                started_at = EXCLUDED.started_at
        ''', uuid.UUID(request.device_id), request.enabled, datetime.utcnow())
        
        # Log hands-on event
        await conn.execute('''
            INSERT INTO logs (event_type, device_id, payload)
            VALUES ('hands_on_toggled', $1, $2)
        ''', uuid.UUID(request.device_id), json.dumps({"enabled": request.enabled}))
    
    # Publish hands-on event
    event_subject = "hands_on.enabled" if request.enabled else "hands_on.disabled"
    await publish_event(event_subject, {
        "device_id": request.device_id,
        "device_name": device['name'],
        "device_type": device['type'],
        "enabled": request.enabled,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "status": "hands_on_enabled" if request.enabled else "hands_on_disabled",
        "device_id": request.device_id,
        "enabled": request.enabled
    }

# ==================== Legacy Endpoints ====================

@app.post("/control/grant")
async def grant_control(device_id: str, target_device_id: str):
    """Grant control from one device to another"""
    await publish_event("control.granted", {
        "from_device": device_id,
        "to_device": target_device_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "control_granted", "from": device_id, "to": target_device_id}

@app.post("/handoff/request")
async def request_handoff(from_device: str, to_device: str, context: dict):
    """Request context handoff between devices"""
    await publish_event("handoff.requested", {
        "from_device": from_device,
        "to_device": to_device,
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "handoff_requested"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)