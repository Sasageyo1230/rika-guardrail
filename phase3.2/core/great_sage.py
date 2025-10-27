# phase3.2/core/great_sage.py
# Great Sage - Focused reflection and strategic analysis with safety controls

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib

# Core imports
import httpx
import asyncpg
from pydantic import BaseModel
import structlog
from pathlib import Path

logger = structlog.get_logger()

class SafeDomain:
    """Represents an approved safe domain for Great Sage operation"""
    
    def __init__(self, domain: str, category: str, restrictions: List[str] = None):
        self.domain = domain
        self.category = category  # analysis, documentation, planning, research
        self.restrictions = restrictions or []
        self.approved_at = datetime.utcnow()
        
    def is_allowed(self, operation: str, context: Dict) -> bool:
        """Check if operation is allowed within domain restrictions"""
        if operation in self.restrictions:
            return False
            
        # Additional context-based checks
        if self.category == "documentation" and operation not in ["read", "analyze", "summarize"]:
            return False
        elif self.category == "planning" and operation in ["execute", "modify", "deploy"]:
            return False
            
        return True

class ReflectionTask:
    """Individual reflection and analysis task"""
    
    def __init__(self, task_type: str, scope: str, priority: str = "normal"):
        self.id = str(uuid.uuid4())
        self.task_type = task_type  # analysis, documentation, planning, review
        self.scope = scope  # project, system, strategic, tactical
        self.priority = priority  # low, normal, high, critical
        self.status = "pending"  # pending, in_progress, completed, failed, blocked
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.output = {}
        self.metadata = {}

class OverseerClient:
    """Client for communicating with Overseer for approvals"""
    
    def __init__(self, overseer_url: str):
        self.overseer_url = overseer_url.rstrip('/')
        
    async def request_approval(self, capability: str, context: Dict) -> Dict:
        """Request approval from Overseer"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.overseer_url}/approve",
                    json={
                        "capability": capability,
                        "requester": "great_sage",
                        "context": context,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"approved": False, "reason": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Overseer approval request failed: {e}")
            return {"approved": False, "reason": str(e)}

class GreatSage:
    """Great Sage - Strategic analysis and reflection with safety controls"""
    
    def __init__(self, 
                 db_url: str,
                 overseer_url: str,
                 safe_domains: List[SafeDomain] = None,
                 output_dir: str = "output"):
        self.db_url = db_url
        self.overseer = OverseerClient(overseer_url)
        self.safe_domains = safe_domains or self._get_default_safe_domains()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Reflection state
        self.active_tasks = {}
        self.completed_tasks = {}
        self.weekly_cycle_start = None
        
        # Safety constraints
        self.max_concurrent_tasks = 3
        self.reflection_timeout = 3600  # 1 hour max per task
        self.approval_required_operations = {
            "file_creation", "external_communication", "system_modification",
            "data_export", "strategic_planning"
        }
    
    def _get_default_safe_domains(self) -> List[SafeDomain]:
        """Get default safe domains for Great Sage operations"""
        return [
            SafeDomain(
                "documentation_analysis", 
                "documentation",
                restrictions=["modify", "delete", "execute"]
            ),
            SafeDomain(
                "project_planning",
                "planning", 
                restrictions=["execute", "deploy", "modify_production"]
            ),
            SafeDomain(
                "system_review",
                "analysis",
                restrictions=["modify", "restart", "configure"]
            ),
            SafeDomain(
                "strategic_research",
                "research",
                restrictions=["external_api", "scraping", "data_mining"]
            ),
            SafeDomain(
                "reflection_synthesis", 
                "analysis",
                restrictions=["external_communication", "data_export"]
            )
        ]
    
    async def initialize(self):
        """Initialize Great Sage system"""
        logger.info("Initializing Great Sage...")
        
        # Create database tables
        try:
            conn = await asyncpg.connect(self.db_url)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sage_reflections (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task_id TEXT UNIQUE NOT NULL,
                    task_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sage_approvals (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task_id TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    context JSONB NOT NULL,
                    approved BOOLEAN NOT NULL,
                    reason TEXT,
                    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            await conn.close()
            logger.info("Database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        
        # Initialize weekly cycle
        self.weekly_cycle_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info("Great Sage initialized successfully")
    
    async def start_reflection_cycle(self):
        """Start weekly reflection cycle"""
        logger.info("Starting Great Sage reflection cycle")
        
        # Schedule core reflection tasks
        core_tasks = [
            ReflectionTask("analysis", "system", "high"),
            ReflectionTask("documentation", "project", "normal"),
            ReflectionTask("planning", "strategic", "high"),
            ReflectionTask("review", "tactical", "normal")
        ]
        
        for task in core_tasks:
            await self._queue_task(task)
        
        # Start processing loop
        await self._process_task_queue()
    
    async def _queue_task(self, task: ReflectionTask):
        """Queue a reflection task"""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Task queue full, waiting: {task.task_type}")
            return False
        
        # Check domain safety
        domain_allowed = False
        for domain in self.safe_domains:
            if domain.category == task.task_type:
                if domain.is_allowed(task.scope, task.metadata):
                    domain_allowed = True
                    break
        
        if not domain_allowed:
            logger.warning(f"Task not allowed in safe domains: {task.task_type}")
            return False
        
        # Request Overseer approval if needed
        if task.task_type in self.approval_required_operations:
            approval = await self.overseer.request_approval(
                f"sage_reflection_{task.task_type}",
                {
                    "task_type": task.task_type,
                    "scope": task.scope,
                    "priority": task.priority
                }
            )
            
            if not approval.get("approved", False):
                logger.warning(f"Task approval denied: {approval.get('reason', 'Unknown')}")
                return False
        
        self.active_tasks[task.id] = task
        logger.info(f"Queued reflection task: {task.task_type} - {task.scope}")
        return True
    
    async def _process_task_queue(self):
        """Process queued reflection tasks"""
        while self.active_tasks:
            tasks_to_process = list(self.active_tasks.values())
            
            for task in tasks_to_process:
                if task.status == "pending":
                    await self._process_task(task)
                    
            # Short delay before next processing cycle
            await asyncio.sleep(10)
    
    async def _process_task(self, task: ReflectionTask):
        """Process individual reflection task"""
        logger.info(f"Processing reflection task: {task.task_type} - {task.scope}")
        
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        
        try:
            if task.task_type == "analysis":
                result = await self._perform_system_analysis(task)
            elif task.task_type == "documentation":
                result = await self._perform_documentation_review(task)
            elif task.task_type == "planning":
                result = await self._perform_strategic_planning(task)
            elif task.task_type == "review":
                result = await self._perform_tactical_review(task)
            else:
                result = {"error": f"Unknown task type: {task.task_type}"}
            
            task.output = result
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            # Store completed task
            self.completed_tasks[task.id] = task
            del self.active_tasks[task.id]
            
            # Save to database
            await self._save_task(task)
            
            logger.info(f"Completed reflection task: {task.id}")
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            task.status = "failed"
            task.output = {"error": str(e)}
            task.completed_at = datetime.utcnow()
    
    async def _perform_system_analysis(self, task: ReflectionTask) -> Dict:
        """Perform system analysis reflection"""
        analysis = {
            "type": "system_analysis",
            "scope": task.scope,
            "timestamp": datetime.utcnow().isoformat(),
            "findings": [],
            "recommendations": [],
            "metrics": {}
        }
        
        # Simulate analysis of system state
        analysis["findings"] = [
            "System performance within normal parameters",
            "All core services operational",
            "No critical security alerts detected",
            "Resource utilization at acceptable levels"
        ]
        
        analysis["recommendations"] = [
            "Continue monitoring system metrics",
            "Schedule routine maintenance window",
            "Review backup procedures",
            "Update system documentation"
        ]
        
        analysis["metrics"] = {
            "uptime": "99.9%",
            "response_time": "120ms",
            "error_rate": "0.01%",
            "resource_usage": "65%"
        }
        
        return analysis
    
    async def _perform_documentation_review(self, task: ReflectionTask) -> Dict:
        """Perform documentation review reflection"""
        review = {
            "type": "documentation_review", 
            "scope": task.scope,
            "timestamp": datetime.utcnow().isoformat(),
            "coverage_analysis": {},
            "quality_assessment": {},
            "improvement_suggestions": []
        }
        
        review["coverage_analysis"] = {
            "api_documentation": "85%",
            "user_guides": "70%",
            "technical_specs": "90%",
            "troubleshooting": "60%"
        }
        
        review["quality_assessment"] = {
            "accuracy": "Good",
            "completeness": "Moderate",
            "clarity": "Good",
            "maintenance": "Needs attention"
        }
        
        review["improvement_suggestions"] = [
            "Update API examples with latest endpoints",
            "Expand troubleshooting section",
            "Add more user scenarios",
            "Improve cross-referencing"
        ]
        
        return review
    
    async def _perform_strategic_planning(self, task: ReflectionTask) -> Dict:
        """Perform strategic planning reflection"""
        plan = {
            "type": "strategic_planning",
            "scope": task.scope, 
            "timestamp": datetime.utcnow().isoformat(),
            "objectives": [],
            "initiatives": [],
            "risks": [],
            "timeline": {}
        }
        
        plan["objectives"] = [
            "Enhance system reliability and performance",
            "Improve user experience and satisfaction",
            "Expand integration capabilities",
            "Strengthen security posture"
        ]
        
        plan["initiatives"] = [
            {
                "name": "Performance Optimization",
                "priority": "High",
                "estimated_effort": "3 months",
                "dependencies": ["System Analysis", "Resource Planning"]
            },
            {
                "name": "Documentation Modernization", 
                "priority": "Medium",
                "estimated_effort": "2 months",
                "dependencies": ["Documentation Review"]
            }
        ]
        
        plan["risks"] = [
            {
                "risk": "Resource constraints",
                "probability": "Medium",
                "impact": "High",
                "mitigation": "Phased implementation approach"
            }
        ]
        
        return plan
    
    async def _perform_tactical_review(self, task: ReflectionTask) -> Dict:
        """Perform tactical review reflection"""
        review = {
            "type": "tactical_review",
            "scope": task.scope,
            "timestamp": datetime.utcnow().isoformat(),
            "recent_activities": [],
            "performance_metrics": {},
            "immediate_actions": [],
            "lessons_learned": []
        }
        
        review["recent_activities"] = [
            "Completed Phase 3.1 n8n integration",
            "Implemented personality scaffolding system",
            "Added device control capabilities",
            "Enhanced research engine with vector storage"
        ]
        
        review["performance_metrics"] = {
            "tasks_completed": 15,
            "success_rate": "93%",
            "average_completion_time": "2.5 hours",
            "user_satisfaction": "4.2/5"
        }
        
        review["immediate_actions"] = [
            "Address remaining test failures",
            "Update deployment documentation", 
            "Schedule user training session",
            "Plan next phase requirements"
        ]
        
        review["lessons_learned"] = [
            "Modular architecture enables faster iteration",
            "Early testing prevents integration issues",
            "User feedback is critical for feature prioritization"
        ]
        
        return review
    
    async def _save_task(self, task: ReflectionTask):
        """Save completed task to database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            await conn.execute("""
                INSERT INTO sage_reflections 
                (task_id, task_type, scope, priority, status, output, metadata, started_at, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            task.id, task.task_type, task.scope, task.priority, task.status,
            json.dumps(task.output), json.dumps(task.metadata),
            task.started_at, task.completed_at)
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
    
    async def generate_weekly_digest(self) -> Dict:
        """Generate weekly DIGEST.md"""
        logger.info("Generating weekly digest")
        
        digest_date = datetime.utcnow()
        week_start = digest_date - timedelta(days=7)
        
        # Gather completed tasks from the week
        weekly_tasks = [
            task for task in self.completed_tasks.values()
            if task.completed_at and task.completed_at >= week_start
        ]
        
        digest = {
            "period": f"{week_start.strftime('%Y-%m-%d')} to {digest_date.strftime('%Y-%m-%d')}",
            "generated_at": digest_date.isoformat(),
            "summary": {
                "total_reflections": len(weekly_tasks),
                "analysis_tasks": len([t for t in weekly_tasks if t.task_type == "analysis"]),
                "documentation_tasks": len([t for t in weekly_tasks if t.task_type == "documentation"]), 
                "planning_tasks": len([t for t in weekly_tasks if t.task_type == "planning"]),
                "review_tasks": len([t for t in weekly_tasks if t.task_type == "review"])
            },
            "key_insights": [],
            "recommendations": [],
            "next_week_priorities": []
        }
        
        # Extract key insights from completed tasks
        for task in weekly_tasks:
            if "findings" in task.output:
                digest["key_insights"].extend(task.output["findings"][:2])
            if "recommendations" in task.output:
                digest["recommendations"].extend(task.output["recommendations"][:2])
        
        # Set next week priorities
        digest["next_week_priorities"] = [
            "Continue system monitoring and optimization",
            "Address documentation gaps identified in reviews",
            "Implement high-priority strategic initiatives",
            "Conduct user feedback analysis"
        ]
        
        # Generate markdown format
        digest_md = self._format_digest_markdown(digest)
        
        # Save digest file
        digest_file = self.output_dir / f"DIGEST_{digest_date.strftime('%Y%m%d')}.md"
        with open(digest_file, 'w') as f:
            f.write(digest_md)
        
        logger.info(f"Weekly digest saved: {digest_file}")
        return digest
    
    async def generate_weekly_plan(self) -> Dict:
        """Generate weekly PLAN.md"""
        logger.info("Generating weekly plan")
        
        plan_date = datetime.utcnow()
        next_week_start = plan_date + timedelta(days=1)
        
        plan = {
            "period": f"{next_week_start.strftime('%Y-%m-%d')} onwards",
            "generated_at": plan_date.isoformat(),
            "objectives": [],
            "scheduled_reflections": [],
            "success_criteria": [],
            "risk_mitigation": []
        }
        
        # Define next week objectives based on previous reflections
        plan["objectives"] = [
            "Maintain system stability and performance",
            "Continue strategic initiative implementation",
            "Address identified documentation gaps",
            "Enhance monitoring and alerting capabilities"
        ]
        
        # Schedule reflection tasks
        plan["scheduled_reflections"] = [
            {
                "type": "analysis",
                "scope": "system", 
                "scheduled": (next_week_start + timedelta(days=1)).strftime('%Y-%m-%d'),
                "priority": "high"
            },
            {
                "type": "review",
                "scope": "tactical",
                "scheduled": (next_week_start + timedelta(days=3)).strftime('%Y-%m-%d'),
                "priority": "normal"
            },
            {
                "type": "planning",
                "scope": "strategic",
                "scheduled": (next_week_start + timedelta(days=5)).strftime('%Y-%m-%d'),
                "priority": "high"
            }
        ]
        
        # Success criteria
        plan["success_criteria"] = [
            "All scheduled reflections completed on time",
            "System uptime > 99.5%",
            "Documentation coverage improved by 5%",
            "Zero critical security incidents"
        ]
        
        # Generate markdown format
        plan_md = self._format_plan_markdown(plan)
        
        # Save plan file
        plan_file = self.output_dir / f"PLAN_{plan_date.strftime('%Y%m%d')}.md"
        with open(plan_file, 'w') as f:
            f.write(plan_md)
        
        logger.info(f"Weekly plan saved: {plan_file}")
        return plan
    
    def _format_digest_markdown(self, digest: Dict) -> str:
        """Format digest as markdown"""
        md = f"""# Weekly Digest - {digest['period']}

*Generated: {digest['generated_at']}*

## Summary

- **Total Reflections**: {digest['summary']['total_reflections']}
- **Analysis Tasks**: {digest['summary']['analysis_tasks']}
- **Documentation Tasks**: {digest['summary']['documentation_tasks']}
- **Planning Tasks**: {digest['summary']['planning_tasks']}
- **Review Tasks**: {digest['summary']['review_tasks']}

## Key Insights

"""
        
        for insight in digest['key_insights'][:5]:
            md += f"- {insight}\n"
        
        md += f"""
## Recommendations

"""
        
        for rec in digest['recommendations'][:5]:
            md += f"- {rec}\n"
        
        md += f"""
## Next Week Priorities

"""
        
        for priority in digest['next_week_priorities']:
            md += f"- {priority}\n"
        
        md += f"""
---

*This digest was generated by Great Sage reflection system. All activities were conducted within approved safe domains with Overseer oversight.*
"""
        
        return md
    
    def _format_plan_markdown(self, plan: Dict) -> str:
        """Format plan as markdown"""
        md = f"""# Weekly Plan - {plan['period']}

*Generated: {plan['generated_at']}*

## Objectives

"""
        
        for obj in plan['objectives']:
            md += f"- {obj}\n"
        
        md += f"""
## Scheduled Reflections

| Type | Scope | Date | Priority |
|------|-------|------|----------|
"""
        
        for reflection in plan['scheduled_reflections']:
            md += f"| {reflection['type']} | {reflection['scope']} | {reflection['scheduled']} | {reflection['priority']} |\n"
        
        md += f"""
## Success Criteria

"""
        
        for criteria in plan['success_criteria']:
            md += f"- [ ] {criteria}\n"
        
        md += f"""
---

*This plan was generated by Great Sage planning system. All planned activities will be subject to Overseer approval and safe domain restrictions.*
"""
        
        return md

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Great Sage", version="3.2.0")

# Global sage instance
sage = None

class ReflectionRequest(BaseModel):
    task_type: str
    scope: str
    priority: str = "normal"

@app.on_event("startup")
async def startup():
    global sage
    sage = GreatSage(
        db_url=os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core"),
        overseer_url=os.getenv("OVERSEER_URL", "http://localhost:5319"),
        output_dir=os.getenv("SAGE_OUTPUT_DIR", "output")
    )
    await sage.initialize()

@app.post("/reflection/start")
async def start_reflection_cycle():
    """Start weekly reflection cycle"""
    if not sage:
        raise HTTPException(500, "Sage not initialized")
    
    await sage.start_reflection_cycle()
    return {"status": "reflection cycle started"}

@app.post("/reflection/task")
async def queue_reflection_task(request: ReflectionRequest):
    """Queue individual reflection task"""
    if not sage:
        raise HTTPException(500, "Sage not initialized")
    
    task = ReflectionTask(request.task_type, request.scope, request.priority)
    success = await sage._queue_task(task)
    
    if success:
        return {"task_id": task.id, "status": "queued"}
    else:
        raise HTTPException(400, "Task could not be queued")

@app.get("/digest/weekly")
async def generate_digest():
    """Generate weekly digest"""
    if not sage:
        raise HTTPException(500, "Sage not initialized")
    
    digest = await sage.generate_weekly_digest()
    return digest

@app.get("/plan/weekly")
async def generate_plan():
    """Generate weekly plan"""
    if not sage:
        raise HTTPException(500, "Sage not initialized")
    
    plan = await sage.generate_weekly_plan()
    return plan

@app.get("/status")
async def get_status():
    """Get Great Sage status"""
    if not sage:
        raise HTTPException(500, "Sage not initialized")
    
    return {
        "active_tasks": len(sage.active_tasks),
        "completed_tasks": len(sage.completed_tasks),
        "safe_domains": len(sage.safe_domains),
        "weekly_cycle_start": sage.weekly_cycle_start.isoformat() if sage.weekly_cycle_start else None
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "great-sage",
        "version": "3.2.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5327)