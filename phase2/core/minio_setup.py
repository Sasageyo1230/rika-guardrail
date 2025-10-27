# core/minio_setup.py
"""
MinIO Setup and Management for Rika Phase 2
Handles bucket creation, lifecycle policies, and cleanup operations
"""

import os
import asyncio
from datetime import datetime, timedelta
from minio import Minio
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "rikaadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "RikaMinIO2025SecureStorage")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "rika-screenshots")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RikaMinIOManager:
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
    def setup_bucket(self):
        """Create bucket and setup lifecycle policies"""
        try:
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(MINIO_BUCKET):
                self.client.make_bucket(MINIO_BUCKET)
                logger.info(f"✅ Created bucket: {MINIO_BUCKET}")
            else:
                logger.info(f"✅ Bucket already exists: {MINIO_BUCKET}")
            
            # Setup lifecycle policy for automatic cleanup
            self.setup_lifecycle_policy()
            
            # Create initial folder structure
            self.create_folder_structure()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup bucket: {e}")
            return False
    
    def setup_lifecycle_policy(self):
        """Setup automatic cleanup policies"""
        try:
            # Create lifecycle rules
            rules = []
            
            # Rule 1: Delete thumbnails older than 48 hours
            thumbnail_rule = Rule(
                rule_id="cleanup-thumbnails",
                rule_filter=Filter(prefix="thumbnails/"),
                status="Enabled",
                expiration=Expiration(days=2)  # 48 hours
            )
            rules.append(thumbnail_rule)
            
            # Rule 2: Keep only last 10 screenshots per device
            # Note: This is handled by application logic since MinIO doesn't support "keep last N" natively
            
            # Rule 3: Delete old gesture recordings (if we add them later)
            gesture_rule = Rule(
                rule_id="cleanup-gestures",
                rule_filter=Filter(prefix="gestures/"),
                status="Enabled",
                expiration=Expiration(days=7)  # 1 week
            )
            rules.append(gesture_rule)
            
            # Apply lifecycle configuration
            lifecycle_config = LifecycleConfig(rules)
            self.client.set_bucket_lifecycle(MINIO_BUCKET, lifecycle_config)
            
            logger.info("✅ Lifecycle policies configured:")
            logger.info("   - Thumbnails: 48 hour TTL")
            logger.info("   - Gestures: 7 day TTL")
            
        except Exception as e:
            logger.error(f"⚠️ Failed to setup lifecycle policy: {e}")
    
    def create_folder_structure(self):
        """Create initial folder structure"""
        try:
            folders = [
                "thumbnails/",
                "gestures/", 
                "recordings/",
                "backups/"
            ]
            
            for folder in folders:
                # MinIO creates folders implicitly when objects are uploaded
                # Create a placeholder file to ensure folder exists
                placeholder_content = f"Rika Phase 2 - {folder} directory created at {datetime.utcnow().isoformat()}"
                
                self.client.put_object(
                    MINIO_BUCKET,
                    f"{folder}.placeholder",
                    data=placeholder_content.encode(),
                    length=len(placeholder_content.encode()),
                    content_type="text/plain"
                )
            
            logger.info("✅ Created folder structure")
            
        except Exception as e:
            logger.error(f"⚠️ Failed to create folder structure: {e}")
    
    def cleanup_old_thumbnails(self, device_id: str, keep_count: int = 10):
        """Keep only the most recent N thumbnails for a device"""
        try:
            prefix = f"thumbnails/{device_id}/"
            
            # List all objects for this device
            objects = list(self.client.list_objects(
                MINIO_BUCKET, 
                prefix=prefix,
                recursive=True
            ))
            
            # Sort by last_modified (newest first)
            objects.sort(key=lambda obj: obj.last_modified, reverse=True)
            
            # Delete objects beyond keep_count
            if len(objects) > keep_count:
                objects_to_delete = objects[keep_count:]
                
                for obj in objects_to_delete:
                    self.client.remove_object(MINIO_BUCKET, obj.object_name)
                
                logger.info(f"✅ Cleaned up {len(objects_to_delete)} old thumbnails for device {device_id}")
                return len(objects_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup thumbnails for device {device_id}: {e}")
            return 0
    
    def get_storage_stats(self):
        """Get storage usage statistics"""
        try:
            stats = {
                "thumbnails": {"count": 0, "size": 0},
                "gestures": {"count": 0, "size": 0},
                "total": {"count": 0, "size": 0}
            }
            
            # Count thumbnails
            thumbnail_objects = list(self.client.list_objects(
                MINIO_BUCKET, 
                prefix="thumbnails/",
                recursive=True
            ))
            
            for obj in thumbnail_objects:
                if not obj.object_name.endswith('.placeholder'):
                    stats["thumbnails"]["count"] += 1
                    stats["thumbnails"]["size"] += obj.size
            
            # Count gestures
            gesture_objects = list(self.client.list_objects(
                MINIO_BUCKET,
                prefix="gestures/", 
                recursive=True
            ))
            
            for obj in gesture_objects:
                if not obj.object_name.endswith('.placeholder'):
                    stats["gestures"]["count"] += 1
                    stats["gestures"]["size"] += obj.size
            
            # Calculate totals
            stats["total"]["count"] = stats["thumbnails"]["count"] + stats["gestures"]["count"]
            stats["total"]["size"] = stats["thumbnails"]["size"] + stats["gestures"]["size"]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage stats: {e}")
            return None
    
    def test_upload_download(self):
        """Test MinIO connectivity with upload/download"""
        try:
            # Test data
            test_content = f"Rika MinIO test - {datetime.utcnow().isoformat()}"
            test_object = "test/connectivity-test.txt"
            
            # Upload test file
            self.client.put_object(
                MINIO_BUCKET,
                test_object,
                data=test_content.encode(),
                length=len(test_content.encode()),
                content_type="text/plain"
            )
            
            # Download test file
            response = self.client.get_object(MINIO_BUCKET, test_object)
            downloaded_content = response.read().decode()
            
            # Cleanup test file
            self.client.remove_object(MINIO_BUCKET, test_object)
            
            # Verify content matches
            if downloaded_content == test_content:
                logger.info("✅ MinIO connectivity test passed")
                return True
            else:
                logger.error("❌ MinIO connectivity test failed - content mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ MinIO connectivity test failed: {e}")
            return False

def main():
    """Main setup function"""
    print("=" * 50)
    print("🗄️ Rika MinIO Setup - Phase 2")
    print("=" * 50)
    
    manager = RikaMinIOManager()
    
    print("\\n1. Testing MinIO connectivity...")
    if not manager.test_upload_download():
        print("❌ MinIO connectivity test failed. Please check your MinIO server and credentials.")
        return False
    
    print("\\n2. Setting up bucket and policies...")
    if not manager.setup_bucket():
        print("❌ Bucket setup failed.")
        return False
    
    print("\\n3. Getting storage statistics...")
    stats = manager.get_storage_stats()
    if stats:
        print(f"   Thumbnails: {stats['thumbnails']['count']} files, {stats['thumbnails']['size']} bytes")
        print(f"   Gestures: {stats['gestures']['count']} files, {stats['gestures']['size']} bytes")
        print(f"   Total: {stats['total']['count']} files, {stats['total']['size']} bytes")
    
    print("\\n✅ MinIO setup completed successfully!")
    print("\\n📋 Configuration:")
    print(f"   Endpoint: {MINIO_ENDPOINT}")
    print(f"   Bucket: {MINIO_BUCKET}")
    print(f"   Lifecycle policies: Enabled")
    print(f"   Thumbnail TTL: 48 hours")
    print(f"   Per-device limit: 10 files")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)