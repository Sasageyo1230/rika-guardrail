-- Phase 2.5 Database Schema
-- Creates tables for streaming and control functionality

-- Control requests table
CREATE TABLE IF NOT EXISTS control_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    requester VARCHAR(100) NOT NULL,
    reason TEXT,
    ttl_minutes INTEGER NOT NULL DEFAULT 15,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    expires_at TIMESTAMP,
    n8n_execution_id VARCHAR(50)
);

-- Control requests indexes
CREATE INDEX IF NOT EXISTS idx_control_requests_device_id ON control_requests(device_id);
CREATE INDEX IF NOT EXISTS idx_control_requests_status ON control_requests(status);
CREATE INDEX IF NOT EXISTS idx_control_requests_created_at ON control_requests(created_at);

-- Control sessions table
CREATE TABLE IF NOT EXISTS control_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    requester VARCHAR(100) NOT NULL,
    request_id VARCHAR(50) REFERENCES control_requests(request_id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW(),
    terminated_at TIMESTAMP,
    termination_reason VARCHAR(100)
);

-- Control sessions indexes
CREATE INDEX IF NOT EXISTS idx_control_sessions_device_id ON control_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_control_sessions_status ON control_sessions(status);
CREATE INDEX IF NOT EXISTS idx_control_sessions_expires_at ON control_sessions(expires_at);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(100),
    device_id VARCHAR(50),
    session_id VARCHAR(50),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_device_id ON audit_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);

-- Stream sessions table
CREATE TABLE IF NOT EXISTS stream_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    requester VARCHAR(100) NOT NULL,
    quality VARCHAR(20) DEFAULT '720p',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    terminated_at TIMESTAMP,
    viewer_count INTEGER DEFAULT 0,
    bandwidth_mbps DECIMAL(5,2)
);

-- Stream sessions indexes
CREATE INDEX IF NOT EXISTS idx_stream_sessions_device_id ON stream_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_status ON stream_sessions(status);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_room_name ON stream_sessions(room_name);

-- Insert initial audit log
INSERT INTO audit_logs (event_type, user_id, details, timestamp)
VALUES (
    'database_migration', 
    'system', 
    '{"migration_version": "2.5.0", "tables_created": ["control_requests", "control_sessions", "audit_logs", "stream_sessions"]}'::jsonb,
    NOW()
) ON CONFLICT DO NOTHING;

-- Verify table creation
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_name IN ('control_requests', 'control_sessions', 'audit_logs', 'stream_sessions')
ORDER BY table_name;