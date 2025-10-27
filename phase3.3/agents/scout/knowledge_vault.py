"""
Scout Agent - Knowledge Vault System
Advanced knowledge management with semantic search and MinIO/Qdrant integration

Phase 3.3 Enhancement:
- Persistent knowledge storage with MinIO object storage
- Semantic search with Qdrant vector database
- Intelligent knowledge indexing and retrieval
- Daily/weekly digest generation
- Atlas integration for comprehensive knowledge access
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from collections import defaultdict, Counter

# Vector database and storage
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant client not available - semantic search will be limited")

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logging.warning("MinIO client not available - object storage will be limited")

try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers not available - will use simple embeddings")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """Individual knowledge item in the vault"""
    item_id: str
    title: str
    content: str
    content_type: str  # text, code, image, video, audio, document
    source: str  # URL, file path, or source identifier
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    importance: float = 0.5  # 0.0 to 1.0
    
    # Relationships
    related_items: List[str] = field(default_factory=list)  # Related item IDs
    references: List[str] = field(default_factory=list)  # External references
    
    # Processing metadata
    embedding_vector: Optional[List[float]] = None
    extracted_entities: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    language: str = "en"
    
    # Storage metadata
    storage_path: Optional[str] = None  # Path in MinIO
    checksum: Optional[str] = None
    file_size: Optional[int] = None

@dataclass
class SearchQuery:
    """Search query configuration"""
    query_text: str
    query_vector: Optional[List[float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Search parameters
    limit: int = 10
    score_threshold: float = 0.7
    include_categories: List[str] = field(default_factory=list)
    exclude_categories: List[str] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    
    # Advanced options
    semantic_weight: float = 0.7  # Weight for semantic vs keyword matching
    recency_boost: bool = True  # Boost recent items
    importance_boost: bool = True  # Boost important items

@dataclass
class SearchResult:
    """Search result with scoring"""
    item: KnowledgeItem
    score: float
    relevance_explanation: str
    highlight_snippets: List[str] = field(default_factory=list)

@dataclass
class KnowledgeDigest:
    """Daily/weekly knowledge digest"""
    digest_id: str
    digest_type: str  # daily, weekly, monthly
    period_start: datetime
    period_end: datetime
    
    # Content summary
    total_items: int
    new_items: List[str]  # Item IDs
    updated_items: List[str]
    trending_topics: List[Tuple[str, float]]  # (topic, score)
    most_accessed: List[str]  # Item IDs
    
    # Analytics
    category_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    
    # Generated content
    summary: str
    recommendations: List[str]  # Recommended items to explore
    insights: List[str]  # Key insights from the period
    
    created_at: datetime = field(default_factory=datetime.utcnow)

class EmbeddingManager:
    """Manages text embeddings for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.vector_dim = 384  # Default for all-MiniLM-L6-v2
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("SentenceTransformers not available, using dummy embeddings")
            return
        
        try:
            self.model = SentenceTransformer(self.model_name)
            # Update vector dimension based on model
            sample_embedding = self.model.encode(["test"])
            self.vector_dim = len(sample_embedding[0])
            logger.info(f"Loaded embedding model {self.model_name} with dimension {self.vector_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.model is None:
            # Return dummy embedding if model not available
            return [0.0] * self.vector_dim
        
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.vector_dim

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.model is None:
            return [[0.0] * self.vector_dim for _ in texts]
        
        try:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * self.vector_dim for _ in texts]

class VectorStore:
    """Qdrant vector database interface"""
    
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "rika_knowledge"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self.embedding_manager = EmbeddingManager()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Qdrant client"""
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant not available, using in-memory vector store")
            self.vectors = {}  # In-memory fallback
            return
        
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._ensure_collection_exists()
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
            self.vectors = {}  # Fallback to in-memory

    def _ensure_collection_exists(self):
        """Ensure the collection exists in Qdrant"""
        if not self.client:
            return
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_manager.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")

    async def store_item(self, item: KnowledgeItem) -> bool:
        """Store knowledge item in vector database"""
        try:
            # Generate embedding if not present
            if item.embedding_vector is None:
                content_for_embedding = f"{item.title} {item.content}"
                item.embedding_vector = self.embedding_manager.embed_text(content_for_embedding)
            
            if self.client:
                # Store in Qdrant
                point = PointStruct(
                    id=item.item_id,
                    vector=item.embedding_vector,
                    payload={
                        "title": item.title,
                        "content": item.content[:1000],  # Truncate for storage
                        "content_type": item.content_type,
                        "source": item.source,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat(),
                        "author": item.author,
                        "tags": item.tags,
                        "category": item.category,
                        "importance": item.importance,
                        "language": item.language
                    }
                )
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            else:
                # Store in memory fallback
                self.vectors[item.item_id] = {
                    "vector": item.embedding_vector,
                    "item": item
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store item {item.item_id}: {e}")
            return False

    async def search_similar(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar items using semantic search"""
        try:
            # Generate query embedding
            if query.query_vector is None:
                query.query_vector = self.embedding_manager.embed_text(query.query_text)
            
            if self.client:
                # Search with Qdrant
                results = await self._search_qdrant(query)
            else:
                # Search in memory fallback
                results = await self._search_memory(query)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def _search_qdrant(self, query: SearchQuery) -> List[SearchResult]:
        """Search using Qdrant vector database"""
        # Build filter conditions
        filter_conditions = []
        
        if query.include_categories:
            filter_conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=query.include_categories[0])  # Simplified for demo
                )
            )
        
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # Perform search
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query.query_vector,
            query_filter=query_filter,
            limit=query.limit,
            score_threshold=query.score_threshold
        )
        
        # Convert to SearchResult objects
        results = []
        for result in search_results:
            # Reconstruct KnowledgeItem from payload (simplified)
            payload = result.payload
            item = KnowledgeItem(
                item_id=str(result.id),
                title=payload["title"],
                content=payload["content"],
                content_type=payload["content_type"],
                source=payload["source"],
                created_at=datetime.fromisoformat(payload["created_at"]),
                updated_at=datetime.fromisoformat(payload["updated_at"]),
                author=payload.get("author"),
                tags=payload.get("tags", []),
                category=payload.get("category", "general"),
                importance=payload.get("importance", 0.5),
                language=payload.get("language", "en")
            )
            
            search_result = SearchResult(
                item=item,
                score=result.score,
                relevance_explanation=f"Semantic similarity: {result.score:.3f}",
                highlight_snippets=[payload["content"][:200] + "..."]
            )
            results.append(search_result)
        
        return results

    async def _search_memory(self, query: SearchQuery) -> List[SearchResult]:
        """Search using in-memory fallback"""
        results = []
        
        for item_id, data in self.vectors.items():
            vector = data["vector"]
            item = data["item"]
            
            # Calculate similarity
            similarity = self._cosine_similarity(query.query_vector, vector)
            
            if similarity >= query.score_threshold:
                # Apply filters
                if query.include_categories and item.category not in query.include_categories:
                    continue
                if query.exclude_categories and item.category in query.exclude_categories:
                    continue
                
                search_result = SearchResult(
                    item=item,
                    score=similarity,
                    relevance_explanation=f"Cosine similarity: {similarity:.3f}",
                    highlight_snippets=[item.content[:200] + "..."]
                )
                results.append(search_result)
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.limit]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0

class ObjectStore:
    """MinIO object storage interface"""
    
    def __init__(self, endpoint: str = "localhost:9000", access_key: str = "minioadmin", 
                 secret_key: str = "minioadmin", bucket_name: str = "rika-knowledge", secure: bool = False):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize MinIO client"""
        if not MINIO_AVAILABLE:
            logger.warning("MinIO not available, using local file storage")
            return
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            self._ensure_bucket_exists()
            logger.info(f"Connected to MinIO at {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            self.client = None

    def _ensure_bucket_exists(self):
        """Ensure the bucket exists"""
        if not self.client:
            return
        
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to create MinIO bucket: {e}")

    async def store_file(self, item_id: str, content: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
        """Store file content in object storage"""
        if not self.client:
            # Fallback to local file storage
            return await self._store_file_locally(item_id, content)
        
        try:
            object_name = f"items/{item_id}"
            
            # Calculate checksum
            checksum = hashlib.md5(content).hexdigest()
            
            # Store in MinIO
            from io import BytesIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(content),
                length=len(content),
                content_type=content_type,
                metadata={"checksum": checksum}
            )
            
            return object_name
            
        except Exception as e:
            logger.error(f"Failed to store file for item {item_id}: {e}")
            return None

    async def retrieve_file(self, storage_path: str) -> Optional[bytes]:
        """Retrieve file content from object storage"""
        if not self.client:
            return await self._retrieve_file_locally(storage_path)
        
        try:
            response = self.client.get_object(self.bucket_name, storage_path)
            content = response.read()
            response.close()
            response.release_conn()
            return content
            
        except Exception as e:
            logger.error(f"Failed to retrieve file {storage_path}: {e}")
            return None

    async def _store_file_locally(self, item_id: str, content: bytes) -> Optional[str]:
        """Fallback local file storage"""
        try:
            storage_dir = Path("data/knowledge_vault/files")
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = storage_dir / f"{item_id}.data"
            with open(file_path, "wb") as f:
                f.write(content)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to store file locally: {e}")
            return None

    async def _retrieve_file_locally(self, storage_path: str) -> Optional[bytes]:
        """Fallback local file retrieval"""
        try:
            with open(storage_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to retrieve local file: {e}")
            return None

class KnowledgeVault:
    """Main knowledge vault system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Initialize components
        self.vector_store = VectorStore(
            host=config.get("qdrant_host", "localhost"),
            port=config.get("qdrant_port", 6333),
            collection_name=config.get("collection_name", "rika_knowledge")
        )
        
        self.object_store = ObjectStore(
            endpoint=config.get("minio_endpoint", "localhost:9000"),
            access_key=config.get("minio_access_key", "minioadmin"),
            secret_key=config.get("minio_secret_key", "minioadmin"),
            bucket_name=config.get("bucket_name", "rika-knowledge"),
            secure=config.get("minio_secure", False)
        )
        
        # Local metadata storage
        self.metadata_store: Dict[str, KnowledgeItem] = {}
        self.digests: List[KnowledgeDigest] = []
        
        # Analytics tracking
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.search_history: List[Tuple[datetime, str]] = []
        
        # Load existing data
        asyncio.create_task(self._load_metadata())

    async def _load_metadata(self):
        """Load metadata from persistent storage"""
        try:
            metadata_file = Path("data/knowledge_vault/metadata.json")
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Reconstruct KnowledgeItem objects
                for item_data in data.get("items", []):
                    item = KnowledgeItem(**item_data)
                    # Convert datetime strings back to datetime objects
                    item.created_at = datetime.fromisoformat(item.created_at)
                    item.updated_at = datetime.fromisoformat(item.updated_at)
                    self.metadata_store[item.item_id] = item
                
                logger.info(f"Loaded {len(self.metadata_store)} items from metadata store")
                
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    async def _save_metadata(self):
        """Save metadata to persistent storage"""
        try:
            metadata_dir = Path("data/knowledge_vault")
            metadata_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            items_data = []
            for item in self.metadata_store.values():
                item_dict = asdict(item)
                # Convert datetime objects to strings
                item_dict["created_at"] = item.created_at.isoformat()
                item_dict["updated_at"] = item.updated_at.isoformat()
                items_data.append(item_dict)
            
            data = {
                "items": items_data,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            metadata_file = metadata_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    async def add_knowledge(
        self,
        title: str,
        content: str,
        content_type: str = "text",
        source: str = "manual_entry",
        author: Optional[str] = None,
        tags: List[str] = None,
        category: str = "general",
        importance: float = 0.5,
        file_content: Optional[bytes] = None
    ) -> Optional[str]:
        """Add new knowledge item to the vault"""
        
        # Generate unique ID
        item_id = self._generate_id()
        
        # Create knowledge item
        item = KnowledgeItem(
            item_id=item_id,
            title=title,
            content=content,
            content_type=content_type,
            source=source,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author=author,
            tags=tags or [],
            category=category,
            importance=importance
        )
        
        # Store file content if provided
        if file_content:
            storage_path = await self.object_store.store_file(item_id, file_content, content_type)
            if storage_path:
                item.storage_path = storage_path
                item.checksum = hashlib.md5(file_content).hexdigest()
                item.file_size = len(file_content)
        
        # Extract entities and generate summary
        await self._process_item(item)
        
        # Store in vector database
        success = await self.vector_store.store_item(item)
        
        if success:
            # Store metadata
            self.metadata_store[item_id] = item
            await self._save_metadata()
            
            logger.info(f"Added knowledge item: {title} ({item_id})")
            return item_id
        else:
            logger.error(f"Failed to add knowledge item: {title}")
            return None

    async def _process_item(self, item: KnowledgeItem):
        """Process knowledge item to extract entities and generate summary"""
        try:
            # Simple entity extraction (in real implementation, would use NLP)
            words = item.content.split()
            
            # Extract potential entities (capitalized words, emails, URLs)
            entities = []
            for word in words:
                word_clean = word.strip(".,!?()[]{}\"'")
                if len(word_clean) > 2:
                    if word_clean[0].isupper() or "@" in word_clean or "http" in word_clean.lower():
                        entities.append(word_clean)
            
            item.extracted_entities = list(set(entities))[:10]  # Limit to 10
            
            # Generate simple summary (first 200 chars or first sentence)
            sentences = item.content.split(". ")
            if len(sentences) > 0:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 200:
                    item.summary = first_sentence[:200] + "..."
                else:
                    item.summary = first_sentence
            
        except Exception as e:
            logger.error(f"Failed to process item {item.item_id}: {e}")

    async def search_knowledge(
        self,
        query_text: str,
        limit: int = 10,
        category: Optional[str] = None,
        importance_threshold: float = 0.0,
        recent_days: Optional[int] = None
    ) -> List[SearchResult]:
        """Search knowledge vault with semantic search"""
        
        # Build search query
        query = SearchQuery(
            query_text=query_text,
            limit=limit,
            score_threshold=0.3  # Lower threshold for more results
        )
        
        # Apply filters
        if category:
            query.include_categories = [category]
        
        if recent_days:
            cutoff_date = datetime.utcnow() - timedelta(days=recent_days)
            query.date_range = (cutoff_date, datetime.utcnow())
        
        # Track search
        self.search_history.append((datetime.utcnow(), query_text))
        
        # Perform search
        results = await self.vector_store.search_similar(query)
        
        # Apply additional filtering and ranking
        filtered_results = []
        for result in results:
            # Importance threshold
            if result.item.importance >= importance_threshold:
                # Boost score based on importance and recency
                boosted_score = result.score
                
                if query.importance_boost:
                    boosted_score += result.item.importance * 0.2
                
                if query.recency_boost:
                    days_old = (datetime.utcnow() - result.item.updated_at).days
                    recency_factor = max(0, 1.0 - (days_old / 365))  # Decay over year
                    boosted_score += recency_factor * 0.1
                
                result.score = min(1.0, boosted_score)
                filtered_results.append(result)
        
        # Sort by boosted score
        filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        # Track access
        for result in filtered_results:
            self.access_counts[result.item.item_id] += 1
        
        return filtered_results[:limit]

    async def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get specific knowledge item by ID"""
        item = self.metadata_store.get(item_id)
        if item:
            self.access_counts[item_id] += 1
        return item

    async def get_item_content(self, item_id: str) -> Optional[bytes]:
        """Get file content for knowledge item"""
        item = self.metadata_store.get(item_id)
        if not item or not item.storage_path:
            return None
        
        return await self.object_store.retrieve_file(item.storage_path)

    async def update_knowledge(
        self,
        item_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        importance: Optional[float] = None
    ) -> bool:
        """Update existing knowledge item"""
        
        item = self.metadata_store.get(item_id)
        if not item:
            return False
        
        # Update fields
        if title is not None:
            item.title = title
        if content is not None:
            item.content = content
        if tags is not None:
            item.tags = tags
        if category is not None:
            item.category = category
        if importance is not None:
            item.importance = importance
        
        item.updated_at = datetime.utcnow()
        
        # Reprocess the item
        await self._process_item(item)
        
        # Update in vector store
        success = await self.vector_store.store_item(item)
        
        if success:
            await self._save_metadata()
            logger.info(f"Updated knowledge item: {item_id}")
            return True
        else:
            logger.error(f"Failed to update knowledge item: {item_id}")
            return False

    async def delete_knowledge(self, item_id: str) -> bool:
        """Delete knowledge item from vault"""
        item = self.metadata_store.get(item_id)
        if not item:
            return False
        
        try:
            # Remove from vector store (implementation depends on Qdrant API)
            # For now, we'll just remove from metadata
            del self.metadata_store[item_id]
            
            # Remove from access tracking
            if item_id in self.access_counts:
                del self.access_counts[item_id]
            
            await self._save_metadata()
            logger.info(f"Deleted knowledge item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge item {item_id}: {e}")
            return False

    async def generate_digest(self, digest_type: str = "daily") -> KnowledgeDigest:
        """Generate knowledge digest for a period"""
        
        # Calculate period
        now = datetime.utcnow()
        if digest_type == "daily":
            period_start = now - timedelta(days=1)
        elif digest_type == "weekly":
            period_start = now - timedelta(weeks=1)
        elif digest_type == "monthly":
            period_start = now - timedelta(days=30)
        else:
            period_start = now - timedelta(days=1)
        
        # Collect items from period
        new_items = []
        updated_items = []
        
        for item in self.metadata_store.values():
            if item.created_at >= period_start:
                new_items.append(item.item_id)
            elif item.updated_at >= period_start and item.created_at < period_start:
                updated_items.append(item.item_id)
        
        # Analyze categories and sources
        category_dist = defaultdict(int)
        source_dist = defaultdict(int)
        language_dist = defaultdict(int)
        
        for item in self.metadata_store.values():
            if item.created_at >= period_start or item.updated_at >= period_start:
                category_dist[item.category] += 1
                source_dist[item.source] += 1
                language_dist[item.language] += 1
        
        # Find trending topics (simplified)
        all_tags = []
        for item in self.metadata_store.values():
            if item.created_at >= period_start or item.updated_at >= period_start:
                all_tags.extend(item.tags)
        
        tag_counts = Counter(all_tags)
        trending_topics = [(tag, count / len(all_tags)) for tag, count in tag_counts.most_common(5)]
        
        # Most accessed items
        period_access = {}
        for item_id, count in self.access_counts.items():
            item = self.metadata_store.get(item_id)
            if item and (item.created_at >= period_start or item.updated_at >= period_start):
                period_access[item_id] = count
        
        most_accessed = sorted(period_access.keys(), key=lambda x: period_access[x], reverse=True)[:5]
        
        # Generate summary and insights
        summary = self._generate_digest_summary(new_items, updated_items, trending_topics, digest_type)
        insights = self._generate_digest_insights(category_dist, trending_topics, period_start, now)
        recommendations = self._generate_recommendations(trending_topics, most_accessed)
        
        # Create digest
        digest = KnowledgeDigest(
            digest_id=self._generate_id("digest"),
            digest_type=digest_type,
            period_start=period_start,
            period_end=now,
            total_items=len(self.metadata_store),
            new_items=new_items,
            updated_items=updated_items,
            trending_topics=trending_topics,
            most_accessed=most_accessed,
            category_distribution=dict(category_dist),
            source_distribution=dict(source_dist),
            language_distribution=dict(language_dist),
            summary=summary,
            recommendations=recommendations,
            insights=insights
        )
        
        self.digests.append(digest)
        
        logger.info(f"Generated {digest_type} digest: {len(new_items)} new, {len(updated_items)} updated items")
        return digest

    def _generate_digest_summary(self, new_items: List[str], updated_items: List[str], 
                                trending_topics: List[Tuple[str, float]], digest_type: str) -> str:
        """Generate summary text for digest"""
        summary_parts = []
        
        summary_parts.append(f"Knowledge Vault {digest_type.capitalize()} Digest")
        summary_parts.append(f"Added {len(new_items)} new items and updated {len(updated_items)} existing items.")
        
        if trending_topics:
            top_topics = [topic for topic, _ in trending_topics[:3]]
            summary_parts.append(f"Trending topics: {', '.join(top_topics)}.")
        
        return " ".join(summary_parts)

    def _generate_digest_insights(self, category_dist: Dict[str, int], trending_topics: List[Tuple[str, float]],
                                period_start: datetime, period_end: datetime) -> List[str]:
        """Generate insights for digest"""
        insights = []
        
        if category_dist:
            top_category = max(category_dist.keys(), key=lambda x: category_dist[x])
            insights.append(f"Most active category: {top_category} ({category_dist[top_category]} items)")
        
        if trending_topics:
            top_topic, score = trending_topics[0]
            insights.append(f"Top trending topic: {top_topic} (appears in {score:.1%} of content)")
        
        total_days = (period_end - period_start).days
        if total_days > 0:
            daily_avg = sum(category_dist.values()) / total_days
            insights.append(f"Average daily knowledge additions: {daily_avg:.1f} items")
        
        return insights

    def _generate_recommendations(self, trending_topics: List[Tuple[str, float]], 
                                most_accessed: List[str]) -> List[str]:
        """Generate recommendations for digest"""
        recommendations = []
        
        if most_accessed:
            recommendations.append(f"Review highly accessed item: {most_accessed[0]}")
        
        if trending_topics:
            topic, _ = trending_topics[0]
            recommendations.append(f"Explore more content related to: {topic}")
        
        recommendations.append("Consider adding more diverse content sources")
        
        return recommendations

    def get_vault_statistics(self) -> Dict[str, Any]:
        """Get comprehensive vault statistics"""
        stats = {
            "total_items": len(self.metadata_store),
            "categories": {},
            "content_types": {},
            "sources": {},
            "languages": {},
            "importance_distribution": {"low": 0, "medium": 0, "high": 0},
            "recent_activity": {
                "last_24h": 0,
                "last_week": 0,
                "last_month": 0
            },
            "most_accessed": [],
            "search_activity": len(self.search_history),
            "total_file_size": 0
        }
        
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(weeks=1)
        one_month_ago = now - timedelta(days=30)
        
        for item in self.metadata_store.values():
            # Categories
            stats["categories"][item.category] = stats["categories"].get(item.category, 0) + 1
            
            # Content types
            stats["content_types"][item.content_type] = stats["content_types"].get(item.content_type, 0) + 1
            
            # Sources
            stats["sources"][item.source] = stats["sources"].get(item.source, 0) + 1
            
            # Languages
            stats["languages"][item.language] = stats["languages"].get(item.language, 0) + 1
            
            # Importance distribution
            if item.importance < 0.33:
                stats["importance_distribution"]["low"] += 1
            elif item.importance < 0.67:
                stats["importance_distribution"]["medium"] += 1
            else:
                stats["importance_distribution"]["high"] += 1
            
            # Recent activity
            if item.created_at >= one_day_ago or item.updated_at >= one_day_ago:
                stats["recent_activity"]["last_24h"] += 1
            if item.created_at >= one_week_ago or item.updated_at >= one_week_ago:
                stats["recent_activity"]["last_week"] += 1
            if item.created_at >= one_month_ago or item.updated_at >= one_month_ago:
                stats["recent_activity"]["last_month"] += 1
            
            # File sizes
            if item.file_size:
                stats["total_file_size"] += item.file_size
        
        # Most accessed items
        top_accessed = sorted(self.access_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        stats["most_accessed"] = [
            {"item_id": item_id, "title": self.metadata_store[item_id].title, "access_count": count}
            for item_id, count in top_accessed if item_id in self.metadata_store
        ]
        
        return stats

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID"""
        import uuid
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}" if prefix else f"{timestamp}_{unique_id}"

    async def export_vault(self, include_files: bool = False) -> Dict[str, Any]:
        """Export vault data for backup"""
        export_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_items": len(self.metadata_store),
                "include_files": include_files
            },
            "items": [],
            "digests": [asdict(digest) for digest in self.digests],
            "statistics": self.get_vault_statistics()
        }
        
        # Export items
        for item in self.metadata_store.values():
            item_data = asdict(item)
            # Convert datetime objects
            item_data["created_at"] = item.created_at.isoformat()
            item_data["updated_at"] = item.updated_at.isoformat()
            
            # Optionally include file content
            if include_files and item.storage_path:
                try:
                    file_content = await self.get_item_content(item.item_id)
                    if file_content:
                        import base64
                        item_data["file_content_base64"] = base64.b64encode(file_content).decode()
                except Exception as e:
                    logger.error(f"Failed to export file content for {item.item_id}: {e}")
            
            export_data["items"].append(item_data)
        
        return export_data

# Example usage and testing
async def main():
    """Example usage of the Knowledge Vault system"""
    
    # Initialize knowledge vault
    vault = KnowledgeVault()
    
    # Add some sample knowledge
    sample_items = [
        {
            "title": "Python Best Practices",
            "content": "Follow PEP 8 style guide for Python code. Use meaningful variable names, write docstrings for functions, and implement proper error handling with try-except blocks.",
            "category": "programming",
            "tags": ["python", "coding", "best-practices"],
            "importance": 0.8
        },
        {
            "title": "Machine Learning Fundamentals",
            "content": "Machine learning is a subset of AI that enables systems to automatically learn and improve from experience. Key concepts include supervised learning, unsupervised learning, and reinforcement learning.",
            "category": "ai-ml",
            "tags": ["machine-learning", "ai", "data-science"],
            "importance": 0.9
        },
        {
            "title": "Database Design Principles",
            "content": "Good database design follows normalization principles, ensures data integrity, and optimizes for query performance. Consider indexing strategies and relationship modeling.",
            "category": "database",
            "tags": ["database", "design", "sql"],
            "importance": 0.7
        }
    ]
    
    # Add items to vault
    item_ids = []
    for item_data in sample_items:
        item_id = await vault.add_knowledge(**item_data)
        if item_id:
            item_ids.append(item_id)
    
    print(f"Added {len(item_ids)} knowledge items")
    
    # Search for knowledge
    search_results = await vault.search_knowledge("python programming best practices", limit=5)
    
    print("\nSearch Results:")
    for result in search_results:
        print(f"- {result.item.title} (score: {result.score:.3f})")
        print(f"  {result.item.summary or result.item.content[:100]}...")
        print(f"  Tags: {result.item.tags}")
        print()
    
    # Generate daily digest
    digest = await vault.generate_digest("daily")
    
    print(f"Daily Digest:")
    print(f"Summary: {digest.summary}")
    print(f"New items: {len(digest.new_items)}")
    print(f"Trending topics: {digest.trending_topics}")
    print(f"Insights: {digest.insights}")
    
    # Get vault statistics
    stats = vault.get_vault_statistics()
    print(f"\nVault Statistics:")
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())