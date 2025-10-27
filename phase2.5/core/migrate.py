#!/usr/bin/env python3
"""
Phase 2.5 Database Migration Script
Creates the required tables for Phase 2.5 functionality
"""

import asyncio
import asyncpg
import os
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rika:password@localhost/rika_db')

async def create_phase25_tables():
    """Create all Phase 2.5 database tables"""
    print(f"Connecting to database: {DATABASE_URL}")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Database connection established")
        
        # Create control_requests table
        print("Creating control_requests table...")
        await conn.execute('''
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
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_control_requests_device_id ON control_requests(device_id);
            CREATE INDEX IF NOT EXISTS idx_control_requests_status ON control_requests(status);
            CREATE INDEX IF NOT EXISTS idx_control_requests_created_at ON control_requests(created_at);
        ''')
        print("✅ control_requests table created")
        
        # Create control_sessions table
        print("Creating control_sessions table...")
        await conn.execute('''
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
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_control_sessions_device_id ON control_sessions(device_id);
            CREATE INDEX IF NOT EXISTS idx_control_sessions_status ON control_sessions(status);
            CREATE INDEX IF NOT EXISTS idx_control_sessions_expires_at ON control_sessions(expires_at);
        ''')
        print("✅ control_sessions table created")
        
        # Create audit_logs table
        print("Creating audit_logs table...")
        await conn.execute('''
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
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_device_id ON audit_logs(device_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);
        ''')
        print("✅ audit_logs table created")
        
        # Create stream_sessions table
        print("Creating stream_sessions table...")
        await conn.execute('''
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
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_stream_sessions_device_id ON stream_sessions(device_id);
            CREATE INDEX IF NOT EXISTS idx_stream_sessions_status ON stream_sessions(status);
            CREATE INDEX IF NOT EXISTS idx_stream_sessions_room_name ON stream_sessions(room_name);
        ''')
        print("✅ stream_sessions table created")
        
        # Verify table creation
        print("\nVerifying table creation...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN 
            ('control_requests', 'control_sessions', 'audit_logs', 'stream_sessions')
            ORDER BY table_name;
        """)
        
        print("Created tables:")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"  - {table['table_name']}: {count} records")
        
        # Insert initial audit log
        await conn.execute("""
            INSERT INTO audit_logs (event_type, user_id, details, timestamp)
            VALUES ('database_migration', 'system', $1, NOW());
        """, {
            'migration_version': '2.5.0',
            'tables_created': ['control_requests', 'control_sessions', 'audit_logs', 'stream_sessions'],
            'migration_time': datetime.now().isoformat()
        })
        
        print("\n🎉 Phase 2.5 database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if 'conn' in locals():
            await conn.close()
            print("Database connection closed")

def main():
    """Main migration function"""
    print("🚀 Starting Phase 2.5 Database Migration")
    print("=" * 40)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not found, using system environment")
    
    # Run migration
    asyncio.run(create_phase25_tables())

if __name__ == '__main__':
    main()