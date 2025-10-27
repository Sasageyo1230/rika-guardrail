-- Phase 2 Database Schema
-- Cognitive Sphere and Agent Management

-- Cognitive data storage
CREATE TABLE IF NOT EXISTS cognitive_data (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,  -- "email_relationship", "schedule_pattern", "coding_style", etc.
    source VARCHAR(50) NOT NULL,      -- "gmail", "calendar", "github", "projects"
    content TEXT NOT NULL,            -- encrypted JSON
    embedding_id VARCHAR(100),        -- reference to vector store
    timestamp TIMESTAMP,
    relevance_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_data_type (data_type),
    INDEX idx_source (source),
    INDEX idx_timestamp (timestamp)
);

-- Cognitive profile (synthesized user attributes)
CREATE TABLE IF NOT EXISTS cognitive_profile (
    id SERIAL PRIMARY KEY,
    attribute VARCHAR(100) NOT NULL UNIQUE,  -- "works_best_9am_11am", "prefers_async_communication", etc.
    confidence FLOAT DEFAULT 0.8,
    source VARCHAR(255),     -- how we inferred this
    last_updated TIMESTAMP DEFAULT NOW(),
    INDEX idx_attribute (attribute)
);

-- Conversation history
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    user_input TEXT NOT NULL,
    rika_response JSONB,  -- {text, confidence, actions_taken, decision_log}
    context_used JSONB,   -- list of sources used
    feedback TEXT,        -- user correction/rating
    timestamp TIMESTAMP DEFAULT NOW(),
    encrypted BOOLEAN DEFAULT TRUE,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
);

-- Agent permissions and data access
CREATE TABLE IF NOT EXISTS agent_permissions (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    requested_data_types JSONB,
    approved_data_types JSONB,
    approved_by_user BOOLEAN DEFAULT FALSE,
    requested_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    INDEX idx_agent_name (agent_name)
);

-- Agent data access log
CREATE TABLE IF NOT EXISTS agent_access_log (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- "read", "write", "request"
    reason TEXT,
    approved BOOLEAN,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_agent_name (agent_name),
    INDEX idx_timestamp (timestamp)
);

-- Mint agent - YouTube videos
CREATE TABLE IF NOT EXISTS mint_videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(100) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB,
    scheduled_time TIMESTAMP,
    published_time TIMESTAMP,
    status VARCHAR(50) NOT NULL,  -- DRAFT, SCHEDULED, PUBLISHED, FAILED
    views INT DEFAULT 0,
    revenue FLOAT DEFAULT 0,
    metadata JSONB,  -- Additional video metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_video_id (video_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time)
);

-- Mint agent - YouTube analytics
CREATE TABLE IF NOT EXISTS mint_analytics (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(100),
    metric_type VARCHAR(50) NOT NULL,  -- "views", "engagement", "revenue", "ctr"
    value FLOAT NOT NULL,
    date DATE NOT NULL,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_video_id (video_id),
    INDEX idx_metric_type (metric_type),
    INDEX idx_date (date),
    FOREIGN KEY (video_id) REFERENCES mint_videos(video_id) ON DELETE CASCADE
);

-- Mint agent - Scheduled actions
CREATE TABLE IF NOT EXISTS mint_scheduled_actions (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,  -- "upload_video", "analyze_performance"
    video_id VARCHAR(100),
    scheduled_for TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETED, FAILED
    result JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_scheduled_for (scheduled_for),
    INDEX idx_status (status),
    FOREIGN KEY (video_id) REFERENCES mint_videos(video_id) ON DELETE SET NULL
);

-- Action approvals (for actions requiring user approval)
CREATE TABLE IF NOT EXISTS action_approvals (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB NOT NULL,
    requested_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    approved BOOLEAN,
    user_response TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, DENIED, EXPIRED
    INDEX idx_agent_name (agent_name),
    INDEX idx_status (status),
    INDEX idx_requested_at (requested_at)
);

-- System events and audit trail
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    agent_name VARCHAR(50),
    user_id VARCHAR(50),
    event_data JSONB,
    severity VARCHAR(20) DEFAULT 'INFO',  -- INFO, WARNING, ERROR, CRITICAL
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_event_type (event_type),
    INDEX idx_agent_name (agent_name),
    INDEX idx_timestamp (timestamp)
);

-- Create views for common queries

-- Recent conversations with context
CREATE OR REPLACE VIEW recent_conversations AS
SELECT
    id,
    user_id,
    user_input,
    rika_response->>'text' as response_text,
    rika_response->>'confidence' as confidence,
    context_used,
    timestamp
FROM conversations
ORDER BY timestamp DESC
LIMIT 100;

-- Agent activity summary
CREATE OR REPLACE VIEW agent_activity_summary AS
SELECT
    agent_name,
    COUNT(*) as access_count,
    COUNT(DISTINCT data_type) as unique_data_types,
    MAX(timestamp) as last_access
FROM agent_access_log
GROUP BY agent_name;

-- Mint video performance
CREATE OR REPLACE VIEW mint_video_performance AS
SELECT
    v.video_id,
    v.title,
    v.status,
    v.published_time,
    MAX(CASE WHEN a.metric_type = 'views' THEN a.value END) as total_views,
    MAX(CASE WHEN a.metric_type = 'revenue' THEN a.value END) as total_revenue,
    MAX(CASE WHEN a.metric_type = 'engagement' THEN a.value END) as engagement_rate
FROM mint_videos v
LEFT JOIN mint_analytics a ON v.video_id = a.video_id
GROUP BY v.video_id, v.title, v.status, v.published_time;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rika_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rika_user;
