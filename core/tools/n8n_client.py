"""
Rika Phase 3.4 n8n Tool Client
Integration with n8n workflows for task execution
"""
import httpx
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from .datetime import datetime, timezone
from .config import RikaConfig

class N8NTask:
    """Represents an n8n workflow execution task"""
    def __init__(self, task_id: str, workflow_id: str, status: str = "pending", result: Optional[Dict] = None):
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.status = status  # pending, running, completed, failed
        self.result = result
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class N8NClient:
    """Client for interacting with n8n workflows"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
        self.base_url = config.n8n_base_url.rstrip('/')
        self.timeout = config.n8n_timeout
        
        # In-memory task tracking (could be moved to persistent storage later)
        self.tasks: Dict[str, N8NTask] = {}
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
    
    async def run_workflow(self, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an n8n workflow
        Returns: {task_id, status, status_url?}
        """
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = N8NTask(task_id=task_id, workflow_id=workflow_id, status="pending")
        self.tasks[task_id] = task
        
        try:
            # Construct webhook URL for the workflow
            webhook_url = f"{self.base_url}/webhook/{workflow_id}"
            
            # Execute the workflow
            response = await self.client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                task.status = "completed"
                task.result = response.json()
                task.updated_at = datetime.now(timezone.utc)
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": task.result,
                    "execution_time_ms": int((task.updated_at - task.created_at).total_seconds() * 1000)
                }
            
            elif response.status_code == 202:
                # Asynchronous execution
                task.status = "running"
                task.updated_at = datetime.now(timezone.utc)
                
                return {
                    "task_id": task_id,
                    "status": "running",
                    "status_url": f"/tools/n8n/status/{task_id}"
                }
            
            else:
                task.status = "failed"
                task.result = {"error": f"HTTP {response.status_code}: {response.text}"}
                task.updated_at = datetime.now(timezone.utc)
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": task.result["error"]
                }
        
        except httpx.TimeoutException:
            task.status = "failed"
            task.result = {"error": f"Workflow execution timed out after {self.timeout}s"}
            task.updated_at = datetime.now(timezone.utc)
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Timeout"
            }
        
        except Exception as e:
            task.status = "failed"
            task.result = {"error": str(e)}
            task.updated_at = datetime.now(timezone.utc)
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow execution task
        Returns: {task_id, status, result?, error?}
        """
        task = self.tasks.get(task_id)
        if not task:
            return {
                "task_id": task_id,
                "status": "not_found",
                "error": "Task not found"
            }
        
        return {
            "task_id": task_id,
            "workflow_id": task.workflow_id,
            "status": task.status,
            "result": task.result,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List available n8n workflows (stub implementation)
        In a real implementation, this would query the n8n API
        """
        # TODO: Implement actual n8n API call to list workflows
        # For now, return some example workflows
        return [
            {
                "id": "email-notification",
                "name": "Send Email Notification",
                "description": "Send an email notification with custom message",
                "inputs": ["recipient", "subject", "message"]
            },
            {
                "id": "data-processing",
                "name": "Process Data Pipeline",
                "description": "Execute data processing pipeline with input data",
                "inputs": ["data_source", "processing_type", "output_format"]
            },
            {
                "id": "file-backup",
                "name": "Backup Files",
                "description": "Backup specified files to cloud storage",
                "inputs": ["file_paths", "backup_location", "compression"]
            }
        ]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old task records to prevent memory leaks"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task.created_at.timestamp() < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        return len(tasks_to_remove)

# Tool functions for use in chat
class N8NTools:
    """Tool interface for n8n integration in chat"""
    
    def __init__(self, client: N8NClient):
        self.client = client
    
    async def run(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an n8n workflow from chat"""
        return await self.client.run_workflow(workflow_id, input_data)
    
    async def status(self, task_id: str) -> Dict[str, Any]:
        """Check status of a workflow execution"""
        return await self.client.get_status(task_id)
    
    async def list_available(self) -> List[Dict[str, Any]]:
        """List available workflows"""
        return await self.client.list_workflows()

# Tool definitions for LLM function calling
N8N_TOOL_DEFINITIONS = [
    {
        "name": "n8n_run_workflow",
        "description": "Execute an n8n workflow with input data",
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "The ID of the n8n workflow to execute"
                },
                "input_data": {
                    "type": "object",
                    "description": "Input data to pass to the workflow"
                }
            },
            "required": ["workflow_id", "input_data"]
        }
    },
    {
        "name": "n8n_check_status",
        "description": "Check the status of a workflow execution",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID returned from workflow execution"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "n8n_list_workflows",
        "description": "List available n8n workflows",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

# Global client instance
_n8n_client: Optional[N8NClient] = None

def get_n8n_client(config: RikaConfig) -> N8NClient:
    """Get or create the global n8n client"""
    global _n8n_client
    if _n8n_client is None:
        _n8n_client = N8NClient(config)
    return _n8n_client