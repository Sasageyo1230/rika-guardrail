"""
Rika Phase 3.4 Configuration System
Reads from environment variables and config/default.json fallback
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

class RikaConfig(BaseSettings):
    """Configuration for Rika Phase 3.4"""
    
    # LLM Configuration
    llm_provider: str = Field(default="anthropic", description="LLM provider: anthropic, openai, or local")
    model_name: str = Field(default="claude-3-haiku-20240307", description="Model name to use")
    guarded: bool = Field(default=False, description="If true, plan tools but don't execute")
    max_tokens: int = Field(default=2048, description="Maximum tokens per response")
    
    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Local LLM Configuration
    local_base_url: str = Field(default="http://localhost:11434", description="Local LLM base URL (Ollama)")
    local_model_name: str = Field(default="llama2", description="Local model name")
    
    # Memory Configuration
    memory_provider: str = Field(default="json", description="Memory provider: postgres or json")
    memory_max_turns: int = Field(default=20, description="Maximum conversation turns to remember")
    
    # Database Configuration (if using postgres)
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection string")
    
    # n8n Configuration
    n8n_base_url: str = Field(default="http://localhost:5324", description="n8n webhook base URL")
    n8n_timeout: int = Field(default=30, description="n8n request timeout in seconds")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute per session")
    
    # Security
    allowed_origins: list = Field(default=["http://localhost:5173", "http://localhost:3000"], description="CORS allowed origins")
    
    model_config = {
        "extra": "ignore"
    }

def load_config() -> RikaConfig:
    """Load configuration from environment and config files"""
    
    # Try to load from config/default.json if it exists
    config_path = Path("config/default.json")
    config_data = {}
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config/default.json: {e}")
    
    # Environment variables take precedence
    env_overrides = {}
    
    # Map common environment variable names
    env_mappings = {
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "OPENAI_API_KEY": "openai_api_key", 
        "LLM_PROVIDER": "llm_provider",
        "MODEL_NAME": "model_name",
        "GUARDED": "guarded",
        "DATABASE_URL": "database_url"
    }
    
    for env_name, config_name in env_mappings.items():
        if os.getenv(env_name):
            env_overrides[config_name] = os.getenv(env_name)
    
    # Merge config file and environment variables
    final_config = {**config_data, **env_overrides}
    
    # Filter to only include known fields
    known_fields = {
        "llm_provider", "model_name", "guarded", "max_tokens",
        "anthropic_api_key", "openai_api_key", 
        "local_base_url", "local_model_name",
        "memory_provider", "memory_max_turns",
        "database_url",
        "n8n_base_url", "n8n_timeout",
        "rate_limit_per_minute",
        "allowed_origins"
    }
    
    filtered_config = {k: v for k, v in final_config.items() if k in known_fields}
    
    return RikaConfig(**filtered_config)

def create_default_config_file():
    """Create a default config file if it doesn't exist"""
    config_path = Path("config/default.json")
    
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "llm_provider": "anthropic",
            "model_name": "claude-3-haiku-20240307", 
            "guarded": False,
            "max_tokens": 2048,
            "memory_provider": "json",
            "memory_max_turns": 20,
            "n8n_base_url": "http://localhost:5324",
            "n8n_timeout": 30,
            "rate_limit_per_minute": 60,
            "local_base_url": "http://localhost:11434",
            "local_model_name": "llama2",
            "allowed_origins": ["http://localhost:5173", "http://localhost:3000"]
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"Created default config at: {config_path}")

# Global config instance
config = load_config()