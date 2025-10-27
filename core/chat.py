"""
Rika Phase 3.4 Chat System
Handles chat endpoints with streaming, memory, and tool integration
"""
import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .config import RikaConfig, config
from .llm_client import LLMMessage, get_llm_client
from .memory import get_memory_manager
from .tools import get_tool_registry, get_rate_limiter
from .agents import AgentType, get_agent_registry

# Request/Response Models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    agent: Optional[str] = None
    stream: bool = True
    guarded: Optional[bool] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: List[Dict[str, Any]] = []
    finished: bool = True

class SessionListResponse(BaseModel):
    sessions: List[str]

# Router for chat endpoints
chat_router = APIRouter(prefix="/chat", tags=["chat"])

# System prompts for different agents/personas
SYSTEM_PROMPTS = {
    "rika": """You are Rika, a helpful and knowledgeable AI assistant. You are part of a multi-agent system designed to assist with various tasks. 

Key capabilities:
- You can search the web for current information
- You can execute workflows through n8n integration
- You can control smart home devices (when connected)
- You maintain conversation context and memory

Be conversational, helpful, and proactive. When users ask for help with tasks that could benefit from tools, offer to use them. Always explain what tools you're planning to use before executing them.""",
    
    "rig": """You are Rig, a technical specialist focused on creative and engineering tasks. You excel at:
- 3D modeling and Blender integration
- CAD and design workflows  
- Technical problem solving
- Engineering calculations
- Creative project planning

You're direct, technically precise, and focused on practical solutions.""",
    
    "craft": """You are Craft, a creative storytelling specialist. You excel at:
- Creative writing and storytelling
- Storyboard creation and visual narrative
- Content planning and ideation
- Brand voice and messaging
- Creative project coordination

You're imaginative, articulate, and skilled at bringing ideas to life through words and narrative structure.""",
    
    "scout": """You are Scout, an information gathering and research specialist. You excel at:
- Web research and information discovery
- Knowledge synthesis and analysis
- Fact checking and verification
- Research planning and methodology
- Information organization

You're thorough, analytical, and focused on finding accurate, relevant information."""
}

class ChatService:
    """Main chat service handling all chat operations"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
        self.llm_client = get_llm_client(config)
        self.memory_manager = get_memory_manager(config)
        self.tool_registry = get_tool_registry(config)
        self.rate_limiter = get_rate_limiter(config)
        self.agent_registry = get_agent_registry()
    
    async def process_chat(self, request: ChatRequest, client_ip: str) -> AsyncGenerator[str, None]:
        """Process chat request and yield streaming responses"""
        
        # Rate limiting check
        if not await self.rate_limiter.check_rate_limit(request.session_id):
            yield self._create_sse_event("error", {"error": "Rate limit exceeded. Please wait before sending another message."})
            return
        
        try:
            # Determine if guarded mode is enabled
            guarded_mode = request.guarded if request.guarded is not None else self.config.guarded
            
            # Get conversation history
            context = await self.memory_manager.get_conversation_context(request.session_id)
            
            # Build messages for LLM
            messages = []
            
            # Add system prompt based on agent
            agent_str = request.agent or "rika"
            try:
                agent_type = AgentType(agent_str)
            except ValueError:
                agent_type = AgentType.RIKA
            
            system_prompt = self.agent_registry.get_system_prompt(agent_type)
            messages.append(LLMMessage("system", system_prompt))
            
            # Add conversation history
            for msg in context:
                messages.append(LLMMessage(msg["role"], msg["content"]))
            
            # Add current user message
            messages.append(LLMMessage("user", request.message))
            
            # Stream response from LLM
            response_content = ""
            tool_calls = []
            
            yield self._create_sse_event("start", {"session_id": request.session_id})
            
            async for llm_response in self.llm_client.chat_stream(messages):
                if llm_response.error:
                    yield self._create_sse_event("error", {"error": llm_response.error})
                    return
                
                if llm_response.content:
                    response_content += llm_response.content
                    yield self._create_sse_event("token", {"content": llm_response.content})
                
                if llm_response.tool_calls:
                    tool_calls.extend(llm_response.tool_calls)
                
                if llm_response.finished:
                    break
            
            # Process tool calls if any
            if tool_calls and not guarded_mode:
                yield self._create_sse_event("tools_start", {"tool_count": len(tool_calls)})
                
                for tool_call in tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    yield self._create_sse_event("tool_result", {
                        "tool": tool_call.get("name"),
                        "result": tool_result
                    })
                
                yield self._create_sse_event("tools_complete", {})
            
            elif tool_calls and guarded_mode:
                # In guarded mode, just show planned tools
                yield self._create_sse_event("tools_planned", {
                    "tools": tool_calls,
                    "message": "Tools planned but not executed (guarded mode active)"
                })
            
            # Save to memory
            await self.memory_manager.add_interaction(
                request.session_id,
                request.message,
                response_content,
                tool_calls if not guarded_mode else []
            )
            
            yield self._create_sse_event("complete", {
                "session_id": request.session_id,
                "response": response_content,
                "tool_calls": tool_calls,
                "guarded": guarded_mode
            })
            
        except Exception as e:
            yield self._create_sse_event("error", {"error": str(e)})
    
    async def process_chat_non_stream(self, request: ChatRequest, client_ip: str) -> ChatResponse:
        """Process chat request without streaming"""
        
        # Rate limiting check
        if not await self.rate_limiter.check_rate_limit(request.session_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        try:
            # Similar logic but collect all responses
            guarded_mode = request.guarded if request.guarded is not None else self.config.guarded
            context = await self.memory_manager.get_conversation_context(request.session_id)
            
            # Build messages
            messages = []
            agent_str = request.agent or "rika"
            try:
                agent_type = AgentType(agent_str)
            except ValueError:
                agent_type = AgentType.RIKA
            
            system_prompt = self.agent_registry.get_system_prompt(agent_type)
            messages.append(LLMMessage("system", system_prompt))
            
            for msg in context:
                messages.append(LLMMessage(msg["role"], msg["content"]))
            
            messages.append(LLMMessage("user", request.message))
            
            # Get response
            llm_response = await self.llm_client.chat(messages)
            
            if llm_response.error:
                raise HTTPException(status_code=500, detail=llm_response.error)
            
            # Process tools if any
            tool_calls = []
            if llm_response.tool_calls and not guarded_mode:
                for tool_call in llm_response.tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    tool_calls.append({
                        "tool": tool_call.get("name"),
                        "result": tool_result
                    })
            
            # Save to memory
            await self.memory_manager.add_interaction(
                request.session_id,
                request.message,
                llm_response.content,
                tool_calls
            )
            
            return ChatResponse(
                response=llm_response.content,
                session_id=request.session_id,
                tool_calls=tool_calls,
                finished=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool call"""
        try:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            
            result = await self.tool_registry.execute_tool(tool_name, **tool_args)
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _create_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Create Server-Sent Event formatted string"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

# Global chat service instance
_chat_service: Optional[ChatService] = None

def get_chat_service() -> ChatService:
    """Get or create the global chat service"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(config)
    return _chat_service

# FastAPI route handlers
@chat_router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """Main chat endpoint - supports both streaming and non-streaming"""
    chat_service = get_chat_service()
    client_ip = http_request.client.host
    
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            chat_service.process_chat(request, client_ip),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    else:
        # Return regular JSON response
        return await chat_service.process_chat_non_stream(request, client_ip)

@chat_router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """List recent chat sessions"""
    memory_manager = get_memory_manager(config)
    sessions = await memory_manager.list_recent_sessions()
    return SessionListResponse(sessions=sessions)

@chat_router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific chat session"""
    memory_manager = get_memory_manager(config)
    success = await memory_manager.clear_session(session_id)
    
    if success:
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@chat_router.get("/agents")
async def list_agents():
    """List available AI agents"""
    agent_registry = get_agent_registry()
    return {
        "agents": agent_registry.list_agents()
    }

@chat_router.get("/health")
async def chat_health():
    """Chat system health check"""
    return {
        "status": "healthy",
        "llm_provider": config.llm_provider,
        "memory_provider": config.memory_provider,
        "guarded_mode": config.guarded
    }