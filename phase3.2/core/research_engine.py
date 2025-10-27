# phase3.2/core/research_engine.py
# Scout Research Engine with MinIO + Qdrant storage

import asyncio
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import re

# Core imports
import httpx
import asyncpg
from minio import Minio
from minio.error import S3Error
from qdrant_client import QdrantClient
from qdrant_client.http import models
import structlog
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer

# Local imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'subagents', 'sdk'))
from n8n_client import ScoutAgentN8nClient

logger = structlog.get_logger()

class ResearchConfig:
    """Configuration for research operations"""
    
    def __init__(self):
        # Storage configuration
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket = "rika-research"
        
        # Qdrant configuration  
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_collection = "research_vectors"
        
        # Research parameters
        self.quick_mode_pages = 5
        self.deep_mode_pages = 15
        self.max_content_length = 10000
        self.similarity_threshold = 0.75
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.max_concurrent_requests = 3

class ResearchSource:
    """Individual research source/document"""
    
    def __init__(self, url: str, title: str = "", content: str = "", 
                 source_type: str = "web", metadata: Dict = None):
        self.id = str(uuid.uuid4())
        self.url = url
        self.title = title
        self.content = content
        self.source_type = source_type  # web, pdf, api, file
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.hash = self._generate_hash()
        
    def _generate_hash(self) -> str:
        """Generate content hash for deduplication"""
        content_str = f"{self.url}{self.title}{self.content}"
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "source_type": self.source_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "hash": self.hash
        }

class WebScraper:
    """Web scraping functionality"""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Rika Research Bot 1.0"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def scrape_url(self, url: str) -> Optional[ResearchSource]:
        """Scrape content from a URL"""
        try:
            logger.info(f"Scraping URL: {url}")
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
            
            # Extract main content
            content_selectors = [
                'article', 'main', '.content', '#content', 
                '.post-content', '.entry-content', '.article-body'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                content_element = soup.find('body')
            
            # Extract text content
            content = content_element.get_text() if content_element else ""
            
            # Clean and limit content
            content = self._clean_content(content)
            
            # Extract metadata
            metadata = {
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(content),
                "status_code": response.status_code,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            # Extract meta tags
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                metadata["description"] = meta_description.get('content', '')
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                metadata["keywords"] = meta_keywords.get('content', '')
            
            return ResearchSource(
                url=url,
                title=title,
                content=content,
                source_type="web",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep basic punctuation
        content = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', content)
        
        # Limit length
        if len(content) > self.config.max_content_length:
            content = content[:self.config.max_content_length] + "..."
        
        return content.strip()

class VectorStore:
    """Qdrant vector storage for semantic search"""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = config.qdrant_collection
        
    async def initialize(self):
        """Initialize vector collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def store_source(self, source: ResearchSource):
        """Store research source as vector"""
        try:
            # Generate embedding
            text_to_embed = f"{source.title} {source.content}"
            embedding = self.encoder.encode(text_to_embed).tolist()
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=source.id,
                        vector=embedding,
                        payload={
                            "url": source.url,
                            "title": source.title,
                            "source_type": source.source_type,
                            "timestamp": source.timestamp.isoformat(),
                            "hash": source.hash,
                            "content_preview": source.content[:200] + "..." if len(source.content) > 200 else source.content
                        }
                    )
                ]
            )
            
            logger.info(f"Stored vector for: {source.title}")
            
        except Exception as e:
            logger.error(f"Failed to store vector: {e}")
    
    async def search_similar(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Search for similar content"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold
            )
            
            # Format results
            similar_sources = []
            for result in results:
                similar_sources.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            return similar_sources
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

class ObjectStorage:
    """MinIO object storage for research artifacts"""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.client = Minio(
            config.minio_endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=False  # Use HTTPS in production
        )
        self.bucket_name = config.minio_bucket
        
    async def initialize(self):
        """Initialize storage bucket"""
        try:
            # Check if bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                logger.info(f"Using existing MinIO bucket: {self.bucket_name}")
                
        except S3Error as e:
            logger.error(f"Failed to initialize object storage: {e}")
            raise
    
    async def store_source(self, source: ResearchSource) -> str:
        """Store research source as object"""
        try:
            # Generate object key
            timestamp = source.timestamp.strftime("%Y/%m/%d")
            object_key = f"{timestamp}/sources/{source.id}.json"
            
            # Convert to JSON
            source_data = json.dumps(source.to_dict(), indent=2)
            source_bytes = source_data.encode('utf-8')
            
            # Store in MinIO
            self.client.put_object(
                self.bucket_name,
                object_key,
                data=source_bytes,
                length=len(source_bytes),
                content_type="application/json"
            )
            
            logger.info(f"Stored object: {object_key}")
            return object_key
            
        except S3Error as e:
            logger.error(f"Failed to store object: {e}")
            return ""
    
    async def get_source(self, object_key: str) -> Optional[ResearchSource]:
        """Retrieve research source from storage"""
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            data = json.loads(response.read().decode('utf-8'))
            
            # Reconstruct ResearchSource
            source = ResearchSource(
                url=data["url"],
                title=data["title"],
                content=data["content"],
                source_type=data["source_type"],
                metadata=data["metadata"]
            )
            source.id = data["id"]
            source.hash = data["hash"]
            source.timestamp = datetime.fromisoformat(data["timestamp"])
            
            return source
            
        except S3Error as e:
            logger.error(f"Failed to retrieve object {object_key}: {e}")
            return None
    
    async def store_research_report(self, research_id: str, report: Dict) -> str:
        """Store research report"""
        try:
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            object_key = f"{timestamp}/reports/{research_id}.json"
            
            report_data = json.dumps(report, indent=2)
            report_bytes = report_data.encode('utf-8')
            
            self.client.put_object(
                self.bucket_name,
                object_key,
                data=report_bytes,
                length=len(report_bytes),
                content_type="application/json"
            )
            
            return object_key
            
        except S3Error as e:
            logger.error(f"Failed to store report: {e}")
            return ""

class ResearchEngine:
    """Main research engine with quick and deep modes"""
    
    def __init__(self, config: ResearchConfig = None):
        self.config = config or ResearchConfig()
        self.vector_store = VectorStore(self.config)
        self.object_storage = ObjectStorage(self.config)
        self.n8n_client = ScoutAgentN8nClient()
        
        # Research cache
        self.source_cache = {}
        self.query_cache = {}
        
    async def initialize(self):
        """Initialize research engine"""
        logger.info("Initializing research engine...")
        
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Initialize storage backends
        await self.vector_store.initialize()
        await self.object_storage.initialize()
        
        logger.info("Research engine initialized")
    
    async def research_quick(self, query: str, sources: List[str] = None) -> Dict:
        """Quick research mode - faster, fewer sources"""
        return await self._research(
            query=query,
            mode="quick",
            max_pages=self.config.quick_mode_pages,
            sources=sources or self._get_default_sources()
        )
    
    async def research_deep(self, query: str, sources: List[str] = None) -> Dict:
        """Deep research mode - comprehensive, more sources"""
        return await self._research(
            query=query,
            mode="deep", 
            max_pages=self.config.deep_mode_pages,
            sources=sources or self._get_default_sources()
        )
    
    async def _research(self, query: str, mode: str, max_pages: int, sources: List[str]) -> Dict:
        """Core research logic"""
        research_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting {mode} research: {query}")
        
        # Check cache first
        cache_key = hashlib.sha256(f"{query}_{mode}".encode()).hexdigest()
        if cache_key in self.query_cache:
            cached_result = self.query_cache[cache_key]
            if (datetime.utcnow() - cached_result["timestamp"]).seconds < 3600:  # 1 hour cache
                logger.info("Returning cached research result")
                return cached_result["result"]
        
        # Search existing knowledge first
        existing_sources = await self.vector_store.search_similar(
            query, 
            limit=5, 
            threshold=self.config.similarity_threshold
        )
        
        # Generate search URLs
        search_urls = self._generate_search_urls(query, sources, max_pages)
        
        # Scrape new sources
        scraped_sources = []
        async with WebScraper(self.config) as scraper:
            semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
            
            async def scrape_with_limit(url):
                async with semaphore:
                    await asyncio.sleep(self.config.request_delay)
                    return await scraper.scrape_url(url)
            
            tasks = [scrape_with_limit(url) for url in search_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, ResearchSource):
                    scraped_sources.append(result)
        
        # Deduplicate sources
        unique_sources = self._deduplicate_sources(scraped_sources)
        
        # Store new sources
        for source in unique_sources:
            await self.vector_store.store_source(source)
            await self.object_storage.store_source(source)
        
        # Generate research report
        report = await self._generate_report(
            research_id=research_id,
            query=query,
            mode=mode,
            existing_sources=existing_sources,
            new_sources=unique_sources,
            start_time=start_time
        )
        
        # Store report
        await self.object_storage.store_research_report(research_id, report)
        
        # Cache result
        self.query_cache[cache_key] = {
            "result": report,
            "timestamp": datetime.utcnow()
        }
        
        # Send notification
        await self.n8n_client.send_notification(
            f"{mode.title()} research completed: {query}",
            channels=["research"],
            urgency="normal"
        )
        
        return report
    
    def _get_default_sources(self) -> List[str]:
        """Get default search sources"""
        return [
            "https://duckduckgo.com/?q={query}",
            "https://www.google.com/search?q={query}",
            "https://search.brave.com/search?q={query}",
            "https://www.bing.com/search?q={query}"
        ]
    
    def _generate_search_urls(self, query: str, sources: List[str], max_pages: int) -> List[str]:
        """Generate search URLs from query and sources"""
        urls = []
        encoded_query = query.replace(" ", "+")
        
        for source_template in sources:
            if "{query}" in source_template:
                base_url = source_template.format(query=encoded_query)
                urls.append(base_url)
                
                # Add pagination for deep research
                if max_pages > 5:
                    for page in range(2, min(max_pages // len(sources) + 1, 6)):
                        if "google.com" in base_url:
                            urls.append(f"{base_url}&start={page * 10}")
                        elif "bing.com" in base_url:
                            urls.append(f"{base_url}&first={page * 10}")
        
        return urls[:max_pages]
    
    def _deduplicate_sources(self, sources: List[ResearchSource]) -> List[ResearchSource]:
        """Remove duplicate sources based on content hash"""
        seen_hashes = set()
        unique_sources = []
        
        for source in sources:
            if source.hash not in seen_hashes:
                seen_hashes.add(source.hash)
                unique_sources.append(source)
        
        return unique_sources
    
    async def _generate_report(self, research_id: str, query: str, mode: str, 
                             existing_sources: List[Dict], new_sources: List[ResearchSource],
                             start_time: datetime) -> Dict:
        """Generate comprehensive research report"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze content
        all_content = []
        for source in new_sources:
            all_content.append(source.content)
        
        # Extract key insights
        insights = self._extract_insights(query, all_content)
        
        # Generate summary
        summary = self._generate_summary(query, insights, all_content)
        
        report = {
            "research_id": research_id,
            "query": query,
            "mode": mode,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "summary": summary,
            "insights": insights,
            "statistics": {
                "existing_sources_found": len(existing_sources),
                "new_sources_scraped": len(new_sources),
                "total_content_length": sum(len(s.content) for s in new_sources),
                "unique_domains": len(set(s.url.split('/')[2] for s in new_sources if '/' in s.url))
            },
            "sources": {
                "existing": existing_sources,
                "new": [s.to_dict() for s in new_sources]
            },
            "metadata": {
                "confidence_score": self._calculate_confidence(existing_sources, new_sources),
                "completeness_score": min(len(new_sources) / (5 if mode == "quick" else 10), 1.0),
                "relevance_scores": [s.get("score", 0) for s in existing_sources]
            }
        }
        
        return report
    
    def _extract_insights(self, query: str, content_list: List[str]) -> List[str]:
        """Extract key insights from content"""
        insights = []
        query_keywords = set(word_tokenize(query.lower()))
        
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set()
        
        for content in content_list:
            sentences = sent_tokenize(content)
            for sentence in sentences:
                sentence_words = set(word_tokenize(sentence.lower()))
                
                # Check if sentence is relevant to query
                relevance = len(query_keywords.intersection(sentence_words - stop_words))
                if relevance >= 2 and len(sentence) > 50:
                    insights.append(sentence.strip())
        
        # Remove duplicates and sort by length (longer = more detailed)
        unique_insights = list(set(insights))
        unique_insights.sort(key=len, reverse=True)
        
        return unique_insights[:10]  # Top 10 insights
    
    def _generate_summary(self, query: str, insights: List[str], content_list: List[str]) -> str:
        """Generate research summary"""
        if not insights:
            return f"Research on '{query}' yielded limited insights. Consider refining the search query or expanding source coverage."
        
        summary_parts = [
            f"Research Summary for: {query}",
            "",
            f"Based on analysis of {len(content_list)} sources, the key findings are:",
            ""
        ]
        
        # Add top insights
        for i, insight in enumerate(insights[:5], 1):
            summary_parts.append(f"{i}. {insight}")
        
        if len(insights) > 5:
            summary_parts.append(f"\nAdditional insights available ({len(insights) - 5} more findings).")
        
        return "\n".join(summary_parts)
    
    def _calculate_confidence(self, existing_sources: List[Dict], new_sources: List[ResearchSource]) -> float:
        """Calculate confidence score for research results"""
        # Base confidence on source diversity and quantity
        total_sources = len(existing_sources) + len(new_sources)
        
        if total_sources == 0:
            return 0.0
        
        # Domain diversity bonus
        if new_sources:
            unique_domains = len(set(s.url.split('/')[2] for s in new_sources if '/' in s.url))
            domain_diversity = min(unique_domains / 5, 1.0)
        else:
            domain_diversity = 0.0
        
        # Existing knowledge bonus
        existing_bonus = min(len(existing_sources) / 3, 0.3)
        
        # Content quality bonus
        avg_content_length = np.mean([len(s.content) for s in new_sources]) if new_sources else 0
        content_quality = min(avg_content_length / 1000, 0.3)
        
        confidence = min(
            (total_sources / 10) * 0.4 +  # Quantity
            domain_diversity * 0.3 +       # Diversity  
            existing_bonus +               # Prior knowledge
            content_quality,               # Content quality
            1.0
        )
        
        return round(confidence, 2)

# Daily digest functionality
class ResearchDigest:
    """Generate daily research digests"""
    
    def __init__(self, research_engine: ResearchEngine):
        self.engine = research_engine
        
    async def generate_daily_digest(self, date: datetime = None) -> Dict:
        """Generate daily research digest"""
        if date is None:
            date = datetime.utcnow()
        
        # Query research from the day
        # This would integrate with your research history storage
        # For now, return a template
        
        digest = {
            "date": date.strftime("%Y-%m-%d"),
            "summary": "Daily research activity summary",
            "total_queries": 0,
            "top_topics": [],
            "insights": [],
            "trending_keywords": [],
            "recommendations": []
        }
        
        return digest

# FastAPI integration
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Research Engine", version="3.2.0")

# Global engine instance
engine = None

class ResearchRequest(BaseModel):
    query: str
    mode: str = "quick"  # quick or deep
    sources: Optional[List[str]] = None

@app.on_event("startup")
async def startup():
    global engine
    engine = ResearchEngine()
    await engine.initialize()

@app.post("/research")
async def research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Perform research query"""
    if not engine:
        raise HTTPException(500, "Engine not initialized")
    
    if request.mode == "quick":
        result = await engine.research_quick(request.query, request.sources)
    elif request.mode == "deep":
        result = await engine.research_deep(request.query, request.sources)
    else:
        raise HTTPException(400, "Mode must be 'quick' or 'deep'")
    
    return result

@app.get("/research/{research_id}")
async def get_research(research_id: str):
    """Get research by ID"""
    if not engine:
        raise HTTPException(500, "Engine not initialized")
    
    # This would retrieve from storage
    raise HTTPException(404, "Research not found")

@app.get("/digest/daily")
async def daily_digest(date: Optional[str] = None):
    """Get daily research digest"""
    if not engine:
        raise HTTPException(500, "Engine not initialized")
    
    digest_gen = ResearchDigest(engine)
    
    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(400, "Invalid date format")
    else:
        date_obj = datetime.utcnow()
    
    digest = await digest_gen.generate_daily_digest(date_obj)
    return digest

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "research-engine",
        "version": "3.2.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5326)