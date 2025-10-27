# phase3/eval/evaluator.py
# Evaluation Harness for Rika Meta-Cortex

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import httpx
import asyncpg
from pydantic import BaseModel, Field
import structlog
import minio
from minio import Minio

# Configure logging
logger = structlog.get_logger()

class EvalTask(BaseModel):
    """Single evaluation task"""
    task_id: str
    domain: str  # presence_query, link_command, retrieval_qa
    input_data: Dict
    expected_output: Dict
    metadata: Dict = Field(default_factory=dict)

class EvalResult(BaseModel):
    """Result of a single evaluation"""
    task_id: str
    domain: str
    success: bool
    actual_output: Dict
    expected_output: Dict
    metrics: Dict
    latency_ms: float
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvalSuite(BaseModel):
    """Collection of evaluation tasks"""
    suite_id: str
    name: str
    description: str
    domains: List[str]
    tasks: List[EvalTask]
    metadata: Dict = Field(default_factory=dict)

class EvaluationRunner:
    """Main evaluation harness"""
    
    def __init__(self, db_url: str, minio_config: Dict, core_api_url: str):
        self.db_url = db_url
        self.core_api_url = core_api_url
        self.minio_client = Minio(
            minio_config["url"].replace("http://", "").replace("https://", ""),
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["url"].startswith("https://")
        )
        self._ensure_bucket("rika-eval-results")
    
    def _ensure_bucket(self, bucket_name: str):
        """Ensure MinIO bucket exists"""
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
        except Exception as e:
            logger.warning(f"MinIO bucket setup failed: {e}")
    
    async def load_gold_tasks(self, tasks_dir: str) -> Dict[str, EvalSuite]:
        """Load gold standard tasks from directory"""
        suites = {}
        tasks_path = Path(tasks_dir)
        
        for domain_dir in tasks_path.iterdir():
            if not domain_dir.is_dir():
                continue
                
            domain = domain_dir.name
            suite_file = domain_dir / "suite.json"
            
            if not suite_file.exists():
                logger.warning(f"No suite.json found in {domain_dir}")
                continue
            
            try:
                with open(suite_file, 'r', encoding='utf-8') as f:
                    suite_data = json.load(f)
                
                suite = EvalSuite(**suite_data)
                suites[domain] = suite
                logger.info(f"Loaded {len(suite.tasks)} tasks for domain: {domain}")
                
            except Exception as e:
                logger.error(f"Failed to load suite from {suite_file}: {e}")
        
        return suites
    
    async def run_presence_query_task(self, task: EvalTask) -> EvalResult:
        """Evaluate presence query task"""
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.core_api_url}/presence/query",
                    json=task.input_data
                )
                response.raise_for_status()
                actual_output = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Calculate metrics
            expected = task.expected_output
            metrics = self._calculate_presence_metrics(actual_output, expected)
            
            success = metrics["accuracy"] >= 0.8  # 80% accuracy threshold
            
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=success,
                actual_output=actual_output,
                expected_output=expected,
                metrics=metrics,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=False,
                actual_output={},
                expected_output=task.expected_output,
                metrics={"accuracy": 0.0, "error_rate": 1.0},
                latency_ms=latency_ms,
                error=str(e)
            )
    
    async def run_link_command_task(self, task: EvalTask) -> EvalResult:
        """Evaluate link command task"""
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.core_api_url}/link/execute",
                    json=task.input_data
                )
                response.raise_for_status()
                actual_output = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Calculate metrics
            expected = task.expected_output
            metrics = self._calculate_link_metrics(actual_output, expected)
            
            success = metrics["command_success"] and metrics["accuracy"] >= 0.9
            
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=success,
                actual_output=actual_output,
                expected_output=expected,
                metrics=metrics,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=False,
                actual_output={},
                expected_output=task.expected_output,
                metrics={"command_success": False, "accuracy": 0.0},
                latency_ms=latency_ms,
                error=str(e)
            )
    
    async def run_retrieval_qa_task(self, task: EvalTask) -> EvalResult:
        """Evaluate retrieval QA task"""
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.core_api_url}/retrieval/query",
                    json=task.input_data
                )
                response.raise_for_status()
                actual_output = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Calculate metrics
            expected = task.expected_output
            metrics = self._calculate_retrieval_metrics(actual_output, expected)
            
            success = metrics["accuracy"] >= 0.7 and metrics["hallucination_rate"] <= 0.1
            
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=success,
                actual_output=actual_output,
                expected_output=expected,
                metrics=metrics,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=False,
                actual_output={},
                expected_output=task.expected_output,
                metrics={"accuracy": 0.0, "hallucination_rate": 1.0},
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def _calculate_presence_metrics(self, actual: Dict, expected: Dict) -> Dict:
        """Calculate presence query specific metrics"""
        metrics = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0
        }
        
        # Check if presence status matches
        actual_present = actual.get("present", False)
        expected_present = expected.get("present", False)
        
        if actual_present == expected_present:
            metrics["accuracy"] = 1.0
        
        # Calculate precision/recall for detected entities
        actual_entities = set(actual.get("entities", []))
        expected_entities = set(expected.get("entities", []))
        
        if expected_entities:
            intersection = actual_entities.intersection(expected_entities)
            metrics["precision"] = len(intersection) / max(len(actual_entities), 1)
            metrics["recall"] = len(intersection) / len(expected_entities)
            
            if metrics["precision"] + metrics["recall"] > 0:
                metrics["f1_score"] = 2 * (metrics["precision"] * metrics["recall"]) / (metrics["precision"] + metrics["recall"])
        
        return metrics
    
    def _calculate_link_metrics(self, actual: Dict, expected: Dict) -> Dict:
        """Calculate link command specific metrics"""
        metrics = {
            "command_success": actual.get("success", False),
            "accuracy": 0.0,
            "response_relevance": 0.0
        }
        
        # Check command execution success
        if actual.get("success") == expected.get("success"):
            metrics["accuracy"] += 0.5
        
        # Check response content (basic string similarity)
        actual_response = str(actual.get("response", "")).lower()
        expected_response = str(expected.get("response", "")).lower()
        
        if expected_response in actual_response or actual_response in expected_response:
            metrics["response_relevance"] = 1.0
            metrics["accuracy"] += 0.5
        
        return metrics
    
    def _calculate_retrieval_metrics(self, actual: Dict, expected: Dict) -> Dict:
        """Calculate retrieval QA specific metrics"""
        metrics = {
            "accuracy": 0.0,
            "hallucination_rate": 0.0,
            "source_citation_rate": 0.0,
            "relevance_score": 0.0
        }
        
        # Check answer accuracy (basic keyword matching)
        actual_answer = str(actual.get("answer", "")).lower()
        expected_keywords = expected.get("keywords", [])
        
        if expected_keywords:
            keyword_matches = sum(1 for kw in expected_keywords if kw.lower() in actual_answer)
            metrics["accuracy"] = keyword_matches / len(expected_keywords)
        
        # Check for source citations
        actual_sources = actual.get("sources", [])
        if actual_sources:
            metrics["source_citation_rate"] = 1.0
        
        # Hallucination detection (basic check for made-up facts)
        if actual.get("confidence", 1.0) < 0.5:
            metrics["hallucination_rate"] = 0.2
        
        # Calculate overall relevance
        metrics["relevance_score"] = (metrics["accuracy"] + metrics["source_citation_rate"]) / 2
        
        return metrics
    
    async def run_task(self, task: EvalTask) -> EvalResult:
        """Run a single evaluation task"""
        domain_runners = {
            "presence_query": self.run_presence_query_task,
            "link_command": self.run_link_command_task,
            "retrieval_qa": self.run_retrieval_qa_task
        }
        
        runner = domain_runners.get(task.domain)
        if not runner:
            return EvalResult(
                task_id=task.task_id,
                domain=task.domain,
                success=False,
                actual_output={},
                expected_output=task.expected_output,
                metrics={},
                latency_ms=0.0,
                error=f"Unknown domain: {task.domain}"
            )
        
        return await runner(task)
    
    async def run_suite(self, suite: EvalSuite, max_workers: int = 4) -> List[EvalResult]:
        """Run an entire evaluation suite"""
        logger.info(f"Running evaluation suite: {suite.name} ({len(suite.tasks)} tasks)")
        
        # Run tasks with concurrency limit
        semaphore = asyncio.Semaphore(max_workers)
        
        async def run_task_with_semaphore(task):
            async with semaphore:
                return await self.run_task(task)
        
        tasks = [run_task_with_semaphore(task) for task in suite.tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {suite.tasks[i].task_id} failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def save_results(self, run_id: str, suite_name: str, results: List[EvalResult]):
        """Save evaluation results to PostgreSQL and MinIO"""
        # Save to MinIO
        results_json = json.dumps([r.dict() for r in results], indent=2, default=str)
        
        try:
            self.minio_client.put_object(
                bucket_name="rika-eval-results",
                object_name=f"{run_id}/{suite_name}_results.json",
                data=results_json.encode(),
                length=len(results_json.encode()),
                content_type="application/json"
            )
            logger.info(f"Results saved to MinIO: {run_id}/{suite_name}_results.json")
        except Exception as e:
            logger.error(f"Failed to save results to MinIO: {e}")
        
        # Save to PostgreSQL
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Create table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_results (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    run_id TEXT NOT NULL,
                    suite_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    metrics JSONB NOT NULL,
                    latency_ms REAL NOT NULL,
                    error TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Insert results
            for result in results:
                await conn.execute("""
                    INSERT INTO eval_results 
                    (run_id, suite_name, task_id, domain, success, metrics, latency_ms, error, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                run_id, suite_name, result.task_id, result.domain, result.success,
                json.dumps(result.metrics), result.latency_ms, result.error, result.timestamp)
            
            await conn.close()
            logger.info(f"Results saved to PostgreSQL: {len(results)} records")
            
        except Exception as e:
            logger.error(f"Failed to save results to PostgreSQL: {e}")
    
    def calculate_suite_summary(self, results: List[EvalResult]) -> Dict:
        """Calculate summary metrics for a suite run"""
        if not results:
            return {}
        
        total_tasks = len(results)
        successful_tasks = sum(1 for r in results if r.success)
        failed_tasks = total_tasks - successful_tasks
        
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        latencies.sort()
        
        p95_latency = latencies[int(0.95 * len(latencies))] if latencies else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Domain-specific metrics
        domain_metrics = {}
        for result in results:
            domain = result.domain
            if domain not in domain_metrics:
                domain_metrics[domain] = []
            domain_metrics[domain].append(result)
        
        domain_summaries = {}
        for domain, domain_results in domain_metrics.items():
            domain_success_rate = sum(1 for r in domain_results if r.success) / len(domain_results)
            
            # Calculate average metrics
            avg_metrics = {}
            if domain_results:
                for metric_name in domain_results[0].metrics.keys():
                    values = [r.metrics.get(metric_name, 0) for r in domain_results if isinstance(r.metrics.get(metric_name), (int, float))]
                    avg_metrics[metric_name] = sum(values) / len(values) if values else 0
            
            domain_summaries[domain] = {
                "success_rate": domain_success_rate,
                "task_count": len(domain_results),
                "avg_metrics": avg_metrics
            }
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "domain_summaries": domain_summaries,
            "timestamp": datetime.utcnow().isoformat()
        }