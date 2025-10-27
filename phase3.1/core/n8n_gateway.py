# phase3.1/core/n8n_gateway.py
# n8n Gateway - Safe interface for workflow automation

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
import asyncpg
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

class WorkflowRunRequest(BaseModel):
    """Request to run an n8n workflow"""
    workflow: str  # workflow name or ID
    input: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    requester: str = "system"
    priority: str = "normal"  # low, normal, high, urgent

class WorkflowPromoteRequest(BaseModel):
    """Request to promote a workflow"""
    workflow_id: str
    version: str = "latest"
    environment: str = "production"  # staging, production
    approver: str
    notes: str = ""

class ExecutionResult(BaseModel):
    """Result of workflow execution"""
    execution_id: str
    workflow_id: str
    status: str  # running, success, failed, cancelled
    start_time: datetime
    end_time: Optional[datetime] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class N8nGateway:
    """n8n Gateway - Central interface for workflow automation"""
    
    def __init__(self, n8n_url: str, api_key: str, overseer_url: str, db_url: str):
        self.n8n_url = n8n_url.rstrip('/')
        self.api_key = api_key
        self.overseer_url = overseer_url
        self.db_url = db_url
        
        # Risk categories for different operations
        self.risk_categories = {
            'file.write': 'high',
            'exec.shell': 'critical',
            'external.webhook': 'medium',
            'data.read': 'low',
            'notification.send': 'low',
            'api.call': 'medium'
        }
    
    async def check_operation_safety(self, workflow: str, operation_type: str, context: Dict) -> bool:
        """Check with Overseer before risky operations"""
        risk_level = self.risk_categories.get(operation_type, 'medium')
        
        if risk_level in ['low']:
            return True  # Skip check for low-risk operations
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.overseer_url}/check", json={
                    "capability": f"n8n_workflow_{operation_type}",
                    "requester": "n8n_gateway",
                    "context": {
                        "workflow": workflow,
                        "operation_type": operation_type,
                        "risk_level": risk_level,
                        **context
                    }
                })
                
                if response.status_code == 200:
                    decision = response.json()
                    return decision.get("decision") == "allow"
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to check operation safety: {e}")
            return False  # Fail safe
    
    async def run_workflow(self, request: WorkflowRunRequest) -> ExecutionResult:
        """Execute n8n workflow with safety checks"""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Running workflow: {request.workflow}", execution_id=execution_id)
        
        try:
            # Analyze workflow for risky operations
            risky_ops = await self._analyze_workflow_risks(request.workflow)
            
            # Check safety for each risky operation
            for op_type, op_context in risky_ops.items():
                safe = await self.check_operation_safety(
                    request.workflow, op_type, {**op_context, **request.input}
                )
                if not safe:
                    return ExecutionResult(
                        execution_id=execution_id,
                        workflow_id=request.workflow,
                        status="failed",
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        error=f"Operation {op_type} denied by safety check"
                    )
            
            # Execute workflow via n8n API
            result = await self._execute_n8n_workflow(request)
            
            # Store execution record
            await self._store_execution(execution_id, request, result)
            
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=request.workflow,
                status=result.get("status", "success"),
                start_time=start_time,
                end_time=datetime.utcnow(),
                output=result.get("output", {}),
                metadata={
                    "tags": request.tags,
                    "requester": request.requester,
                    "risky_operations": list(risky_ops.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=request.workflow,
                status="failed",
                start_time=start_time,
                end_time=datetime.utcnow(),
                error=str(e)
            )
    
    async def _analyze_workflow_risks(self, workflow_id: str) -> Dict[str, Dict]:
        """Analyze workflow for risky operations"""
        risky_ops = {}
        
        try:
            # Get workflow definition from n8n
            async with httpx.AsyncClient() as client:
                headers = {"X-N8N-API-KEY": self.api_key}
                response = await client.get(
                    f"{self.n8n_url}/api/v1/workflows/{workflow_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    workflow_data = response.json()
                    nodes = workflow_data.get("nodes", [])
                    
                    for node in nodes:
                        node_type = node.get("type", "")
                        parameters = node.get("parameters", {})
                        
                        # Check for risky node types
                        if "filesystem" in node_type.lower() or "file" in node_type.lower():
                            if parameters.get("operation") in ["write", "create", "delete"]:
                                risky_ops["file.write"] = {
                                    "node": node.get("name", ""),
                                    "operation": parameters.get("operation"),
                                    "path": parameters.get("fileName", "")
                                }
                        
                        elif "shell" in node_type.lower() or "execute" in node_type.lower():
                            risky_ops["exec.shell"] = {
                                "node": node.get("name", ""),
                                "command": parameters.get("command", "")
                            }
                        
                        elif "webhook" in node_type.lower() or "http" in node_type.lower():
                            if not parameters.get("url", "").startswith(("http://localhost", "http://127.0.0.1")):
                                risky_ops["external.webhook"] = {
                                    "node": node.get("name", ""),
                                    "url": parameters.get("url", "")
                                }
        
        except Exception as e:
            logger.warning(f"Failed to analyze workflow risks: {e}")
        
        return risky_ops
    
    async def _execute_n8n_workflow(self, request: WorkflowRunRequest) -> Dict:
        """Execute workflow via n8n API"""
        async with httpx.AsyncClient(timeout=300) as client:
            headers = {
                "X-N8N-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Trigger workflow execution
            payload = {
                "workflowData": request.input,
                "loadStaticData": True
            }
            
            response = await client.post(
                f"{self.n8n_url}/api/v1/workflows/{request.workflow}/execute",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"n8n API error: {response.status_code} {response.text}")
    
    async def _store_execution(self, execution_id: str, request: WorkflowRunRequest, result: Dict):
        """Store execution record in database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS n8n_executions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    execution_id TEXT UNIQUE NOT NULL,
                    workflow_id TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    input_data JSONB NOT NULL,
                    output_data JSONB,
                    status TEXT NOT NULL,
                    tags TEXT[],
                    error_message TEXT,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                INSERT INTO n8n_executions 
                (execution_id, workflow_id, requester, input_data, output_data, status, tags, start_time, end_time)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            execution_id, request.workflow, request.requester,
            json.dumps(request.input), json.dumps(result), 
            result.get("status", "completed"), request.tags,
            datetime.utcnow(), datetime.utcnow())
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
    
    async def get_executions(self, workflow_id: Optional[str] = None, 
                           limit: int = 50, status: Optional[str] = None) -> List[ExecutionResult]:
        """Get workflow execution history"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            query = "SELECT * FROM n8n_executions WHERE 1=1"
            params = []
            
            if workflow_id:
                query += " AND workflow_id = $" + str(len(params) + 1)
                params.append(workflow_id)
            
            if status:
                query += " AND status = $" + str(len(params) + 1)
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [
                ExecutionResult(
                    execution_id=row["execution_id"],
                    workflow_id=row["workflow_id"],
                    status=row["status"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    output=row["output_data"] or {},
                    error=row["error_message"],
                    metadata={
                        "requester": row["requester"],
                        "tags": row["tags"] or []
                    }
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get executions: {e}")
            return []
    
    async def promote_workflow(self, request: WorkflowPromoteRequest) -> bool:
        """Promote workflow with Overseer approval"""
        try:
            # Check with Overseer for promotion approval
            safe = await self.check_operation_safety(
                request.workflow_id, "workflow.promote", {
                    "environment": request.environment,
                    "approver": request.approver,
                    "notes": request.notes
                }
            )
            
            if not safe:
                logger.warning(f"Workflow promotion denied: {request.workflow_id}")
                return False
            
            # Implement promotion logic here
            # This would typically involve copying workflow to production environment
            logger.info(f"Workflow promoted: {request.workflow_id} to {request.environment}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote workflow: {e}")
            return False
    
    async def get_available_workflows(self) -> List[Dict]:
        """Get list of available workflows"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"X-N8N-API-KEY": self.api_key}
                response = await client.get(
                    f"{self.n8n_url}/api/v1/workflows",
                    headers=headers
                )
                
                if response.status_code == 200:
                    workflows = response.json()
                    return [
                        {
                            "id": wf.get("id"),
                            "name": wf.get("name"),
                            "active": wf.get("active", False),
                            "tags": wf.get("tags", []),
                            "updated": wf.get("updatedAt")
                        }
                        for wf in workflows.get("data", [])
                    ]
                
                return []
                
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []

# FastAPI integration
from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI(title="n8n Gateway", version="3.1.0")

# Initialize gateway
gateway = None

@app.on_event("startup")
async def startup():
    global gateway
    gateway = N8nGateway(
        n8n_url=os.getenv("N8N_URL", "http://localhost:5678"),
        api_key=os.getenv("N8N_API_KEY", ""),
        overseer_url=os.getenv("OVERSEER_URL", "http://localhost:5319"),
        db_url=os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core")
    )

@app.post("/n8n/run", response_model=ExecutionResult)
async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
    """Run n8n workflow with safety checks"""
    if not gateway:
        raise HTTPException(500, "Gateway not initialized")
    
    result = await gateway.run_workflow(request)
    return result

@app.get("/n8n/executions")
async def get_executions(workflow_id: Optional[str] = None, 
                        limit: int = 50, status: Optional[str] = None):
    """Get workflow execution history"""
    if not gateway:
        raise HTTPException(500, "Gateway not initialized")
    
    executions = await gateway.get_executions(workflow_id, limit, status)
    return {
        "executions": executions,
        "total": len(executions)
    }

@app.post("/n8n/promote")
async def promote_workflow(request: WorkflowPromoteRequest):
    """Promote workflow to production"""
    if not gateway:
        raise HTTPException(500, "Gateway not initialized")
    
    success = await gateway.promote_workflow(request)
    
    if success:
        return {"status": "promoted", "workflow_id": request.workflow_id}
    else:
        raise HTTPException(403, "Promotion denied by safety check")

@app.get("/n8n/workflows")
async def get_workflows():
    """Get available workflows"""
    if not gateway:
        raise HTTPException(500, "Gateway not initialized")
    
    workflows = await gateway.get_available_workflows()
    return {"workflows": workflows}

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "n8n-gateway",
        "version": "3.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5324)