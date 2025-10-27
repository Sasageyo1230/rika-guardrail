# phase3/l2-autonomy/autonomy_controller.py
# Guarded Autonomy L2 System - Main Controller

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import httpx
import asyncpg
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

# Configure logging
logger = structlog.get_logger()

class AutonomyLevel(str, Enum):
    DISABLED = "disabled"
    L1_SUPERVISED = "l1_supervised"  # Human approves each action
    L2_GUARDED = "l2_guarded"       # AI acts within bounds, human oversight
    L3_AUTONOMOUS = "l3_autonomous"  # Full autonomy (future)

class ChangeScope(str, Enum):
    SAFE_REFACTOR = "safe_refactor"      # Code refactoring, comments, formatting
    UI_IMPROVEMENT = "ui_improvement"     # UI/UX improvements
    PERFORMANCE = "performance"          # Performance optimizations
    BUG_FIX = "bug_fix"                 # Bug fixes
    FEATURE_ADD = "feature_add"         # New features (requires approval)
    SYSTEM_CONFIG = "system_config"     # System configuration changes

@dataclass
class AutonomyBounds:
    """Defines what the L2 system is allowed to do"""
    allowed_scopes: List[ChangeScope]
    max_files_per_change: int = 5
    max_lines_per_file: int = 100
    require_tests: bool = True
    require_eval_pass: bool = True
    rollback_on_failure: bool = True
    human_notification: bool = True

class AutonomyRequest(BaseModel):
    """Request for autonomous action"""
    task_description: str
    scope: ChangeScope
    priority: str = "normal"  # low, normal, high, urgent
    context: Dict[str, Any] = Field(default_factory=dict)
    requester: str = "l2_system"
    timeout_minutes: int = 30

class AutonomyDecision(BaseModel):
    """Decision about autonomous action"""
    request_id: str
    approved: bool
    reason: str
    bounds: Optional[Dict] = None
    expires_at: datetime
    restrictions: List[str] = Field(default_factory=list)

class TaskExecution(BaseModel):
    """Execution status of autonomous task"""
    request_id: str
    status: str  # queued, running, completed, failed, rolled_back
    agent_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    files_changed: List[str] = Field(default_factory=list)
    eval_results: Optional[Dict] = None
    rollback_info: Optional[Dict] = None
    error: Optional[str] = None

class L2AutonomyController:
    """Main controller for L2 Guarded Autonomy"""
    
    def __init__(self, db_url: str, overseer_url: str, sage_url: str, eval_url: str):
        self.db_url = db_url
        self.overseer_url = overseer_url
        self.sage_url = sage_url
        self.eval_url = eval_url
        
        # Current autonomy settings
        self.current_level = AutonomyLevel.DISABLED
        self.bounds = AutonomyBounds(
            allowed_scopes=[ChangeScope.SAFE_REFACTOR, ChangeScope.UI_IMPROVEMENT],
            max_files_per_change=3,
            max_lines_per_file=50,
            require_tests=True,
            require_eval_pass=True
        )
        
        # Active tasks tracking
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.task_queue = asyncio.Queue()
        
        # Agent registry
        self.available_agents = {
            "scout-v0": "agents/scout.py",
            "craft-v0": "agents/craft.py"
        }
    
    async def set_autonomy_level(self, level: AutonomyLevel, bounds: Optional[AutonomyBounds] = None) -> bool:
        """Set autonomy level with optional bounds update"""
        try:
            # Request permission from Overseer for level changes
            if level != AutonomyLevel.DISABLED:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{self.overseer_url}/check", json={
                        "capability": "autonomy_level_change",
                        "requester": "l2_controller",
                        "context": {
                            "new_level": level.value,
                            "current_level": self.current_level.value
                        }
                    })
                    
                    if response.status_code != 200:
                        return False
                    
                    decision = response.json()
                    if decision.get("decision") != "allow":
                        logger.warning(f"Autonomy level change denied: {decision.get('reason')}")
                        return False
            
            self.current_level = level
            if bounds:
                self.bounds = bounds
            
            logger.info(f"Autonomy level set to: {level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set autonomy level: {e}")
            return False
    
    async def request_autonomous_action(self, request: AutonomyRequest) -> AutonomyDecision:
        """Request permission for autonomous action"""
        request_id = f"l2_{uuid.uuid4().hex[:8]}"
        
        # Check if scope is allowed
        if request.scope not in self.bounds.allowed_scopes:
            return AutonomyDecision(
                request_id=request_id,
                approved=False,
                reason=f"Scope {request.scope.value} not in allowed scopes",
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
        
        # Check current autonomy level
        if self.current_level == AutonomyLevel.DISABLED:
            return AutonomyDecision(
                request_id=request_id,
                approved=False,
                reason="Autonomy is currently disabled",
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
        
        # For L2, check with Overseer for complex changes
        needs_approval = (
            request.scope in [ChangeScope.FEATURE_ADD, ChangeScope.SYSTEM_CONFIG] or
            request.priority == "urgent"
        )
        
        if needs_approval:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{self.overseer_url}/check", json={
                        "capability": "autonomous_action",
                        "requester": "l2_system",
                        "context": {
                            "task_description": request.task_description,
                            "scope": request.scope.value,
                            "priority": request.priority
                        }
                    })
                    
                    if response.status_code != 200:
                        raise Exception(f"Overseer request failed: {response.status_code}")
                    
                    decision = response.json()
                    
                    if decision.get("decision") == "deny":
                        return AutonomyDecision(
                            request_id=request_id,
                            approved=False,
                            reason=decision.get("reason", "Denied by Overseer"),
                            expires_at=datetime.utcnow() + timedelta(minutes=5)
                        )
                    elif decision.get("decision") == "review":
                        # Return pending status, will be resolved by approval flow
                        return AutonomyDecision(
                            request_id=decision.get("request_id", request_id),
                            approved=False,
                            reason="Pending human approval",
                            expires_at=datetime.utcnow() + timedelta(minutes=request.timeout_minutes)
                        )
            
            except Exception as e:
                logger.error(f"Failed to check with Overseer: {e}")
                return AutonomyDecision(
                    request_id=request_id,
                    approved=False,
                    reason=f"Overseer check failed: {e}",
                    expires_at=datetime.utcnow() + timedelta(minutes=5)
                )
        
        # Approve with bounds
        return AutonomyDecision(
            request_id=request_id,
            approved=True,
            reason=f"Approved for L2 autonomy within bounds",
            bounds={
                "max_files": self.bounds.max_files_per_change,
                "max_lines_per_file": self.bounds.max_lines_per_file,
                "require_tests": self.bounds.require_tests,
                "require_eval": self.bounds.require_eval_pass
            },
            expires_at=datetime.utcnow() + timedelta(minutes=request.timeout_minutes),
            restrictions=[
                f"Scope limited to: {request.scope.value}",
                f"Max files: {self.bounds.max_files_per_change}",
                f"Max lines per file: {self.bounds.max_lines_per_file}"
            ]
        )
    
    async def execute_autonomous_task(self, request: AutonomyRequest, decision: AutonomyDecision) -> TaskExecution:
        """Execute approved autonomous task"""
        if not decision.approved:
            raise ValueError("Cannot execute unapproved task")
        
        execution = TaskExecution(
            request_id=decision.request_id,
            status="queued",
            agent_id="scout-v0",  # Default agent
            start_time=datetime.utcnow()
        )
        
        self.active_tasks[decision.request_id] = execution
        
        try:
            # Queue the task for execution
            await self.task_queue.put((request, decision, execution))
            execution.status = "running"
            
            # Select appropriate agent
            agent_id = self._select_agent(request.scope)
            execution.agent_id = agent_id
            
            # Execute with the selected agent
            result = await self._execute_with_agent(agent_id, request, decision)
            
            execution.files_changed = result.get("files_changed", [])
            execution.status = "completed" if result.get("success") else "failed"
            execution.end_time = datetime.utcnow()
            
            # Run evaluation if required
            if self.bounds.require_eval_pass and result.get("success"):
                eval_result = await self._run_evaluation(execution.files_changed)
                execution.eval_results = eval_result
                
                if not eval_result.get("passed", False):
                    execution.status = "failed"
                    execution.error = "Evaluation failed"
                    
                    # Rollback if required
                    if self.bounds.rollback_on_failure:
                        await self._rollback_changes(execution)
            
            # Notify human if required
            if self.bounds.human_notification:
                await self._notify_completion(execution, request)
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.end_time = datetime.utcnow()
            logger.error(f"Task execution failed: {e}")
            
            # Attempt rollback on failure
            if self.bounds.rollback_on_failure:
                try:
                    await self._rollback_changes(execution)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
        
        return execution
    
    def _select_agent(self, scope: ChangeScope) -> str:
        """Select appropriate agent for the task scope"""
        if scope in [ChangeScope.SAFE_REFACTOR, ChangeScope.BUG_FIX]:
            return "craft-v0"  # Code modification agent
        else:
            return "scout-v0"  # General purpose agent
    
    async def _execute_with_agent(self, agent_id: str, request: AutonomyRequest, decision: AutonomyDecision) -> Dict:
        """Execute task with specified agent"""
        agent_script = self.available_agents.get(agent_id)
        if not agent_script:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        # This would invoke the actual agent script
        # For now, simulate execution
        return {
            "success": True,
            "files_changed": ["/example/file1.py", "/example/file2.py"],
            "changes_made": "Refactored code for better performance",
            "agent_logs": f"Agent {agent_id} completed task successfully"
        }
    
    async def _run_evaluation(self, files_changed: List[str]) -> Dict:
        """Run evaluation on changed files"""
        try:
            # This would call the evaluation harness
            # For now, simulate evaluation
            return {
                "passed": True,
                "metrics": {
                    "accuracy": 0.95,
                    "performance_impact": "positive",
                    "test_coverage": 0.92
                },
                "details": f"Evaluation passed for {len(files_changed)} files"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "details": "Evaluation failed"
            }
    
    async def _rollback_changes(self, execution: TaskExecution):
        """Rollback changes if evaluation fails"""
        try:
            # This would implement git rollback or similar
            execution.rollback_info = {
                "rollback_time": datetime.utcnow().isoformat(),
                "files_reverted": execution.files_changed,
                "method": "git_revert"
            }
            execution.status = "rolled_back"
            logger.info(f"Rolled back changes for task {execution.request_id}")
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
    
    async def _notify_completion(self, execution: TaskExecution, request: AutonomyRequest):
        """Notify human of task completion"""
        try:
            # This would send notification via configured channel
            logger.info(f"Task {execution.request_id} completed: {execution.status}")
        except Exception as e:
            logger.warning(f"Notification failed: {e}")

# FastAPI app
app = FastAPI(title="Rika L2 Autonomy Controller", version="1.0.0")

# Global controller instance
controller = None

@app.on_event("startup")
async def startup():
    global controller
    controller = L2AutonomyController(
        db_url=os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core"),
        overseer_url=os.getenv("OVERSEER_URL", "http://localhost:5319"),
        sage_url=os.getenv("SAGE_URL", "http://localhost:5320"),
        eval_url=os.getenv("EVAL_URL", "http://localhost:5321")
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "autonomy_level": controller.current_level.value if controller else "unknown",
        "active_tasks": len(controller.active_tasks) if controller else 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/status")
async def get_status():
    """Get current autonomy status"""
    if not controller:
        raise HTTPException(500, "Controller not initialized")
    
    return {
        "autonomy_level": controller.current_level.value,
        "bounds": {
            "allowed_scopes": [scope.value for scope in controller.bounds.allowed_scopes],
            "max_files_per_change": controller.bounds.max_files_per_change,
            "max_lines_per_file": controller.bounds.max_lines_per_file,
            "require_tests": controller.bounds.require_tests,
            "require_eval_pass": controller.bounds.require_eval_pass
        },
        "active_tasks": {
            task_id: {
                "status": task.status,
                "agent_id": task.agent_id,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "files_changed": len(task.files_changed)
            }
            for task_id, task in controller.active_tasks.items()
        },
        "available_agents": list(controller.available_agents.keys())
    }

@app.post("/set-level")
async def set_autonomy_level(level: AutonomyLevel, bounds: Optional[Dict] = None):
    """Set autonomy level"""
    if not controller:
        raise HTTPException(500, "Controller not initialized")
    
    # Convert bounds dict to AutonomyBounds if provided
    bounds_obj = None
    if bounds:
        bounds_obj = AutonomyBounds(
            allowed_scopes=[ChangeScope(scope) for scope in bounds.get("allowed_scopes", [])],
            max_files_per_change=bounds.get("max_files_per_change", 5),
            max_lines_per_file=bounds.get("max_lines_per_file", 100),
            require_tests=bounds.get("require_tests", True),
            require_eval_pass=bounds.get("require_eval_pass", True)
        )
    
    success = await controller.set_autonomy_level(level, bounds_obj)
    
    if not success:
        raise HTTPException(403, "Failed to set autonomy level")
    
    return {"status": "success", "new_level": level.value}

@app.post("/request-action", response_model=AutonomyDecision)
async def request_action(request: AutonomyRequest):
    """Request autonomous action"""
    if not controller:
        raise HTTPException(500, "Controller not initialized")
    
    decision = await controller.request_autonomous_action(request)
    return decision

@app.post("/execute-task", response_model=TaskExecution)
async def execute_task(request: AutonomyRequest, background_tasks: BackgroundTasks):
    """Execute autonomous task (if approved)"""
    if not controller:
        raise HTTPException(500, "Controller not initialized")
    
    # First get decision
    decision = await controller.request_autonomous_action(request)
    
    if not decision.approved:
        raise HTTPException(403, f"Task not approved: {decision.reason}")
    
    # Execute in background
    execution = await controller.execute_autonomous_task(request, decision)
    
    return execution

@app.get("/task/{request_id}")
async def get_task_status(request_id: str):
    """Get task execution status"""
    if not controller:
        raise HTTPException(500, "Controller not initialized")
    
    task = controller.active_tasks.get(request_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    return {
        "request_id": task.request_id,
        "status": task.status,
        "agent_id": task.agent_id,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "files_changed": task.files_changed,
        "eval_results": task.eval_results,
        "error": task.error
    }