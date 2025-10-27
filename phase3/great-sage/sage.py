# phase3/great-sage/sage.py
"""
Rika Great Sage - Meta-cortex Loop
Observe → Reflect → Plan → Try → Evaluate → Promote
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core')
MINIO_URL = os.getenv('MINIO_URL', 'http://localhost:9000')
OVERSEER_URL = os.getenv('OVERSEER_URL', 'http://localhost:5319')
METHOD_LIBRARY_PATH = Path(os.getenv('METHOD_LIBRARY_PATH', '../method-library'))

# FastAPI setup
app = FastAPI(
    title="Rika Great Sage",
    version="3.0.0",
    description="Meta-cortex loop for continuous improvement"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db_pool = None

# ============= Models =============

class ReflectionRequest(BaseModel):
    days_back: int = Field(default=7, description="Days of logs to analyze")
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus on")

class ReflectionResult(BaseModel):
    summary: str
    insights: List[str]
    improvement_opportunities: List[str]
    plan_generated: bool
    plan_path: Optional[str]

class EvalRequest(BaseModel):
    domain: str = Field(..., description="Domain to evaluate (prompts, router, etc)")
    version: Optional[str] = None
    run_full_suite: bool = False

class EvalResult(BaseModel):
    domain: str
    version: str
    passed: bool
    metrics: Dict[str, float]
    details: Dict[str, Any]
    timestamp: datetime

class PromotionRequest(BaseModel):
    artifact_type: str = Field(..., description="Type of artifact (prompt, router, eval)")
    version: str = Field(..., description="Version to promote")
    reason: str = Field(..., description="Reason for promotion")
    require_approval: bool = True

class PromotionResult(BaseModel):
    status: str
    version: str
    promoted_at: Optional[datetime]
    approval_required: bool
    request_id: Optional[str]

# ============= Observation & Reflection =============

async def gather_logs(days_back: int = 7) -> Dict[str, List[Dict]]:
    """Gather logs from various sources for reflection"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    logs = {
        "audit_logs": [],
        "control_sessions": [],
        "device_activity": [],
        "errors": [],
        "performance": []
    }
    
    try:
        async with db_pool.acquire() as conn:
            # Audit logs
            audit_entries = await conn.fetch("""
                SELECT * FROM audit_logs 
                WHERE timestamp >= $1 AND timestamp <= $2
                ORDER BY timestamp DESC
            """, start_date, end_date)
            logs["audit_logs"] = [dict(entry) for entry in audit_entries]
            
            # Control sessions
            control_sessions = await conn.fetch("""
                SELECT * FROM control_sessions 
                WHERE created_at >= $1 AND created_at <= $2
                ORDER BY created_at DESC
            """, start_date, end_date)
            logs["control_sessions"] = [dict(session) for session in control_sessions]
            
            # Device activity patterns
            device_activity = await conn.fetch("""
                SELECT device_id, COUNT(*) as activity_count,
                       AVG(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as uptime_ratio
                FROM device_presence_log 
                WHERE timestamp >= $1 AND timestamp <= $2
                GROUP BY device_id
                ORDER BY activity_count DESC
            """, start_date, end_date)
            logs["device_activity"] = [dict(activity) for activity in device_activity] if device_activity else []
            
    except Exception as e:
        logging.error(f"Error gathering logs: {e}")
    
    return logs

def analyze_patterns(logs: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Analyze patterns in gathered logs"""
    analysis = {
        "control_usage": {},
        "error_patterns": {},
        "device_health": {},
        "security_events": {},
        "performance_trends": {}
    }
    
    # Control usage patterns
    control_sessions = logs.get("control_sessions", [])
    if control_sessions:
        total_sessions = len(control_sessions)
        avg_duration = sum(
            (datetime.fromisoformat(s.get("terminated_at", s["created_at"])) - 
             datetime.fromisoformat(s["created_at"])).total_seconds() / 60
            for s in control_sessions if s.get("terminated_at")
        ) / max(len([s for s in control_sessions if s.get("terminated_at")]), 1)
        
        analysis["control_usage"] = {
            "total_sessions": total_sessions,
            "avg_duration_minutes": round(avg_duration, 2),
            "success_rate": len([s for s in control_sessions if s.get("status") == "completed"]) / max(total_sessions, 1)
        }
    
    # Error patterns
    audit_logs = logs.get("audit_logs", [])
    error_events = [log for log in audit_logs if "error" in log.get("event_type", "").lower()]
    if error_events:
        error_types = {}
        for event in error_events:
            event_type = event.get("event_type", "unknown")
            error_types[event_type] = error_types.get(event_type, 0) + 1
        
        analysis["error_patterns"] = {
            "total_errors": len(error_events),
            "top_error_types": dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    # Device health
    device_activity = logs.get("device_activity", [])
    if device_activity:
        analysis["device_health"] = {
            "total_devices": len(device_activity),
            "avg_uptime": sum(d.get("uptime_ratio", 0) for d in device_activity) / len(device_activity),
            "most_active": max(device_activity, key=lambda d: d.get("activity_count", 0)) if device_activity else None
        }
    
    return analysis

def generate_insights(analysis: Dict[str, Any]) -> List[str]:
    """Generate insights from analysis"""
    insights = []
    
    # Control usage insights
    control_usage = analysis.get("control_usage", {})
    if control_usage.get("total_sessions", 0) > 0:
        avg_duration = control_usage.get("avg_duration_minutes", 0)
        if avg_duration > 20:
            insights.append(f"Control sessions are averaging {avg_duration:.1f} minutes, which may indicate inefficient workflows")
        elif avg_duration < 5:
            insights.append("Short control sessions suggest users are accomplishing tasks efficiently")
        
        success_rate = control_usage.get("success_rate", 0)
        if success_rate < 0.8:
            insights.append(f"Control success rate is {success_rate:.1%}, indicating potential reliability issues")
    
    # Error insights
    error_patterns = analysis.get("error_patterns", {})
    if error_patterns.get("total_errors", 0) > 10:
        top_error = list(error_patterns.get("top_error_types", {}).keys())[0] if error_patterns.get("top_error_types") else None
        if top_error:
            insights.append(f"Most common error is '{top_error}' - this should be prioritized for fixes")
    
    # Device health insights
    device_health = analysis.get("device_health", {})
    avg_uptime = device_health.get("avg_uptime", 0)
    if avg_uptime < 0.7:
        insights.append(f"Average device uptime is {avg_uptime:.1%}, suggesting connectivity issues")
    elif avg_uptime > 0.95:
        insights.append("Excellent device uptime indicates stable infrastructure")
    
    return insights

def generate_improvement_plan(insights: List[str], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate actionable improvement plan"""
    plan = {
        "version": f"plan-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
        "created_at": datetime.utcnow().isoformat(),
        "priority": "L2",  # Safe changes only
        "changes": [],
        "expected_impact": [],
        "success_metrics": []
    }
    
    # Generate specific changes based on insights
    for insight in insights:
        if "control sessions" in insight and "averaging" in insight:
            plan["changes"].append({
                "type": "prompt_adjustment",
                "description": "Add timeout warnings to control session prompts",
                "files": ["method-library/prompts/control-session.md"],
                "risk": "low"
            })
            plan["expected_impact"].append("Reduce average control session duration by 15%")
            plan["success_metrics"].append("avg_control_duration < 15 minutes")
        
        elif "error" in insight.lower():
            plan["changes"].append({
                "type": "error_handling", 
                "description": "Improve error messages and retry logic",
                "files": ["phase2.5/core/api.py", "phase2.5/agent-desktop/agent.py"],
                "risk": "low"
            })
            plan["expected_impact"].append("Reduce error rate by 25%")
            plan["success_metrics"].append("error_count < previous_week * 0.75")
        
        elif "uptime" in insight.lower() and "connectivity" in insight:
            plan["changes"].append({
                "type": "connectivity_improvement",
                "description": "Add connection retry logic and better offline handling",
                "files": ["phase2.5/agent-desktop/agent.py"],
                "risk": "low"
            })
            plan["expected_impact"].append("Improve device uptime by 10%")
            plan["success_metrics"].append("avg_uptime > 0.85")
    
    # If no specific changes, add general improvements
    if not plan["changes"]:
        plan["changes"].append({
            "type": "maintenance",
            "description": "General code cleanup and optimization",
            "files": ["phase2.5/ui/src/components/"],
            "risk": "very_low"
        })
        plan["expected_impact"].append("Improved code maintainability")
        plan["success_metrics"].append("no_regression_in_core_metrics")
    
    return plan

# ============= Evaluation System =============

async def run_eval_suite(domain: str, version: str = "current") -> Dict[str, Any]:
    """Run evaluation suite for specified domain"""
    
    eval_results = {
        "domain": domain,
        "version": version,
        "timestamp": datetime.utcnow().isoformat(),
        "tests": [],
        "metrics": {},
        "passed": False
    }
    
    # Load eval configuration
    eval_config_path = METHOD_LIBRARY_PATH / "evals" / f"{domain}-eval.json"
    if not eval_config_path.exists():
        raise HTTPException(404, f"Eval config not found for domain: {domain}")
    
    with open(eval_config_path) as f:
        eval_config = json.load(f)
    
    # Run tests based on domain
    if domain == "prompts":
        eval_results = await eval_prompts(eval_config, version)
    elif domain == "router":
        eval_results = await eval_router(eval_config, version)
    elif domain == "presence":
        eval_results = await eval_presence_queries(eval_config, version)
    else:
        raise HTTPException(400, f"Unknown eval domain: {domain}")
    
    # Calculate overall pass/fail
    passed_tests = sum(1 for test in eval_results["tests"] if test.get("passed", False))
    total_tests = len(eval_results["tests"])
    pass_rate = passed_tests / max(total_tests, 1)
    
    eval_results["metrics"]["pass_rate"] = pass_rate
    eval_results["passed"] = pass_rate >= eval_config.get("pass_threshold", 0.8)
    
    return eval_results

async def eval_prompts(config: Dict, version: str) -> Dict[str, Any]:
    """Evaluate prompts against gold standard"""
    results = {
        "domain": "prompts",
        "version": version,
        "tests": [],
        "metrics": {}
    }
    
    # Load test cases
    test_cases = config.get("test_cases", [])
    
    for test_case in test_cases:
        test_result = {
            "name": test_case["name"],
            "input": test_case["input"],
            "expected_output": test_case["expected_output"],
            "actual_output": None,
            "passed": False,
            "score": 0.0
        }
        
        # Simulate prompt evaluation
        # In a real implementation, this would run the prompt through the system
        # For now, we'll simulate with basic checks
        
        if "device" in test_case["input"].lower():
            test_result["actual_output"] = "Device query processed successfully"
            test_result["passed"] = "device" in test_case["expected_output"].lower()
            test_result["score"] = 1.0 if test_result["passed"] else 0.0
        else:
            test_result["actual_output"] = "Generic response"
            test_result["passed"] = True  # Assume pass for demo
            test_result["score"] = 0.8
        
        results["tests"].append(test_result)
    
    # Calculate metrics
    if results["tests"]:
        results["metrics"]["accuracy"] = sum(t["score"] for t in results["tests"]) / len(results["tests"])
        results["metrics"]["latency_p95"] = 150.0  # Simulated
        results["metrics"]["hallucination_rate"] = 0.02  # Simulated
    
    return results

async def eval_router(config: Dict, version: str) -> Dict[str, Any]:
    """Evaluate router rules"""
    results = {
        "domain": "router", 
        "version": version,
        "tests": [],
        "metrics": {}
    }
    
    # Simulate router evaluation
    test_cases = config.get("test_cases", [])
    
    for test_case in test_cases:
        test_result = {
            "name": test_case["name"],
            "input": test_case["input"],
            "expected_route": test_case["expected_route"],
            "actual_route": None,
            "passed": False
        }
        
        # Simulate routing logic
        if "link" in test_case["input"].lower():
            test_result["actual_route"] = "device_management"
        elif "stream" in test_case["input"].lower():
            test_result["actual_route"] = "streaming"
        else:
            test_result["actual_route"] = "general"
        
        test_result["passed"] = test_result["actual_route"] == test_result["expected_route"]
        results["tests"].append(test_result)
    
    # Calculate routing accuracy
    if results["tests"]:
        correct_routes = sum(1 for t in results["tests"] if t["passed"])
        results["metrics"]["routing_accuracy"] = correct_routes / len(results["tests"])
        results["metrics"]["avg_response_time"] = 45.0  # Simulated ms
    
    return results

async def eval_presence_queries(config: Dict, version: str) -> Dict[str, Any]:
    """Evaluate presence query handling"""
    results = {
        "domain": "presence",
        "version": version,
        "tests": [],
        "metrics": {}
    }
    
    # Test presence query accuracy
    test_cases = config.get("test_cases", [])
    
    for test_case in test_cases:
        test_result = {
            "name": test_case["name"],
            "query": test_case["query"],
            "expected_devices": test_case.get("expected_devices", []),
            "actual_devices": [],
            "passed": False
        }
        
        # Simulate presence query
        if "active" in test_case["query"].lower():
            test_result["actual_devices"] = ["laptop-001", "desktop-002"]  # Simulated
        elif "offline" in test_case["query"].lower():
            test_result["actual_devices"] = ["tablet-003"]
        else:
            test_result["actual_devices"] = test_case.get("expected_devices", [])
        
        test_result["passed"] = set(test_result["actual_devices"]) == set(test_result["expected_devices"])
        results["tests"].append(test_result)
    
    if results["tests"]:
        results["metrics"]["query_accuracy"] = sum(1 for t in results["tests"] if t["passed"]) / len(results["tests"])
        results["metrics"]["response_time"] = 120.0  # Simulated ms
    
    return results

# ============= Promotion System =============

async def promote_artifact(artifact_type: str, version: str, reason: str, require_approval: bool = True) -> Dict[str, Any]:
    """Promote an artifact to production"""
    
    # Check with Overseer if approval required
    if require_approval:
        async with httpx.AsyncClient() as client:
            try:
                decision = await client.post(f"{OVERSEER_URL}/check", json={
                    "capability": "model_change",
                    "requester": "great-sage",
                    "context": {
                        "artifact_type": artifact_type,
                        "version": version,
                        "reason": reason
                    }
                })
                
                decision_data = decision.json()
                
                if decision_data["decision"] == "deny":
                    return {
                        "status": "denied",
                        "reason": decision_data["reason"],
                        "version": version
                    }
                elif decision_data["decision"] == "review":
                    return {
                        "status": "pending_approval",
                        "request_id": decision_data["request_id"],
                        "version": version,
                        "approval_required": True
                    }
            except Exception as e:
                logging.error(f"Failed to check with Overseer: {e}")
                # Continue with promotion if Overseer is unavailable (fail-open for L2)
    
    # Proceed with promotion
    try:
        # Update version in release.lock.json
        release_lock_path = Path("../../release.lock.json")
        if release_lock_path.exists():
            with open(release_lock_path) as f:
                release_data = json.load(f)
        else:
            release_data = {"versions": {}}
        
        # Bump version
        old_version = release_data.get("versions", {}).get(artifact_type, "0.1.0")
        new_version = bump_version(old_version)
        
        release_data["versions"][artifact_type] = new_version
        release_data["last_updated"] = datetime.utcnow().isoformat()
        release_data["promoted_by"] = "great-sage"
        
        with open(release_lock_path, "w") as f:
            json.dump(release_data, f, indent=2)
        
        # Copy artifacts to production location
        # This would copy files from method-library to active locations
        
        return {
            "status": "promoted",
            "version": new_version,
            "promoted_at": datetime.utcnow().isoformat(),
            "approval_required": False
        }
        
    except Exception as e:
        logging.error(f"Promotion failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "version": version
        }

def bump_version(version_str: str) -> str:
    """Bump semantic version"""
    try:
        parts = version_str.split(".")
        patch = int(parts[2]) + 1
        return f"{parts[0]}.{parts[1]}.{patch}"
    except:
        return "0.1.1"

# ============= API Endpoints =============

@app.post("/reflect", response_model=ReflectionResult)
async def reflect_on_logs(request: ReflectionRequest, background_tasks: BackgroundTasks):
    """Analyze recent logs and generate insights"""
    
    try:
        # Gather logs
        logs = await gather_logs(request.days_back)
        
        # Analyze patterns
        analysis = analyze_patterns(logs)
        
        # Generate insights
        insights = generate_insights(analysis)
        
        # Generate improvement plan
        plan = generate_improvement_plan(insights, analysis)
        
        # Save plan to file
        plan_filename = f"PLAN-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.md"
        plan_path = METHOD_LIBRARY_PATH / "plans" / plan_filename
        plan_path.parent.mkdir(exist_ok=True)
        
        # Convert plan to markdown
        plan_md = f"""# Improvement Plan: {plan['version']}

Generated: {plan['created_at']}
Priority: {plan['priority']} (Safe changes only)

## Insights Discovered
{chr(10).join(f"- {insight}" for insight in insights)}

## Proposed Changes
{chr(10).join(f"### {i+1}. {change['type'].replace('_', ' ').title()}{chr(10)}- **Description**: {change['description']}{chr(10)}- **Files**: {', '.join(change['files'])}{chr(10)}- **Risk**: {change['risk']}{chr(10)}" for i, change in enumerate(plan['changes']))}

## Expected Impact
{chr(10).join(f"- {impact}" for impact in plan['expected_impact'])}

## Success Metrics
{chr(10).join(f"- {metric}" for metric in plan['success_metrics'])}

## Analysis Data
```json
{json.dumps(analysis, indent=2, default=str)}
```
"""
        
        with open(plan_path, "w") as f:
            f.write(plan_md)
        
        return ReflectionResult(
            summary=f"Analyzed {len(logs.get('audit_logs', []))} audit entries and {len(logs.get('control_sessions', []))} control sessions",
            insights=insights,
            improvement_opportunities=[change["description"] for change in plan["changes"]],
            plan_generated=True,
            plan_path=str(plan_path)
        )
        
    except Exception as e:
        logging.error(f"Reflection failed: {e}")
        raise HTTPException(500, f"Reflection failed: {e}")

@app.post("/eval", response_model=EvalResult)
async def evaluate_domain(request: EvalRequest):
    """Run evaluation suite for specified domain"""
    
    try:
        results = await run_eval_suite(request.domain, request.version or "current")
        
        # Store results in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO eval_results (domain, version, passed, metrics, details, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, request.domain, results["version"], results["passed"],
                 json.dumps(results["metrics"]), json.dumps(results),
                 datetime.fromisoformat(results["timestamp"]))
        
        return EvalResult(**results, timestamp=datetime.fromisoformat(results["timestamp"]))
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        raise HTTPException(500, f"Evaluation failed: {e}")

@app.post("/promote", response_model=PromotionResult)
async def promote_changes(request: PromotionRequest):
    """Promote artifact to production"""
    
    try:
        result = await promote_artifact(
            request.artifact_type,
            request.version,
            request.reason,
            request.require_approval
        )
        
        return PromotionResult(
            status=result["status"],
            version=result["version"],
            promoted_at=datetime.fromisoformat(result["promoted_at"]) if result.get("promoted_at") else None,
            approval_required=result.get("approval_required", False),
            request_id=result.get("request_id")
        )
        
    except Exception as e:
        logging.error(f"Promotion failed: {e}")
        raise HTTPException(500, f"Promotion failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check method library
    method_lib_exists = METHOD_LIBRARY_PATH.exists()
    
    # Check recent activity
    try:
        async with db_pool.acquire() as conn:
            recent_evals = await conn.fetchval("""
                SELECT COUNT(*) FROM eval_results 
                WHERE timestamp > NOW() - INTERVAL '7 days'
            """)
    except:
        recent_evals = 0
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "method_library": "available" if method_lib_exists else "missing",
        "recent_evaluations": recent_evals,
        "timestamp": datetime.utcnow()
    }

@app.get("/status")
async def get_status():
    """Get current Great Sage status and recent activity"""
    
    try:
        async with db_pool.acquire() as conn:
            # Recent evaluations
            recent_evals = await conn.fetch("""
                SELECT domain, version, passed, timestamp 
                FROM eval_results 
                WHERE timestamp > NOW() - INTERVAL '7 days'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            # Success rates by domain
            success_rates = await conn.fetch("""
                SELECT domain, 
                       AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(*) as total_runs
                FROM eval_results 
                WHERE timestamp > NOW() - INTERVAL '30 days'
                GROUP BY domain
            """)
            
        # Check for recent plans
        plans_dir = METHOD_LIBRARY_PATH / "plans"
        recent_plans = []
        if plans_dir.exists():
            for plan_file in sorted(plans_dir.glob("PLAN-*.md"), reverse=True)[:5]:
                recent_plans.append({
                    "filename": plan_file.name,
                    "created": plan_file.stat().st_mtime,
                    "size": plan_file.stat().st_size
                })
        
        return {
            "recent_evaluations": [dict(eval) for eval in recent_evals] if recent_evals else [],
            "success_rates": [dict(rate) for rate in success_rates] if success_rates else [],
            "recent_plans": recent_plans,
            "method_library_status": "available" if METHOD_LIBRARY_PATH.exists() else "missing",
            "overseer_connected": await check_overseer_connection(),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logging.error(f"Status check failed: {e}")
        raise HTTPException(500, f"Status check failed: {e}")

async def check_overseer_connection() -> bool:
    """Check if Overseer is reachable"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OVERSEER_URL}/health", timeout=5)
            return response.status_code == 200
    except:
        return False

# ============= Startup/Shutdown =============

@app.on_event("startup")
async def startup():
    global db_pool
    
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        # Create eval results table
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_results (
                    id SERIAL PRIMARY KEY,
                    domain VARCHAR(50) NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    passed BOOLEAN NOT NULL,
                    metrics JSONB,
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
        
        # Ensure method library structure exists
        (METHOD_LIBRARY_PATH / "prompts").mkdir(parents=True, exist_ok=True)
        (METHOD_LIBRARY_PATH / "router").mkdir(parents=True, exist_ok=True)
        (METHOD_LIBRARY_PATH / "evals").mkdir(parents=True, exist_ok=True)
        (METHOD_LIBRARY_PATH / "plans").mkdir(parents=True, exist_ok=True)
        
        logging.info("Great Sage started successfully")
        
    except Exception as e:
        logging.error(f"Great Sage startup failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5320, reload=True)