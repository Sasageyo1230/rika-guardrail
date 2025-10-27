# core/api.py
"""
Rika Core API Service
Handles device enrollment, presence tracking, and control events
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
app = FastAPI(title="Rika Core API", version="1.0.0")

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

class BlackoutRequest(BaseModel):
    device_id: str
    reason: Optional[str] = "Manual blackout triggered"

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
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_devices_fingerprint ON devices(fingerprint)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)')
        
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

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup():
    await init_db()
    await init_nats()
    logger.info("Rika Core API started successfully")

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
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }

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
            f"device.{device_id}.control"
        ]
    )

@app.get("/presence", response_model=List[DevicePresence])
async def get_presence():
    """Get all devices and their last active context"""
    async with db_pool.acquire() as conn:
        devices = await conn.fetch('''
            SELECT id, name, type, last_seen, last_active_app, status
            FROM devices
            ORDER BY last_seen DESC
        ''')
        
        return [
            DevicePresence(
                device_id=str(device['id']),
                name=device['name'],
                type=device['type'],
                last_seen=device['last_seen'],
                last_active_app=device['last_active_app'],
                status=device['status']
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