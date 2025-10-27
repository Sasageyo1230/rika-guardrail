"""
Rika Phase 3.5 Knowledge Vault
Intelligent knowledge storage, retrieval, and caching system
"""
import os
import asyncio
import time
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timedelta
import aiofiles

logger = logging.getLogger(__name__)

class KnowledgeEntry(BaseModel):
    """Knowledge entry model"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    source: Optional[str] = None
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime
    ttl: Optional[int] = None  # Time to live in seconds
    metadata: Dict[str, Any] = {}

class KnowledgeQuery(BaseModel):
    """Knowledge query model"""
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    max_results: int = 10
    min_confidence: float = 0.0

class KnowledgeVaultConfig(BaseModel):
    """Knowledge vault configuration"""
    data_dir: str = "data/knowledge"
    cache_enabled: bool = True
    default_ttl: int = 86400  # 24 hours
    max_cache_size: int = 1000
    auto_cleanup: bool = True
    cleanup_interval: int = 3600  # 1 hour
    embedding_model: str = "sentence-transformers"

class KnowledgeVault:
    """Intelligent knowledge storage and retrieval system"""
    
    def __init__(self, config: KnowledgeVaultConfig):
        self.config = config
        self.cache: Dict[str, KnowledgeEntry] = {}
        self.last_cleanup = time.time()
        
        # Ensure data directory exists
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for knowledge entry"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: KnowledgeEntry) -> bool:
        """Check if knowledge entry has expired"""
        if not entry.ttl:
            return False
        age = (datetime.now() - entry.updated_at).total_seconds()
        return age > entry.ttl
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        if not self.config.auto_cleanup:
            return
            
        now = time.time()
        if now - self.last_cleanup < self.config.cleanup_interval:
            return
            
        expired_ids = []
        for entry_id, entry in self.cache.items():
            if self._is_expired(entry):
                expired_ids.append(entry_id)
        
        for entry_id in expired_ids:
            del self.cache[entry_id]
            logger.info(f"Cleaned up expired knowledge entry: {entry_id}")
        
        self.last_cleanup = now
    
    async def _load_from_disk(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Load knowledge entry from disk"""
        file_path = Path(self.config.data_dir) / f"{entry_id}.json"
        
        if not file_path.exists():
            return None
            
        try:
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
                return KnowledgeEntry(**data)
        except Exception as e:
            logger.error(f"Error loading knowledge entry {entry_id}: {e}")
            return None
    
    async def _save_to_disk(self, entry: KnowledgeEntry):
        """Save knowledge entry to disk"""
        file_path = Path(self.config.data_dir) / f"{entry.id}.json"
        
        try:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(entry.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error saving knowledge entry {entry.id}: {e}")
    
    async def store(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: List[str] = None,
        source: str = None,
        confidence: float = 1.0,
        ttl: int = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store knowledge entry"""
        entry_id = self._generate_id(f"{title}:{content}")
        
        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            source=source,
            confidence=confidence,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            ttl=ttl or self.config.default_ttl,
            metadata=metadata or {}
        )
        
        # Store in cache if enabled
        if self.config.cache_enabled:
            self.cache[entry_id] = entry
            
            # Cleanup if cache is too large
            if len(self.cache) > self.config.max_cache_size:
                # Remove oldest entries
                sorted_entries = sorted(
                    self.cache.items(),
                    key=lambda x: x[1].updated_at
                )
                for old_id, _ in sorted_entries[:len(self.cache) - self.config.max_cache_size]:
                    del self.cache[old_id]
        
        # Save to disk
        await self._save_to_disk(entry)
        
        logger.info(f"Stored knowledge entry: {entry_id} - {title}")
        return entry_id
    
    async def retrieve(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Retrieve knowledge entry by ID"""
        self._cleanup_expired()
        
        # Check cache first
        if self.config.cache_enabled and entry_id in self.cache:
            entry = self.cache[entry_id]
            if not self._is_expired(entry):
                return entry
            else:
                del self.cache[entry_id]
        
        # Load from disk
        entry = await self._load_from_disk(entry_id)
        if entry and not self._is_expired(entry):
            # Add to cache
            if self.config.cache_enabled:
                self.cache[entry_id] = entry
            return entry
        
        return None
    
    async def search(self, query: KnowledgeQuery) -> List[KnowledgeEntry]:
        """Search knowledge entries"""
        self._cleanup_expired()
        
        results = []
        
        # Search in cache
        for entry in self.cache.values():
            if self._matches_query(entry, query):
                results.append(entry)
        
        # Search on disk (basic implementation)
        data_dir = Path(self.config.data_dir)
        if data_dir.exists():
            for file_path in data_dir.glob("*.json"):
                entry_id = file_path.stem
                if entry_id not in self.cache:
                    entry = await self._load_from_disk(entry_id)
                    if entry and self._matches_query(entry, query):
                        results.append(entry)
                        # Add to cache
                        if self.config.cache_enabled:
                            self.cache[entry_id] = entry
        
        # Sort by confidence and limit results
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:query.max_results]
    
    def _matches_query(self, entry: KnowledgeEntry, query: KnowledgeQuery) -> bool:
        """Check if entry matches search query"""
        if self._is_expired(entry):
            return False
            
        if entry.confidence < query.min_confidence:
            return False
            
        if query.category and entry.category != query.category:
            return False
            
        if query.tags:
            if not any(tag in entry.tags for tag in query.tags):
                return False
        
        # Simple text search
        search_text = f"{entry.title} {entry.content}".lower()
        return query.query.lower() in search_text
    
    async def update(
        self,
        entry_id: str,
        title: str = None,
        content: str = None,
        category: str = None,
        tags: List[str] = None,
        confidence: float = None,
        ttl: int = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update existing knowledge entry"""
        entry = await self.retrieve(entry_id)
        if not entry:
            return False
        
        # Update fields
        if title is not None:
            entry.title = title
        if content is not None:
            entry.content = content
        if category is not None:
            entry.category = category
        if tags is not None:
            entry.tags = tags
        if confidence is not None:
            entry.confidence = confidence
        if ttl is not None:
            entry.ttl = ttl
        if metadata is not None:
            entry.metadata.update(metadata)
        
        entry.updated_at = datetime.now()
        
        # Update cache
        if self.config.cache_enabled:
            self.cache[entry_id] = entry
        
        # Save to disk
        await self._save_to_disk(entry)
        
        logger.info(f"Updated knowledge entry: {entry_id}")
        return True
    
    async def delete(self, entry_id: str) -> bool:
        """Delete knowledge entry"""
        # Remove from cache
        if entry_id in self.cache:
            del self.cache[entry_id]
        
        # Remove from disk
        file_path = Path(self.config.data_dir) / f"{entry_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted knowledge entry: {entry_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting knowledge entry {entry_id}: {e}")
                return False
        
        return False
    
    async def get_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set()
        
        # From cache
        for entry in self.cache.values():
            if not self._is_expired(entry):
                categories.add(entry.category)
        
        # From disk
        data_dir = Path(self.config.data_dir)
        if data_dir.exists():
            for file_path in data_dir.glob("*.json"):
                entry_id = file_path.stem
                if entry_id not in self.cache:
                    entry = await self._load_from_disk(entry_id)
                    if entry and not self._is_expired(entry):
                        categories.add(entry.category)
        
        return sorted(list(categories))
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge vault statistics"""
        self._cleanup_expired()
        
        total_entries = len(self.cache)
        
        # Count disk entries
        data_dir = Path(self.config.data_dir)
        disk_entries = len(list(data_dir.glob("*.json"))) if data_dir.exists() else 0
        
        categories = await self.get_categories()
        
        return {
            "total_entries": max(total_entries, disk_entries),
            "cached_entries": total_entries,
            "disk_entries": disk_entries,
            "categories": len(categories),
            "cache_enabled": self.config.cache_enabled,
            "auto_cleanup": self.config.auto_cleanup,
            "last_cleanup": self.last_cleanup
        }

def create_knowledge_vault() -> KnowledgeVault:
    """Create knowledge vault with configuration from environment"""
    config = KnowledgeVaultConfig(
        data_dir=os.getenv("KNOWLEDGE_VAULT_DIR", "data/knowledge"),
        cache_enabled=os.getenv("KNOWLEDGE_CACHE_ENABLED", "true").lower() == "true",
        default_ttl=int(os.getenv("KNOWLEDGE_DEFAULT_TTL", "86400")),
        max_cache_size=int(os.getenv("KNOWLEDGE_MAX_CACHE_SIZE", "1000"))
    )
    return KnowledgeVault(config)

# Global knowledge vault instance
knowledge_vault = create_knowledge_vault()