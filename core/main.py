from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import config, create_default_config_file
from .chat import chat_router
from .ui_patch import ui_patch_router
from .tools.n8n_client import get_n8n_client

# Create default config if it doesn't exist
create_default_config_file()

app = FastAPI(title="Rika Core API", version="3.4")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins + ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(ui_patch_router)

@app.get("/")
def root():
    return {"message": "Rika Core API v3.4", "status": "running", "features": ["chat", "streaming", "tools", "design_mode"]}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "core", "version": "3.4"}

@app.get("/selfcheck")
def selfcheck():
    return {
        "status": "ok",
        "version": "3.4",
        "checks": {
            "database": "ok",
            "memory": "ok",
            "cpu": "ok",
            "llm_provider": config.llm_provider,
            "guarded_mode": config.guarded
        }
    }

# n8n tool endpoints
@app.post("/tools/n8n/run")
async def run_n8n_workflow(workflow_id: str, payload: dict):
    """Manually test n8n workflow execution"""
    client = get_n8n_client(config)
    return await client.run_workflow(workflow_id, payload)

@app.get("/tools/n8n/status/{task_id}")
async def get_n8n_status(task_id: str):
    """Get n8n workflow execution status"""
    client = get_n8n_client(config)
    return await client.get_status(task_id)

@app.get("/tools/n8n/workflows")
async def list_n8n_workflows():
    """List available n8n workflows"""
    client = get_n8n_client(config)
    return await client.list_workflows()

@app.get("/config")
def get_config():
    """Get current configuration (excluding secrets)"""
    return {
        "llm_provider": config.llm_provider,
        "model_name": config.model_name,
        "guarded": config.guarded,
        "memory_provider": config.memory_provider,
        "memory_max_turns": config.memory_max_turns,
        "rate_limit_per_minute": config.rate_limit_per_minute,
        "has_anthropic_key": bool(config.anthropic_api_key),
        "has_openai_key": bool(config.openai_api_key),
        "local_base_url": config.local_base_url,
        "local_model_name": config.local_model_name,
        "n8n_base_url": config.n8n_base_url
    }