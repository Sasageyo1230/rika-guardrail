"""
Rika Phase 3.5 Privacy-Preserving Brave Proxy
Strips metadata and provides enhanced privacy for web requests
"""
import os
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
from pydantic import BaseModel
import hashlib
import time
import json

logger = logging.getLogger(__name__)

class ProxyConfig(BaseModel):
    """Privacy proxy configuration"""
    brave_search_api_key: Optional[str] = None
    strip_metadata: bool = True
    cache_responses: bool = True
    cache_ttl: int = 3600  # 1 hour
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    max_redirects: int = 5
    timeout: int = 30
    strip_headers: List[str] = [
        "x-forwarded-for", "x-real-ip", "x-forwarded-proto",
        "x-request-id", "x-trace-id", "x-session-id",
        "authorization", "cookie", "set-cookie"
    ]

class ProxyResponse(BaseModel):
    """Proxy response model"""
    success: bool
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    cached: bool = False
    error: Optional[str] = None
    status_code: Optional[int] = None

class PrivacyProxy:
    """Privacy-preserving proxy service"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.brave_search_base = "https://api.search.brave.com/res/v1"
        
    def _generate_cache_key(self, url: str, headers: Dict[str, str] = None) -> str:
        """Generate cache key for request"""
        content = f"{url}:{json.dumps(headers or {}, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry.get("timestamp", 0) < self.config.cache_ttl
    
    def _strip_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers"""
        if not self.config.strip_metadata:
            return headers
            
        cleaned = {}
        for key, value in headers.items():
            if key.lower() not in [h.lower() for h in self.config.strip_headers]:
                cleaned[key] = value
                
        return cleaned
    
    def _prepare_request_headers(self, custom_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prepare privacy-focused headers"""
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if custom_headers:
            headers.update(self._strip_sensitive_headers(custom_headers))
            
        return headers
    
    async def fetch_url(self, url: str, headers: Dict[str, str] = None) -> ProxyResponse:
        """Fetch URL with privacy protection"""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return ProxyResponse(success=False, error="Invalid URL")
            
            # Check cache
            cache_key = self._generate_cache_key(url, headers)
            if self.config.cache_responses and cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    return ProxyResponse(
                        success=True,
                        content=cache_entry["content"],
                        metadata=cache_entry["metadata"],
                        cached=True,
                        status_code=cache_entry["status_code"]
                    )
            
            # Prepare request
            request_headers = self._prepare_request_headers(headers)
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                connector=aiohttp.TCPConnector(limit=10)
            ) as session:
                async with session.get(
                    url,
                    headers=request_headers,
                    max_redirects=self.config.max_redirects,
                    allow_redirects=True
                ) as response:
                    content = await response.text()
                    
                    # Extract minimal metadata
                    metadata = {
                        "url": str(response.url),
                        "status": response.status,
                        "content_type": response.headers.get("content-type", ""),
                        "content_length": len(content),
                        "timestamp": time.time()
                    }
                    
                    # Cache response if enabled
                    if self.config.cache_responses:
                        self.cache[cache_key] = {
                            "content": content,
                            "metadata": metadata,
                            "status_code": response.status,
                            "timestamp": time.time()
                        }
                    
                    return ProxyResponse(
                        success=True,
                        content=content,
                        metadata=metadata,
                        cached=False,
                        status_code=response.status
                    )
                    
        except asyncio.TimeoutError:
            return ProxyResponse(success=False, error="Request timeout")
        except Exception as e:
            logger.error(f"Proxy fetch error: {e}")
            return ProxyResponse(success=False, error=str(e))
    
    async def brave_search(self, query: str, count: int = 10, offset: int = 0) -> ProxyResponse:
        """Search using Brave Search API with privacy protection"""
        if not self.config.brave_search_api_key:
            return ProxyResponse(success=False, error="Brave Search API key not configured")
        
        try:
            url = f"{self.brave_search_base}/web/search"
            headers = {
                "X-Subscription-Token": self.config.brave_search_api_key,
                "Accept": "application/json"
            }
            
            params = {
                "q": query,
                "count": min(count, 20),  # Brave API limit
                "offset": offset,
                "safesearch": "moderate",
                "freshness": "pw",  # Past week for freshness
                "text_decorations": False,
                "spellcheck": True
            }
            
            # Check cache
            cache_key = self._generate_cache_key(f"{url}?{query}", headers)
            if self.config.cache_responses and cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    return ProxyResponse(
                        success=True,
                        content=cache_entry["content"],
                        metadata=cache_entry["metadata"],
                        cached=True,
                        status_code=200
                    )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        content = await response.text()
                        metadata = {
                            "query": query,
                            "count": count,
                            "offset": offset,
                            "timestamp": time.time(),
                            "source": "brave_search"
                        }
                        
                        # Cache results
                        if self.config.cache_responses:
                            self.cache[cache_key] = {
                                "content": content,
                                "metadata": metadata,
                                "status_code": 200,
                                "timestamp": time.time()
                            }
                        
                        return ProxyResponse(
                            success=True,
                            content=content,
                            metadata=metadata,
                            cached=False,
                            status_code=200
                        )
                    else:
                        error_text = await response.text()
                        return ProxyResponse(
                            success=False,
                            error=f"Brave Search API error {response.status}: {error_text}",
                            status_code=response.status
                        )
                        
        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return ProxyResponse(success=False, error=str(e))
    
    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_size_bytes": sum(len(entry["content"]) for entry in self.cache.values())
        }

def create_privacy_proxy() -> PrivacyProxy:
    """Create privacy proxy with configuration from environment"""
    config = ProxyConfig(
        brave_search_api_key=os.getenv("BRAVE_SEARCH_API_KEY"),
        strip_metadata=os.getenv("PROXY_STRIP_METADATA", "true").lower() == "true",
        cache_responses=os.getenv("PROXY_CACHE_RESPONSES", "true").lower() == "true",
        cache_ttl=int(os.getenv("PROXY_CACHE_TTL", "3600"))
    )
    return PrivacyProxy(config)

# Global proxy instance
privacy_proxy = create_privacy_proxy()