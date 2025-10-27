"""
Rika Phase 3.4 Tool System
"""
import asyncio
from typing import Dict, Any, List, Optional
from .datetime import datetime, timezone
import httpx
from .config import RikaConfig
from n8n_client import N8NTools, get_n8n_client

class WebSearchTool:
    """Simple web search tool stub"""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Perform web search (stub implementation)
        In production, this would integrate with a real search API
        """
        # For now, just log the query and return a mock result
        print(f"[WebSearch] Query: {query}")
        
        return {
            "query": query,
            "results": [
                {
                    "title": f"Search result for: {query}",
                    "url": "https://example.com/search-result",
                    "snippet": f"This is a mock search result for the query '{query}'. In a real implementation, this would return actual search results from a search engine API."
                }
            ],
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class DeviceControlTool:
    """Device control tool stub for future Echo integration"""
    
    async def control(self, action: str, target: str) -> Dict[str, Any]:
        """
        Control device action (stub implementation)
        In production, this would integrate with Echo system
        """
        print(f"[DeviceControl] Action: {action}, Target: {target}")
        
        return {
            "action": action,
            "target": target,
            "status": "planned",
            "message": f"Device control planned: {action} on {target}. This will be executed when Echo integration is complete.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class ToolRegistry:
    """Registry for all available tools"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
        self.n8n_tools = N8NTools(get_n8n_client(config))
        self.web_search = WebSearchTool()
        self.device_control = DeviceControlTool()
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with arguments"""
        
        if tool_name == "n8n_run_workflow":
            return await self.n8n_tools.run(
                workflow_id=kwargs.get("workflow_id"),
                input_data=kwargs.get("input_data", {})
            )
        
        elif tool_name == "n8n_check_status":
            return await self.n8n_tools.status(
                task_id=kwargs.get("task_id")
            )
        
        elif tool_name == "n8n_list_workflows":
            return await self.n8n_tools.list_available()
        
        elif tool_name == "web_search":
            return await self.web_search.search(
                query=kwargs.get("query", "")
            )
        
        elif tool_name == "device_control":
            return await self.device_control.control(
                action=kwargs.get("action", ""),
                target=kwargs.get("target", "")
            )
        
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.get_tool_definitions().keys())
            }
    
    def get_tool_definitions(self) -> Dict[str, Dict]:
        """Get all tool definitions for LLM function calling"""
        return {
            "n8n_run_workflow": {
                "description": "Execute an n8n workflow with input data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "The ID of the n8n workflow to execute"},
                        "input_data": {"type": "object", "description": "Input data to pass to the workflow"}
                    },
                    "required": ["workflow_id", "input_data"]
                }
            },
            "n8n_check_status": {
                "description": "Check the status of a workflow execution",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "The task ID returned from workflow execution"}
                    },
                    "required": ["task_id"]
                }
            },
            "n8n_list_workflows": {
                "description": "List available n8n workflows",
                "parameters": {"type": "object", "properties": {}}
            },
            "web_search": {
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            "device_control": {
                "description": "Control smart devices (lights, temperature, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Action to perform (turn_on, turn_off, set_brightness, etc.)"},
                        "target": {"type": "string", "description": "Target device or room"}
                    },
                    "required": ["action", "target"]
                }
            }
        }

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.now(timezone.utc)
    
    async def check_rate_limit(self, session_id: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now(timezone.utc)
        
        # Clean up old requests periodically
        if (now - self.last_cleanup).total_seconds() > self.cleanup_interval:
            await self._cleanup_old_requests()
            self.last_cleanup = now
        
        # Get existing requests for this session
        if session_id not in self.requests:
            self.requests[session_id] = []
        
        session_requests = self.requests[session_id]
        
        # Remove requests older than 1 minute
        cutoff_time = now.timestamp() - 60
        session_requests = [req for req in session_requests if req.timestamp() > cutoff_time]
        self.requests[session_id] = session_requests
        
        # Check if under limit
        if len(session_requests) >= self.max_requests:
            return False
        
        # Add current request
        session_requests.append(now)
        return True
    
    async def _cleanup_old_requests(self):
        """Remove old request records to prevent memory leaks"""
        now = datetime.now(timezone.utc)
        cutoff_time = now.timestamp() - 3600  # 1 hour
        
        sessions_to_remove = []
        for session_id, requests in self.requests.items():
            # Filter out old requests
            recent_requests = [req for req in requests if req.timestamp() > cutoff_time]
            
            if not recent_requests:
                sessions_to_remove.append(session_id)
            else:
                self.requests[session_id] = recent_requests
        
        # Remove sessions with no recent requests
        for session_id in sessions_to_remove:
            del self.requests[session_id]

# Global instances
_tool_registry: Optional[ToolRegistry] = None
_rate_limiter: Optional[RateLimiter] = None

def get_tool_registry(config: RikaConfig) -> ToolRegistry:
    """Get or create the global tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry(config)
    return _tool_registry

def get_rate_limiter(config: RikaConfig) -> RateLimiter:
    """Get or create the global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(config.rate_limit_per_minute)
    return _rate_limiter