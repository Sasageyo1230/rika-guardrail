"""
Knowledge Vault API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from ..knowledge_vault import knowledge_vault, KnowledgeEntry, KnowledgeQuery

logger = logging.getLogger(__name__)

knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])

class StoreRequest(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    confidence: float = 1.0
    ttl: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    confidence: Optional[float] = None
    ttl: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[KnowledgeEntry]
    total: int
    query: str

class StoreResponse(BaseModel):
    success: bool
    entry_id: Optional[str] = None
    message: Optional[str] = None

@knowledge_router.post("/store", response_model=StoreResponse)
async def store_knowledge(request: StoreRequest):
    """Store new knowledge entry"""
    try:
        entry_id = await knowledge_vault.store(
            title=request.title,
            content=request.content,
            category=request.category,
            tags=request.tags or [],
            source=request.source,
            confidence=request.confidence,
            ttl=request.ttl,
            metadata=request.metadata or {}
        )
        
        return StoreResponse(
            success=True,
            entry_id=entry_id,
            message="Knowledge stored successfully"
        )
        
    except Exception as e:
        logger.error(f"Error storing knowledge: {e}")
        return StoreResponse(
            success=False,
            message=f"Failed to store knowledge: {str(e)}"
        )

@knowledge_router.get("/retrieve/{entry_id}", response_model=Optional[KnowledgeEntry])
async def retrieve_knowledge(entry_id: str):
    """Retrieve knowledge entry by ID"""
    try:
        entry = await knowledge_vault.retrieve(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@knowledge_router.post("/search", response_model=SearchResponse)
async def search_knowledge(query: KnowledgeQuery):
    """Search knowledge entries"""
    try:
        results = await knowledge_vault.search(query)
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=query.query
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@knowledge_router.get("/search", response_model=SearchResponse)
async def search_knowledge_get(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    max_results: int = Query(10, ge=1, le=100, description="Maximum results"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence")
):
    """Search knowledge entries (GET method)"""
    try:
        tag_list = tags.split(",") if tags else None
        
        query = KnowledgeQuery(
            query=q,
            category=category,
            tags=tag_list,
            max_results=max_results,
            min_confidence=min_confidence
        )
        
        results = await knowledge_vault.search(query)
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=q
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@knowledge_router.put("/update/{entry_id}", response_model=StoreResponse)
async def update_knowledge(entry_id: str, request: UpdateRequest):
    """Update existing knowledge entry"""
    try:
        success = await knowledge_vault.update(
            entry_id=entry_id,
            title=request.title,
            content=request.content,
            category=request.category,
            tags=request.tags,
            confidence=request.confidence,
            ttl=request.ttl,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        return StoreResponse(
            success=True,
            entry_id=entry_id,
            message="Knowledge updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge: {e}")
        return StoreResponse(
            success=False,
            message=f"Failed to update knowledge: {str(e)}"
        )

@knowledge_router.delete("/delete/{entry_id}", response_model=StoreResponse)
async def delete_knowledge(entry_id: str):
    """Delete knowledge entry"""
    try:
        success = await knowledge_vault.delete(entry_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        return StoreResponse(
            success=True,
            entry_id=entry_id,
            message="Knowledge deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        return StoreResponse(
            success=False,
            message=f"Failed to delete knowledge: {str(e)}"
        )

@knowledge_router.get("/categories")
async def list_categories():
    """Get all available knowledge categories"""
    try:
        categories = await knowledge_vault.get_categories()
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@knowledge_router.get("/stats")
async def get_knowledge_stats():
    """Get knowledge vault statistics"""
    try:
        stats = await knowledge_vault.get_stats()
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@knowledge_router.get("/health")
async def knowledge_health():
    """Knowledge vault health check"""
    try:
        stats = await knowledge_vault.get_stats()
        
        return {
            "status": "healthy",
            "features": {
                "storage": True,
                "search": True,
                "caching": knowledge_vault.config.cache_enabled,
                "auto_cleanup": knowledge_vault.config.auto_cleanup
            },
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Knowledge health check error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")