"""
Rika Phase 3.5 Great Sage Orchestration System
Advanced agent fusion, coordination, and intelligent task distribution
"""
import asyncio
import time
import logging
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

from .agents import AgentType, get_agent_registry
from .knowledge_vault import knowledge_vault
from .proxy import privacy_proxy
from .voice import voice_service

logger = logging.getLogger(__name__)

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"

class FusionMode(str, Enum):
    """Agent fusion modes"""
    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"     # Agents work simultaneously
    COLLABORATIVE = "collaborative"  # Agents share context in real-time
    HIERARCHICAL = "hierarchical"   # Lead agent delegates to others

class GreatSageTask(BaseModel):
    """Orchestrated task model"""
    id: str
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    fusion_mode: FusionMode = FusionMode.SEQUENTIAL
    assigned_agents: List[AgentType] = []
    required_capabilities: List[str] = []
    max_execution_time: int = 300  # 5 minutes default
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = {}
    results: Dict[str, Any] = {}
    error_message: Optional[str] = None

class AgentCapability(BaseModel):
    """Agent capability mapping"""
    agent_type: AgentType
    capabilities: List[str]
    performance_score: float = 1.0
    availability: bool = True
    current_load: int = 0
    max_concurrent: int = 3

class GreatSage:
    """Advanced orchestration system for agent fusion and coordination"""
    
    def __init__(self):
        self.agent_registry = get_agent_registry()
        self.active_tasks: Dict[str, GreatSageTask] = {}
        self.agent_capabilities: Dict[AgentType, AgentCapability] = {}
        self.fusion_strategies: Dict[FusionMode, callable] = {}
        self.task_queue: List[GreatSageTask] = []
        
        self._initialize_agent_capabilities()
        self._initialize_fusion_strategies()
    
    def _initialize_agent_capabilities(self):
        """Initialize agent capability mappings"""
        capabilities_map = {
            AgentType.RIKA: [
                "general_assistance", "conversation", "task_coordination",
                "knowledge_synthesis", "decision_making", "problem_solving"
            ],
            AgentType.RIG: [
                "programming", "system_architecture", "debugging", "code_review",
                "technical_analysis", "infrastructure", "automation"
            ],
            AgentType.CRAFT: [
                "design", "ui_ux", "creative_writing", "content_creation",
                "visual_design", "branding", "artistic_direction"
            ],
            AgentType.SCOUT: [
                "research", "data_gathering", "analysis", "market_research",
                "competitive_intelligence", "fact_checking", "investigation"
            ],
            AgentType.ECHO: [
                "memory_management", "context_preservation", "history_tracking",
                "knowledge_continuity", "pattern_recognition", "learning"
            ],
            AgentType.PULSE: [
                "monitoring", "real_time_data", "alerts", "status_updates",
                "performance_tracking", "health_checks", "notifications"
            ]
        }
        
        for agent_type, capabilities in capabilities_map.items():
            self.agent_capabilities[agent_type] = AgentCapability(
                agent_type=agent_type,
                capabilities=capabilities,
                performance_score=1.0,
                availability=True,
                current_load=0,
                max_concurrent=3
            )
    
    def _initialize_fusion_strategies(self):
        """Initialize fusion strategy implementations"""
        self.fusion_strategies = {
            FusionMode.SEQUENTIAL: self._execute_sequential,
            FusionMode.PARALLEL: self._execute_parallel,
            FusionMode.COLLABORATIVE: self._execute_collaborative,
            FusionMode.HIERARCHICAL: self._execute_hierarchical
        }
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        timestamp = int(time.time() * 1000)
        return f"sage_task_{timestamp}"
    
    def _select_optimal_agents(self, required_capabilities: List[str], max_agents: int = 3) -> List[AgentType]:
        """Select optimal agents based on required capabilities"""
        agent_scores = {}
        
        for agent_type, capability in self.agent_capabilities.items():
            if not capability.availability or capability.current_load >= capability.max_concurrent:
                continue
                
            # Calculate capability match score
            matches = len(set(required_capabilities) & set(capability.capabilities))
            capability_score = matches / len(required_capabilities) if required_capabilities else 0
            
            # Factor in performance and current load
            load_penalty = capability.current_load / capability.max_concurrent
            final_score = capability_score * capability.performance_score * (1 - load_penalty)
            
            agent_scores[agent_type] = final_score
        
        # Sort by score and return top agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent_type for agent_type, score in sorted_agents[:max_agents] if score > 0]
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        fusion_mode: FusionMode = FusionMode.SEQUENTIAL,
        required_capabilities: List[str] = None,
        max_execution_time: int = 300,
        context: Dict[str, Any] = None
    ) -> str:
        """Create a new orchestrated task"""
        task_id = self._generate_task_id()
        
        # Auto-select agents if not specified
        if required_capabilities:
            assigned_agents = self._select_optimal_agents(required_capabilities)
        else:
            assigned_agents = [AgentType.RIKA]  # Default to Rika for general tasks
        
        task = GreatSageTask(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            fusion_mode=fusion_mode,
            assigned_agents=assigned_agents,
            required_capabilities=required_capabilities or [],
            max_execution_time=max_execution_time,
            created_at=datetime.now(),
            context=context or {}
        )
        
        self.active_tasks[task_id] = task
        self.task_queue.append(task)
        
        # Store task in knowledge vault for future reference
        await knowledge_vault.store(
            title=f"Task: {title}",
            content=f"Description: {description}\nAgents: {[a.value for a in assigned_agents]}\nPriority: {priority.value}",
            category="orchestration",
            tags=["great_sage", "task", priority.value],
            metadata={
                "task_id": task_id,
                "agents": [a.value for a in assigned_agents],
                "fusion_mode": fusion_mode.value
            }
        )
        
        logger.info(f"Created task {task_id}: {title} with agents {assigned_agents}")
        return task_id
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task using the Great Sage orchestration"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.active_tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task {task_id} is not in pending status")
        
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Update agent loads
            for agent_type in task.assigned_agents:
                if agent_type in self.agent_capabilities:
                    self.agent_capabilities[agent_type].current_load += 1
            
            # Execute using the specified fusion strategy
            fusion_strategy = self.fusion_strategies.get(task.fusion_mode)
            if not fusion_strategy:
                raise ValueError(f"Unknown fusion mode: {task.fusion_mode}")
            
            result = await fusion_strategy(task)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.results = result
            
            logger.info(f"Completed task {task_id} successfully")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Task {task_id} failed: {e}")
            raise
        finally:
            # Update agent loads
            for agent_type in task.assigned_agents:
                if agent_type in self.agent_capabilities:
                    self.agent_capabilities[agent_type].current_load = max(0, 
                        self.agent_capabilities[agent_type].current_load - 1)
    
    async def _execute_sequential(self, task: GreatSageTask) -> Dict[str, Any]:
        """Execute task with agents working sequentially"""
        results = {}
        context = task.context.copy()
        
        for i, agent_type in enumerate(task.assigned_agents):
            agent_context = {
                "task_description": task.description,
                "agent_role": f"Agent {i+1} of {len(task.assigned_agents)}",
                "previous_results": results,
                "shared_context": context
            }
            
            # Simulate agent work (in real implementation, this would call actual LLM)
            agent_result = await self._simulate_agent_work(agent_type, agent_context)
            results[agent_type.value] = agent_result
            
            # Update shared context for next agent
            context.update(agent_result.get("context_updates", {}))
        
        return {
            "fusion_mode": "sequential",
            "agent_results": results,
            "final_context": context,
            "execution_order": [a.value for a in task.assigned_agents]
        }
    
    async def _execute_parallel(self, task: GreatSageTask) -> Dict[str, Any]:
        """Execute task with agents working in parallel"""
        agent_tasks = []
        
        for agent_type in task.assigned_agents:
            agent_context = {
                "task_description": task.description,
                "agent_role": f"Parallel execution",
                "shared_context": task.context
            }
            agent_tasks.append(self._simulate_agent_work(agent_type, agent_context))
        
        # Execute all agents concurrently
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        agent_results = {}
        for i, result in enumerate(results):
            agent_type = task.assigned_agents[i]
            if isinstance(result, Exception):
                agent_results[agent_type.value] = {"error": str(result)}
            else:
                agent_results[agent_type.value] = result
        
        return {
            "fusion_mode": "parallel",
            "agent_results": agent_results,
            "execution_time": "concurrent"
        }
    
    async def _execute_collaborative(self, task: GreatSageTask) -> Dict[str, Any]:
        """Execute task with agents collaborating in real-time"""
        shared_workspace = {
            "task_description": task.description,
            "collaboration_log": [],
            "shared_knowledge": task.context.copy(),
            "active_agents": [a.value for a in task.assigned_agents]
        }
        
        rounds = 3  # Number of collaboration rounds
        for round_num in range(rounds):
            round_results = {}
            
            for agent_type in task.assigned_agents:
                agent_context = {
                    "round": round_num + 1,
                    "shared_workspace": shared_workspace,
                    "other_agents": [a.value for a in task.assigned_agents if a != agent_type]
                }
                
                result = await self._simulate_agent_work(agent_type, agent_context)
                round_results[agent_type.value] = result
                
                # Update shared workspace
                shared_workspace["collaboration_log"].append({
                    "round": round_num + 1,
                    "agent": agent_type.value,
                    "contribution": result.get("contribution", "")
                })
                shared_workspace["shared_knowledge"].update(
                    result.get("knowledge_updates", {})
                )
        
        return {
            "fusion_mode": "collaborative",
            "rounds": rounds,
            "final_workspace": shared_workspace,
            "collaboration_summary": shared_workspace["collaboration_log"]
        }
    
    async def _execute_hierarchical(self, task: GreatSageTask) -> Dict[str, Any]:
        """Execute task with hierarchical delegation"""
        if not task.assigned_agents:
            raise ValueError("No agents assigned for hierarchical execution")
        
        # First agent is the leader
        leader = task.assigned_agents[0]
        subordinates = task.assigned_agents[1:]
        
        # Leader analyzes and delegates
        leader_context = {
            "task_description": task.description,
            "role": "leader",
            "available_agents": [a.value for a in subordinates],
            "delegation_mode": True
        }
        
        leader_result = await self._simulate_agent_work(leader, leader_context)
        
        # Execute delegated tasks
        subordinate_results = {}
        for agent_type in subordinates:
            delegation = leader_result.get("delegations", {}).get(agent_type.value, {})
            if delegation:
                subordinate_context = {
                    "delegated_task": delegation,
                    "reporting_to": leader.value,
                    "original_task": task.description
                }
                subordinate_results[agent_type.value] = await self._simulate_agent_work(
                    agent_type, subordinate_context
                )
        
        return {
            "fusion_mode": "hierarchical",
            "leader": leader.value,
            "leader_analysis": leader_result,
            "subordinate_results": subordinate_results,
            "hierarchy": [leader.value] + [a.value for a in subordinates]
        }
    
    async def _simulate_agent_work(self, agent_type: AgentType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate agent work (placeholder for actual LLM integration)"""
        agent_info = self.agent_registry.get_agent(agent_type)
        
        # Simulate processing time based on agent type
        processing_time = {
            AgentType.RIKA: 1.0,
            AgentType.RIG: 1.5,
            AgentType.CRAFT: 2.0,
            AgentType.SCOUT: 2.5,
            AgentType.ECHO: 1.0,
            AgentType.PULSE: 0.5
        }.get(agent_type, 1.0)
        
        await asyncio.sleep(processing_time)
        
        return {
            "agent": agent_type.value,
            "agent_name": agent_info.name if agent_info else agent_type.value,
            "processing_time": processing_time,
            "context_received": bool(context),
            "timestamp": datetime.now().isoformat(),
            "contribution": f"{agent_info.name if agent_info else agent_type.value} completed analysis",
            "knowledge_updates": {
                f"{agent_type.value}_insights": f"Insights from {agent_type.value}"
            },
            "delegations": {
                subordinate: {"task": f"Subtask for {subordinate}", "priority": "medium"}
                for subordinate in context.get("available_agents", [])
            } if context.get("delegation_mode") else {}
        }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status"""
        if task_id not in self.active_tasks:
            return {"error": "Task not found"}
        
        task = self.active_tasks[task_id]
        return {
            "task_id": task_id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "fusion_mode": task.fusion_mode.value,
            "assigned_agents": [a.value for a in task.assigned_agents],
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "results": task.results,
            "error_message": task.error_message
        }
    
    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks"""
        return [await self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_tasks = len(self.active_tasks)
        completed_tasks = sum(1 for task in self.active_tasks.values() if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in self.active_tasks.values() if task.status == TaskStatus.FAILED)
        
        agent_status = {}
        for agent_type, capability in self.agent_capabilities.items():
            agent_status[agent_type.value] = {
                "availability": capability.availability,
                "current_load": capability.current_load,
                "max_concurrent": capability.max_concurrent,
                "performance_score": capability.performance_score,
                "capabilities": capability.capabilities
            }
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "queue_length": len(self.task_queue),
            "agent_status": agent_status,
            "fusion_modes_available": [mode.value for mode in FusionMode],
            "system_uptime": time.time()
        }

# Global Great Sage instance
great_sage = GreatSage()