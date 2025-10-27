"""
Rika Phase 3.4 Memory System
Lightweight session memory with JSON fallback and optional PostgreSQL
"""
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from .config import RikaConfig

class ConversationTurn:
    """Single turn in a conversation"""
    def __init__(self, user_message: str, assistant_message: str, timestamp: Optional[datetime] = None, tool_calls: Optional[List] = None):
        self.user_message = user_message
        self.assistant_message = assistant_message
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.tool_calls = tool_calls or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_message": self.user_message,
            "assistant_message": self.assistant_message,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc)
        return cls(
            user_message=data["user_message"],
            assistant_message=data["assistant_message"],
            timestamp=timestamp,
            tool_calls=data.get("tool_calls", [])
        )

class ConversationSession:
    """Complete conversation session"""
    def __init__(self, session_id: str, turns: Optional[List[ConversationTurn]] = None):
        self.session_id = session_id
        self.turns = turns or []
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
    
    def add_turn(self, user_message: str, assistant_message: str, tool_calls: Optional[List] = None):
        """Add a new turn to the conversation"""
        turn = ConversationTurn(user_message, assistant_message, tool_calls=tool_calls)
        self.turns.append(turn)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_recent_turns(self, max_turns: int) -> List[ConversationTurn]:
        """Get the most recent N turns"""
        return self.turns[-max_turns:] if max_turns > 0 else self.turns
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        session = cls(data["session_id"])
        session.turns = [ConversationTurn.from_dict(turn_data) for turn_data in data.get("turns", [])]
        session.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc)
        session.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else session.created_at
        return session

class BaseMemoryStore(ABC):
    """Abstract base class for memory storage"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session"""
        pass
    
    @abstractmethod
    async def save_session(self, session: ConversationSession) -> bool:
        """Save a conversation session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        pass
    
    @abstractmethod
    async def list_sessions(self, limit: int = 50) -> List[str]:
        """List recent session IDs"""
        pass

class JSONMemoryStore(BaseMemoryStore):
    """JSON file-based memory storage"""
    
    def __init__(self, config: RikaConfig):
        super().__init__(config)
        self.storage_dir = Path("data/memory")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_cache: Dict[str, ConversationSession] = {}
        
    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session"""
        return self.storage_dir / f"{session_id}.json"
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session"""
        # Check cache first
        if session_id in self.sessions_cache:
            return self.sessions_cache[session_id]
        
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = ConversationSession.from_dict(data)
            # Cache the session
            self.sessions_cache[session_id] = session
            return session
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    async def save_session(self, session: ConversationSession) -> bool:
        """Save a conversation session"""
        try:
            session_file = self._get_session_file(session.session_id)
            
            # Limit turns to prevent files from growing too large
            max_turns = self.config.memory_max_turns
            if len(session.turns) > max_turns:
                session.turns = session.turns[-max_turns:]
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update cache
            self.sessions_cache[session.session_id] = session
            return True
            
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        try:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
            
            # Remove from cache
            self.sessions_cache.pop(session_id, None)
            return True
            
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    async def list_sessions(self, limit: int = 50) -> List[str]:
        """List recent session IDs"""
        try:
            session_files = list(self.storage_dir.glob("*.json"))
            # Sort by modification time, most recent first
            session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            session_ids = []
            for session_file in session_files[:limit]:
                session_id = session_file.stem
                session_ids.append(session_id)
            
            return session_ids
            
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

class PostgresMemoryStore(BaseMemoryStore):
    """PostgreSQL-based memory storage (future implementation)"""
    
    def __init__(self, config: RikaConfig):
        super().__init__(config)
        if not config.database_url:
            raise ValueError("DATABASE_URL is required for PostgreSQL memory store")
        # TODO: Initialize asyncpg connection pool
        
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        # TODO: Implement PostgreSQL queries
        raise NotImplementedError("PostgreSQL memory store not implemented yet")
    
    async def save_session(self, session: ConversationSession) -> bool:
        # TODO: Implement PostgreSQL queries  
        raise NotImplementedError("PostgreSQL memory store not implemented yet")
    
    async def delete_session(self, session_id: str) -> bool:
        # TODO: Implement PostgreSQL queries
        raise NotImplementedError("PostgreSQL memory store not implemented yet")
    
    async def list_sessions(self, limit: int = 50) -> List[str]:
        # TODO: Implement PostgreSQL queries
        raise NotImplementedError("PostgreSQL memory store not implemented yet")

class MemoryManager:
    """High-level interface for memory operations"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
        
        if config.memory_provider == "postgres" and config.database_url:
            self.store = PostgresMemoryStore(config)
        else:
            self.store = JSONMemoryStore(config)
    
    async def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create a new one"""
        session = await self.store.get_session(session_id)
        if session is None:
            session = ConversationSession(session_id)
        return session
    
    async def add_interaction(self, session_id: str, user_message: str, assistant_message: str, tool_calls: Optional[List] = None) -> bool:
        """Add a new interaction to a session"""
        session = await self.get_or_create_session(session_id)
        session.add_turn(user_message, assistant_message, tool_calls)
        return await self.store.save_session(session)
    
    async def get_conversation_context(self, session_id: str, max_turns: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation context formatted for LLM"""
        session = await self.store.get_session(session_id)
        if not session:
            return []
        
        max_turns = max_turns or self.config.memory_max_turns
        recent_turns = session.get_recent_turns(max_turns)
        
        context = []
        for turn in recent_turns:
            context.append({"role": "user", "content": turn.user_message})
            context.append({"role": "assistant", "content": turn.assistant_message})
        
        return context
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session"""
        return await self.store.delete_session(session_id)
    
    async def list_recent_sessions(self, limit: int = 50) -> List[str]:
        """List recent session IDs"""
        return await self.store.list_sessions(limit)

# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None

def get_memory_manager(config: RikaConfig) -> MemoryManager:
    """Get or create the global memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(config)
    return _memory_manager