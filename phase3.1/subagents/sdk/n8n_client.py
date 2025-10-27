# phase3.1/subagents/sdk/n8n_client.py
# SDK for sub-agents to safely interact with n8n Gateway

import asyncio
import json
from typing import Dict, List, Optional, Any
import httpx
import structlog

logger = structlog.get_logger()

class N8nClient:
    """Client SDK for sub-agents to interact with n8n Gateway"""
    
    def __init__(self, gateway_url: str = "http://localhost:5324"):
        self.gateway_url = gateway_url.rstrip('/')
        self.agent_id = "unknown"
        self.timeout = 300  # 5 minutes default timeout
    
    def set_agent_identity(self, agent_id: str):
        """Set the identity of the calling agent"""
        self.agent_id = agent_id
    
    async def run_workflow(self, workflow: str, input_data: Dict = None, 
                          tags: List[str] = None, priority: str = "normal") -> Dict:
        """Run n8n workflow through gateway"""
        if input_data is None:
            input_data = {}
        if tags is None:
            tags = []
        
        # Add agent identity to tags
        if self.agent_id != "unknown":
            tags.append(f"agent:{self.agent_id}")
        
        payload = {
            "workflow": workflow,
            "input": input_data,
            "tags": tags,
            "requester": self.agent_id,
            "priority": priority
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gateway_url}/n8n/run",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Workflow executed: {workflow}", 
                              execution_id=result.get("execution_id"),
                              status=result.get("status"))
                    return result
                else:
                    error_msg = f"Workflow execution failed: {response.status_code}"
                    logger.error(error_msg, workflow=workflow)
                    return {"status": "failed", "error": error_msg}
                    
        except Exception as e:
            error_msg = f"Failed to run workflow: {e}"
            logger.error(error_msg, workflow=workflow)
            return {"status": "failed", "error": error_msg}
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of specific execution"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gateway_url}/n8n/executions?execution_id={execution_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    executions = data.get("executions", [])
                    if executions:
                        return executions[0]
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get execution status: {e}")
            return None
    
    async def get_my_executions(self, limit: int = 20) -> List[Dict]:
        """Get executions by this agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gateway_url}/n8n/executions?limit={limit}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    executions = data.get("executions", [])
                    
                    # Filter by agent
                    agent_executions = [
                        exec for exec in executions 
                        if exec.get("metadata", {}).get("requester") == self.agent_id
                    ]
                    
                    return agent_executions
                
                return []
                
        except Exception as e:
            logger.error(f"Failed to get agent executions: {e}")
            return []
    
    async def list_workflows(self) -> List[Dict]:
        """Get available workflows"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/n8n/workflows")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("workflows", [])
                
                return []
                
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    async def wait_for_completion(self, execution_id: str, poll_interval: int = 5, 
                                max_wait: int = 300) -> Dict:
        """Wait for workflow execution to complete"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status_info = await self.get_execution_status(execution_id)
            
            if not status_info:
                return {"status": "failed", "error": "Execution not found"}
            
            status = status_info.get("status")
            
            if status in ["success", "failed", "cancelled"]:
                return status_info
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                return {"status": "timeout", "error": f"Execution exceeded {max_wait}s timeout"}
            
            await asyncio.sleep(poll_interval)
    
    # Convenience methods for common workflow patterns
    
    async def send_notification(self, message: str, channels: List[str] = None, 
                              urgency: str = "normal") -> Dict:
        """Send notification via n8n workflow"""
        if channels is None:
            channels = ["default"]
        
        return await self.run_workflow(
            workflow="notification-sender",
            input_data={
                "message": message,
                "channels": channels,
                "urgency": urgency,
                "source": self.agent_id
            },
            tags=["notification", urgency],
            priority="high" if urgency == "urgent" else "normal"
        )
    
    async def process_data(self, data: Dict, processor: str, options: Dict = None) -> Dict:
        """Process data through n8n workflow"""
        if options is None:
            options = {}
        
        return await self.run_workflow(
            workflow=f"data-processor-{processor}",
            input_data={
                "data": data,
                "options": options,
                "processor": processor
            },
            tags=["data-processing", processor]
        )
    
    async def external_api_call(self, url: str, method: str = "GET", 
                               headers: Dict = None, data: Dict = None) -> Dict:
        """Make external API call through n8n (with safety checks)"""
        if headers is None:
            headers = {}
        
        return await self.run_workflow(
            workflow="external-api-caller",
            input_data={
                "url": url,
                "method": method,
                "headers": headers,
                "data": data,
                "requester": self.agent_id
            },
            tags=["external-api", method.lower()],
            priority="normal"
        )
    
    async def file_operation(self, operation: str, path: str, 
                           content: str = None, options: Dict = None) -> Dict:
        """Perform file operation through n8n (with safety checks)"""
        if options is None:
            options = {}
        
        return await self.run_workflow(
            workflow="file-operations",
            input_data={
                "operation": operation,  # read, write, delete, move, copy
                "path": path,
                "content": content,
                "options": options,
                "requester": self.agent_id
            },
            tags=["file-operation", operation],
            priority="high"  # File operations are important
        )
    
    async def run_command(self, command: str, args: List[str] = None, 
                         working_dir: str = None, timeout: int = 60) -> Dict:
        """Run shell command through n8n (with safety checks)"""
        if args is None:
            args = []
        
        return await self.run_workflow(
            workflow="shell-executor",
            input_data={
                "command": command,
                "args": args,
                "working_dir": working_dir,
                "timeout": timeout,
                "requester": self.agent_id
            },
            tags=["shell-command", "high-risk"],
            priority="high"
        )

# Example usage for different agent types
class RigAgentN8nClient(N8nClient):
    """Specialized n8n client for Rig agent (device control)"""
    
    def __init__(self, gateway_url: str = "http://localhost:5324"):
        super().__init__(gateway_url)
        self.set_agent_identity("rig")
    
    async def control_device(self, device: str, action: str, parameters: Dict = None) -> Dict:
        """Control device through n8n workflow"""
        if parameters is None:
            parameters = {}
        
        return await self.run_workflow(
            workflow="device-controller",
            input_data={
                "device": device,
                "action": action,
                "parameters": parameters
            },
            tags=["device-control", device, action]
        )
    
    async def tv_command(self, command: str) -> Dict:
        """TV control commands"""
        return await self.control_device("tv", command)
    
    async def pc_command(self, command: str) -> Dict:
        """PC control commands"""
        return await self.control_device("pc", command)

class CraftAgentN8nClient(N8nClient):
    """Specialized n8n client for Craft agent (code modification)"""
    
    def __init__(self, gateway_url: str = "http://localhost:5324"):
        super().__init__(gateway_url)
        self.set_agent_identity("craft")
    
    async def deploy_code(self, project: str, branch: str = "main", 
                         environment: str = "staging") -> Dict:
        """Deploy code through n8n workflow"""
        return await self.run_workflow(
            workflow="code-deployer",
            input_data={
                "project": project,
                "branch": branch,
                "environment": environment
            },
            tags=["deployment", environment]
        )
    
    async def run_tests(self, project: str, test_suite: str = "all") -> Dict:
        """Run tests through n8n workflow"""
        return await self.run_workflow(
            workflow="test-runner",
            input_data={
                "project": project,
                "test_suite": test_suite
            },
            tags=["testing", test_suite]
        )

class ScoutAgentN8nClient(N8nClient):
    """Specialized n8n client for Scout agent (research)"""
    
    def __init__(self, gateway_url: str = "http://localhost:5324"):
        super().__init__(gateway_url)
        self.set_agent_identity("scout")
    
    async def web_research(self, query: str, depth: str = "quick", 
                          sources: List[str] = None) -> Dict:
        """Perform web research through n8n workflow"""
        if sources is None:
            sources = []
        
        return await self.run_workflow(
            workflow="web-researcher",
            input_data={
                "query": query,
                "depth": depth,  # quick, deep
                "sources": sources,
                "max_pages": 5 if depth == "quick" else 15
            },
            tags=["research", depth]
        )
    
    async def data_analysis(self, dataset: str, analysis_type: str, 
                          parameters: Dict = None) -> Dict:
        """Analyze data through n8n workflow"""
        if parameters is None:
            parameters = {}
        
        return await self.run_workflow(
            workflow="data-analyzer",
            input_data={
                "dataset": dataset,
                "analysis_type": analysis_type,
                "parameters": parameters
            },
            tags=["analysis", analysis_type]
        )