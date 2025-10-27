"""
Minimal test server for 6-agent endpoint testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Rika Test Server", version="test")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock agent data
AGENTS = [
    {
        "type": "rika",
        "name": "Rika",
        "description": "General purpose AI assistant - balanced, helpful, and versatile",
        "color": "#667eea",
        "emoji": "🤝"
    },
    {
        "type": "rig",
        "name": "Rig",
        "description": "Technical specialist - programming, engineering, and system architecture",
        "color": "#10b981",
        "emoji": "⚙️"
    },
    {
        "type": "craft",
        "name": "Craft",
        "description": "Creative specialist - design, UI/UX, content creation, and artistic endeavors",
        "color": "#8b5cf6",
        "emoji": "🎨"
    },
    {
        "type": "scout",
        "name": "Scout",
        "description": "Research specialist - information gathering, analysis, and knowledge synthesis",
        "color": "#f59e0b",
        "emoji": "🔍"
    },
    {
        "type": "echo",
        "name": "Echo",
        "description": "Memory specialist - context preservation, history tracking, and knowledge continuity",
        "color": "#06b6d4",
        "emoji": "🧠"
    },
    {
        "type": "pulse",
        "name": "Pulse",
        "description": "Real-time specialist - monitoring, alerts, status updates, and live data",
        "color": "#ef4444",
        "emoji": "⚡"
    }
]

@app.get("/")
def root():
    return {"message": "Rika Test Server", "status": "running", "agents": len(AGENTS)}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "test", "version": "1.0"}

@app.get("/chat/agents")
def list_agents():
    """List available AI agents"""
    return {"agents": AGENTS}

@app.get("/chat/health")
def chat_health():
    """Chat system health check"""
    return {
        "status": "healthy",
        "agents_count": len(AGENTS),
        "test_mode": True
    }

@app.get("/voice/health")
def voice_health():
    """Voice service health check"""
    return {
        "status": "healthy",
        "elevenlabs_configured": False,
        "whisper_configured": False,
        "features": {
            "text_to_speech": False,
            "speech_to_text": False
        },
        "test_mode": True,
        "message": "Voice endpoints available for testing"
    }

@app.get("/voice/agents")
def voice_agents():
    """List agent voice configurations"""
    voice_agents = []
    for agent in AGENTS:
        voice_agents.append({
            "type": agent["type"],
            "name": agent["name"],
            "voice_id": f"mock_voice_{agent['type']}",
            "has_voice": True
        })
    return {"agents": voice_agents}

@app.get("/proxy/health")
def proxy_health():
    """Privacy proxy health check"""
    return {
        "status": "healthy",
        "features": {
            "url_fetch": True,
            "brave_search": False,
            "metadata_stripping": True,
            "caching": True
        },
        "cache_stats": {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
            "cache_size_bytes": 0
        },
        "test_mode": True,
        "message": "Proxy endpoints available for testing"
    }

@app.get("/proxy/cache/stats")
def proxy_cache_stats():
    """Get proxy cache statistics"""
    return {
        "cache_stats": {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
            "cache_size_bytes": 0
        },
        "test_mode": True
    }

@app.get("/knowledge/health")
def knowledge_health():
    """Knowledge vault health check"""
    return {
        "status": "healthy",
        "features": {
            "storage": True,
            "search": True,
            "caching": True,
            "auto_cleanup": True
        },
        "stats": {
            "total_entries": 0,
            "cached_entries": 0,
            "disk_entries": 0,
            "categories": 0,
            "cache_enabled": True,
            "auto_cleanup": True,
            "last_cleanup": 0
        },
        "test_mode": True,
        "message": "Knowledge vault endpoints available for testing"
    }

@app.get("/knowledge/categories")
def knowledge_categories():
    """Get knowledge categories"""
    return {
        "categories": ["general", "technical", "creative", "research", "agent"],
        "test_mode": True
    }

@app.get("/knowledge/stats")
def knowledge_stats():
    """Get knowledge statistics"""
    return {
        "stats": {
            "total_entries": 0,
            "cached_entries": 0,
            "disk_entries": 0,
            "categories": 5,
            "cache_enabled": True,
            "auto_cleanup": True,
            "last_cleanup": 0
        },
        "test_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5318)