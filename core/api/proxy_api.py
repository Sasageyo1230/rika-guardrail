"""
Privacy Proxy API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
import logging

from ..proxy import privacy_proxy, ProxyResponse

logger = logging.getLogger(__name__)

proxy_router = APIRouter(prefix="/proxy", tags=["proxy"])

class FetchRequest(BaseModel):
    url: HttpUrl
    headers: Optional[Dict[str, str]] = None

class SearchRequest(BaseModel):
    query: str
    count: Optional[int] = 10
    offset: Optional[int] = 0

class ProxyHealthResponse(BaseModel):
    status: str
    features: Dict[str, bool]
    cache_stats: Optional[Dict[str, Any]] = None

@proxy_router.post("/fetch", response_model=ProxyResponse)
async def fetch_url(request: FetchRequest):
    """Fetch URL with privacy protection and metadata stripping"""
    try:
        result = await privacy_proxy.fetch_url(str(request.url), request.headers)
        return result
    except Exception as e:
        logger.error(f"Proxy fetch error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.get("/fetch", response_model=ProxyResponse)
async def fetch_url_get(
    url: str = Query(..., description="URL to fetch"),
    strip_metadata: Optional[bool] = Query(True, description="Strip sensitive metadata")
):
    """Fetch URL with privacy protection (GET method)"""
    try:
        # Temporarily override strip_metadata setting if provided
        original_setting = privacy_proxy.config.strip_metadata
        if strip_metadata is not None:
            privacy_proxy.config.strip_metadata = strip_metadata
        
        result = await privacy_proxy.fetch_url(url)
        
        # Restore original setting
        privacy_proxy.config.strip_metadata = original_setting
        
        return result
    except Exception as e:
        logger.error(f"Proxy fetch error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.post("/search", response_model=ProxyResponse)
async def brave_search(request: SearchRequest):
    """Search using Brave Search API with privacy protection"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if request.count and (request.count < 1 or request.count > 20):
            raise HTTPException(status_code=400, detail="Count must be between 1 and 20")
        
        result = await privacy_proxy.brave_search(
            query=request.query,
            count=request.count or 10,
            offset=request.offset or 0
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Brave search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.get("/search", response_model=ProxyResponse)
async def brave_search_get(
    q: str = Query(..., description="Search query"),
    count: int = Query(10, ge=1, le=20, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Search using Brave Search API (GET method)"""
    try:
        result = await privacy_proxy.brave_search(query=q, count=count, offset=offset)
        return result
    except Exception as e:
        logger.error(f"Brave search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.delete("/cache")
async def clear_cache():
    """Clear proxy cache"""
    try:
        privacy_proxy.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.get("/cache/stats")
async def get_cache_stats():
    """Get proxy cache statistics"""
    try:
        stats = privacy_proxy.get_cache_stats()
        return {"cache_stats": stats}
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@proxy_router.get("/health", response_model=ProxyHealthResponse)
async def proxy_health():
    """Privacy proxy health check"""
    try:
        cache_stats = privacy_proxy.get_cache_stats()
        
        return ProxyHealthResponse(
            status="healthy",
            features={
                "url_fetch": True,
                "brave_search": privacy_proxy.config.brave_search_api_key is not None,
                "metadata_stripping": privacy_proxy.config.strip_metadata,
                "caching": privacy_proxy.config.cache_responses
            },
            cache_stats=cache_stats
        )
    except Exception as e:
        logger.error(f"Proxy health check error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")