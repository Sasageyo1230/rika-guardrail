# core/cleanup_script.py
"""
Rika Phase 2 Cleanup Script
Automated cleanup of expired links, old thumbnails, and system maintenance
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime, timedelta
from minio import Minio
from dotenv import load_dotenv
import logging
import json

# Load environment
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "rikaadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "RikaMinIO2025SecureStorage")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "rika-screenshots")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RikaCleanupManager:
    def __init__(self):
        self.db_pool = None
        self.minio_client = None
        
    async def init_db(self):
        """Initialize database connection"""
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def init_minio(self):
        """Initialize MinIO client"""
        try:
            self.minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            logger.info("✅ Connected to MinIO")
            return True
        except Exception as e:
            logger.error(f"❌ MinIO connection failed: {e}")
            return False
    
    async def cleanup_expired_links(self):
        """Remove expired device links from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get expired links before deletion
                expired_links = await conn.fetch('''
                    SELECT device_id, mode FROM device_links 
                    WHERE expires_at <= $1
                ''', datetime.utcnow())
                
                if expired_links:
                    # Delete expired links
                    deleted_count = await conn.fetchval('''
                        DELETE FROM device_links 
                        WHERE expires_at <= $1
                        RETURNING COUNT(*)
                    ''', datetime.utcnow())
                    
                    # Log cleanup
                    await conn.execute('''
                        INSERT INTO logs (event_type, payload)
                        VALUES ('cleanup_expired_links', $1)
                    ''', json.dumps({
                        "count": deleted_count,
                        "expired_links": [
                            {"device_id": str(link['device_id']), "mode": link['mode']} 
                            for link in expired_links
                        ]
                    }))
                    
                    logger.info(f"✅ Cleaned up {deleted_count} expired device links")
                    return deleted_count
                
                logger.info("ℹ️ No expired links to clean up")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired links: {e}")
            return 0
    
    async def cleanup_old_sessions(self, days_old=30):
        """Remove old inactive sessions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            async with self.db_pool.acquire() as conn:
                deleted_count = await conn.fetchval('''
                    DELETE FROM sessions 
                    WHERE is_active = false AND created_at < $1
                    RETURNING COUNT(*)
                ''', cutoff_date)
                
                if deleted_count > 0:
                    await conn.execute('''
                        INSERT INTO logs (event_type, payload)
                        VALUES ('cleanup_old_sessions', $1)
                    ''', json.dumps({"count": deleted_count, "days_old": days_old}))
                    
                    logger.info(f"✅ Cleaned up {deleted_count} old inactive sessions")
                else:
                    logger.info("ℹ️ No old sessions to clean up")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old sessions: {e}")
            return 0
    
    async def cleanup_old_logs(self, days_old=7):
        """Remove old log entries"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            async with self.db_pool.acquire() as conn:
                deleted_count = await conn.fetchval('''
                    DELETE FROM logs 
                    WHERE timestamp < $1 AND event_type != 'blackout_triggered'
                    RETURNING COUNT(*)
                ''', cutoff_date)
                
                if deleted_count > 0:
                    logger.info(f"✅ Cleaned up {deleted_count} old log entries")
                else:
                    logger.info("ℹ️ No old logs to clean up")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old logs: {e}")
            return 0
    
    def cleanup_old_thumbnails_per_device(self, keep_count=10):
        """Keep only the most recent N thumbnails per device"""
        try:
            total_deleted = 0
            
            # Get all device folders
            device_folders = set()
            objects = self.minio_client.list_objects(MINIO_BUCKET, prefix="thumbnails/", recursive=True)
            
            for obj in objects:
                if not obj.object_name.endswith('.placeholder'):
                    # Extract device ID from path: thumbnails/{device_id}/filename
                    path_parts = obj.object_name.split('/')
                    if len(path_parts) >= 2:
                        device_folders.add(path_parts[1])
            
            # Cleanup each device's thumbnails
            for device_id in device_folders:
                deleted = self.cleanup_device_thumbnails(device_id, keep_count)
                total_deleted += deleted
            
            if total_deleted > 0:
                logger.info(f"✅ Cleaned up {total_deleted} old thumbnails across {len(device_folders)} devices")
            else:
                logger.info(f"ℹ️ No thumbnails to clean up for {len(device_folders)} devices")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup device thumbnails: {e}")
            return 0
    
    def cleanup_device_thumbnails(self, device_id: str, keep_count: int):
        """Keep only the most recent N thumbnails for a specific device"""
        try:
            prefix = f"thumbnails/{device_id}/"
            
            # List all thumbnails for this device
            objects = list(self.minio_client.list_objects(
                MINIO_BUCKET, 
                prefix=prefix,
                recursive=True
            ))
            
            # Filter out placeholder files and sort by last_modified (newest first)
            thumbnails = [obj for obj in objects if not obj.object_name.endswith('.placeholder')]
            thumbnails.sort(key=lambda obj: obj.last_modified, reverse=True)
            
            # Delete thumbnails beyond keep_count
            if len(thumbnails) > keep_count:
                thumbnails_to_delete = thumbnails[keep_count:]
                
                for thumbnail in thumbnails_to_delete:
                    self.minio_client.remove_object(MINIO_BUCKET, thumbnail.object_name)
                
                logger.info(f"✅ Cleaned up {len(thumbnails_to_delete)} old thumbnails for device {device_id}")
                return len(thumbnails_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup thumbnails for device {device_id}: {e}")
            return 0
    
    async def get_system_stats(self):
        """Get system cleanup statistics"""
        try:
            stats = {}
            
            async with self.db_pool.acquire() as conn:
                # Active links
                stats['active_links'] = await conn.fetchval('SELECT COUNT(*) FROM device_links WHERE expires_at > $1', datetime.utcnow())
                
                # Total devices
                stats['total_devices'] = await conn.fetchval('SELECT COUNT(*) FROM devices')
                
                # Active sessions
                stats['active_sessions'] = await conn.fetchval('SELECT COUNT(*) FROM sessions WHERE is_active = true')
                
                # Recent logs (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                stats['recent_logs'] = await conn.fetchval('SELECT COUNT(*) FROM logs WHERE timestamp > $1', yesterday)
            
            # MinIO statistics
            if self.minio_client:
                try:
                    thumbnail_objects = list(self.minio_client.list_objects(MINIO_BUCKET, prefix="thumbnails/", recursive=True))
                    stats['total_thumbnails'] = len([obj for obj in thumbnail_objects if not obj.object_name.endswith('.placeholder')])
                except:
                    stats['total_thumbnails'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get system stats: {e}")
            return {}
    
    async def run_full_cleanup(self):
        """Run complete cleanup process"""
        logger.info("🧹 Starting full system cleanup...")
        
        results = {
            'expired_links': 0,
            'old_sessions': 0,
            'old_logs': 0,
            'old_thumbnails': 0,
            'errors': 0
        }
        
        try:
            # Database cleanup
            results['expired_links'] = await self.cleanup_expired_links()
            results['old_sessions'] = await self.cleanup_old_sessions()
            results['old_logs'] = await self.cleanup_old_logs()
            
            # MinIO cleanup
            if self.minio_client:
                results['old_thumbnails'] = self.cleanup_old_thumbnails_per_device()
            
            # Get final stats
            stats = await self.get_system_stats()
            
            logger.info("✅ Cleanup completed successfully!")
            logger.info("📊 Cleanup Results:")
            logger.info(f"   Expired links removed: {results['expired_links']}")
            logger.info(f"   Old sessions removed: {results['old_sessions']}")
            logger.info(f"   Old logs removed: {results['old_logs']}")
            logger.info(f"   Old thumbnails removed: {results['old_thumbnails']}")
            
            logger.info("📊 Current System Stats:")
            logger.info(f"   Active links: {stats.get('active_links', 0)}")
            logger.info(f"   Total devices: {stats.get('total_devices', 0)}")
            logger.info(f"   Active sessions: {stats.get('active_sessions', 0)}")
            logger.info(f"   Total thumbnails: {stats.get('total_thumbnails', 0)}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            results['errors'] += 1
            return results
    
    async def close(self):
        """Close all connections"""
        if self.db_pool:
            await self.db_pool.close()

async def main():
    """Main cleanup function"""
    print("=" * 50)
    print("🧹 Rika System Cleanup - Phase 2")
    print("=" * 50)
    
    cleanup_manager = RikaCleanupManager()
    
    # Initialize connections
    if not await cleanup_manager.init_db():
        print("❌ Failed to connect to database. Exiting.")
        return False
    
    if not cleanup_manager.init_minio():
        print("⚠️ Failed to connect to MinIO. Skipping storage cleanup.")
    
    # Run cleanup
    try:
        results = await cleanup_manager.run_full_cleanup()
        
        # Check if any errors occurred
        if results['errors'] > 0:
            print(f"⚠️ Cleanup completed with {results['errors']} errors")
            return False
        
        print("✅ All cleanup operations completed successfully!")
        return True
        
    finally:
        await cleanup_manager.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)