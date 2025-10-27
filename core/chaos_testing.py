"""
Rika Phase 3.5 Chaos Testing & Resilience
Fault injection, stress testing, and system resilience validation
"""
import asyncio
import random
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)

class ChaosType(str, Enum):
    """Types of chaos scenarios"""
    NETWORK_LATENCY = "network_latency"
    NETWORK_FAILURE = "network_failure"
    SERVICE_OVERLOAD = "service_overload"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_FAILURE = "disk_failure"
    API_ERRORS = "api_errors"
    TIMEOUT_ERRORS = "timeout_errors"
    RANDOM_CRASHES = "random_crashes"

class ChaosScenario(BaseModel):
    """Chaos testing scenario"""
    id: str
    name: str
    chaos_type: ChaosType
    severity: float  # 0.1 to 1.0
    duration: int  # seconds
    target_components: List[str]
    enabled: bool = True
    probability: float = 0.1  # 10% chance
    description: str = ""

class ResilienceMetrics(BaseModel):
    """System resilience metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    recovery_time: float = 0.0
    availability: float = 100.0
    last_incident: Optional[datetime] = None

class ChaosEngine:
    """Chaos engineering and resilience testing engine"""
    
    def __init__(self):
        self.scenarios: Dict[str, ChaosScenario] = {}
        self.active_chaos: Dict[str, Dict[str, Any]] = {}
        self.metrics = ResilienceMetrics()
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        
        self._initialize_scenarios()
        self._initialize_circuit_breakers()
    
    def _initialize_scenarios(self):
        """Initialize predefined chaos scenarios"""
        scenarios = [
            ChaosScenario(
                id="network_lag",
                name="Network Latency Injection",
                chaos_type=ChaosType.NETWORK_LATENCY,
                severity=0.3,
                duration=30,
                target_components=["api", "voice", "proxy"],
                description="Inject 100-500ms latency into network calls"
            ),
            ChaosScenario(
                id="api_errors",
                name="Random API Errors",
                chaos_type=ChaosType.API_ERRORS,
                severity=0.2,
                duration=60,
                target_components=["chat", "voice", "knowledge"],
                description="Randomly return 500/503 errors from APIs"
            ),
            ChaosScenario(
                id="service_overload",
                name="Service Overload",
                chaos_type=ChaosType.SERVICE_OVERLOAD,
                severity=0.5,
                duration=45,
                target_components=["great_sage", "agents"],
                description="Simulate high CPU/memory usage"
            ),
            ChaosScenario(
                id="timeout_chaos",
                name="Timeout Failures",
                chaos_type=ChaosType.TIMEOUT_ERRORS,
                severity=0.4,
                duration=20,
                target_components=["proxy", "knowledge"],
                description="Force request timeouts"
            )
        ]
        
        for scenario in scenarios:
            self.scenarios[scenario.id] = scenario
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for resilience"""
        components = ["chat", "voice", "proxy", "knowledge", "great_sage"]
        
        for component in components:
            self.circuit_breakers[component] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "failure_threshold": 5,
                "recovery_timeout": 30,
                "last_failure": None,
                "total_requests": 0,
                "successful_requests": 0
            }
    
    async def start_chaos_testing(self, duration: int = 300):
        """Start chaos testing for specified duration"""
        if self.is_running:
            logger.warning("Chaos testing already running")
            return
        
        self.is_running = True
        start_time = time.time()
        
        logger.info(f"Starting chaos testing for {duration} seconds")
        
        try:
            while time.time() - start_time < duration and self.is_running:
                # Randomly trigger chaos scenarios
                for scenario_id, scenario in self.scenarios.items():
                    if scenario.enabled and random.random() < scenario.probability:
                        await self._trigger_chaos(scenario)
                
                # Update metrics
                await self._update_metrics()
                
                # Check circuit breakers
                await self._check_circuit_breakers()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        finally:
            self.is_running = False
            await self._cleanup_chaos()
            logger.info("Chaos testing completed")
    
    async def stop_chaos_testing(self):
        """Stop chaos testing"""
        self.is_running = False
        await self._cleanup_chaos()
    
    async def _trigger_chaos(self, scenario: ChaosScenario):
        """Trigger a specific chaos scenario"""
        if scenario.id in self.active_chaos:
            return  # Already active
        
        logger.info(f"Triggering chaos: {scenario.name}")
        
        chaos_data = {
            "scenario": scenario,
            "start_time": time.time(),
            "end_time": time.time() + scenario.duration,
            "active": True
        }
        
        self.active_chaos[scenario.id] = chaos_data
        
        # Schedule cleanup
        asyncio.create_task(self._schedule_chaos_cleanup(scenario.id, scenario.duration))
    
    async def _schedule_chaos_cleanup(self, scenario_id: str, duration: int):
        """Schedule cleanup of chaos scenario"""
        await asyncio.sleep(duration)
        if scenario_id in self.active_chaos:
            del self.active_chaos[scenario_id]
            logger.info(f"Chaos scenario {scenario_id} completed")
    
    async def _cleanup_chaos(self):
        """Clean up all active chaos scenarios"""
        for scenario_id in list(self.active_chaos.keys()):
            del self.active_chaos[scenario_id]
        logger.info("All chaos scenarios cleaned up")
    
    def should_inject_chaos(self, component: str, operation: str) -> Dict[str, Any]:
        """Check if chaos should be injected for a component/operation"""
        for chaos_id, chaos_data in self.active_chaos.items():
            scenario = chaos_data["scenario"]
            
            if component in scenario.target_components:
                return {
                    "inject": True,
                    "type": scenario.chaos_type,
                    "severity": scenario.severity,
                    "scenario_id": chaos_id
                }
        
        return {"inject": False}
    
    async def inject_network_latency(self, severity: float):
        """Inject network latency"""
        latency = severity * 500  # Up to 500ms delay
        await asyncio.sleep(latency / 1000)
    
    def inject_api_error(self, severity: float) -> bool:
        """Check if API error should be injected"""
        return random.random() < severity
    
    async def _update_metrics(self):
        """Update resilience metrics"""
        # Calculate current metrics
        total = sum(cb["total_requests"] for cb in self.circuit_breakers.values())
        successful = sum(cb["successful_requests"] for cb in self.circuit_breakers.values())
        
        self.metrics.total_requests = total
        self.metrics.successful_requests = successful
        self.metrics.failed_requests = total - successful
        self.metrics.error_rate = (total - successful) / total if total > 0 else 0
        self.metrics.availability = (successful / total * 100) if total > 0 else 100
    
    async def _check_circuit_breakers(self):
        """Check and update circuit breaker states"""
        current_time = time.time()
        
        for component, breaker in self.circuit_breakers.items():
            if breaker["state"] == "open":
                # Check if recovery timeout has passed
                if (breaker["last_failure"] and 
                    current_time - breaker["last_failure"] > breaker["recovery_timeout"]):
                    breaker["state"] = "half_open"
                    logger.info(f"Circuit breaker for {component} moved to half-open")
            
            elif breaker["state"] == "half_open":
                # Reset failure count for testing
                breaker["failure_count"] = 0
    
    def record_request(self, component: str, success: bool, response_time: float):
        """Record request result for circuit breaker"""
        if component not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[component]
        breaker["total_requests"] += 1
        
        if success:
            breaker["successful_requests"] += 1
            if breaker["state"] == "half_open":
                breaker["state"] = "closed"
                breaker["failure_count"] = 0
                logger.info(f"Circuit breaker for {component} closed")
        else:
            breaker["failure_count"] += 1
            breaker["last_failure"] = time.time()
            
            if breaker["failure_count"] >= breaker["failure_threshold"]:
                breaker["state"] = "open"
                logger.warning(f"Circuit breaker for {component} opened")
    
    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open for component"""
        return (component in self.circuit_breakers and 
                self.circuit_breakers[component]["state"] == "open")
    
    async def run_stress_test(self, target_url: str, concurrent_requests: int = 50, duration: int = 60):
        """Run stress test against target URL"""
        logger.info(f"Starting stress test: {concurrent_requests} concurrent requests for {duration}s")
        
        start_time = time.time()
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
        async def make_request(session: aiohttp.ClientSession):
            try:
                request_start = time.time()
                async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    await response.text()
                    response_time = time.time() - request_start
                    
                    results["total_requests"] += 1
                    results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1
                        
            except Exception as e:
                results["total_requests"] += 1
                results["failed_requests"] += 1
                results["errors"].append(str(e))
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                tasks = [make_request(session) for _ in range(concurrent_requests)]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)  # 1 second between bursts
        
        # Calculate statistics
        if results["response_times"]:
            avg_response_time = sum(results["response_times"]) / len(results["response_times"])
            max_response_time = max(results["response_times"])
            min_response_time = min(results["response_times"])
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        return {
            "duration": duration,
            "concurrent_requests": concurrent_requests,
            "total_requests": results["total_requests"],
            "successful_requests": results["successful_requests"],
            "failed_requests": results["failed_requests"],
            "success_rate": results["successful_requests"] / results["total_requests"] if results["total_requests"] > 0 else 0,
            "average_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "errors_sample": results["errors"][:10]  # First 10 errors
        }
    
    def get_chaos_status(self) -> Dict[str, Any]:
        """Get current chaos testing status"""
        return {
            "is_running": self.is_running,
            "active_scenarios": len(self.active_chaos),
            "scenarios": {
                scenario_id: {
                    "name": chaos_data["scenario"].name,
                    "type": chaos_data["scenario"].chaos_type.value,
                    "severity": chaos_data["scenario"].severity,
                    "remaining_time": max(0, chaos_data["end_time"] - time.time())
                }
                for scenario_id, chaos_data in self.active_chaos.items()
            },
            "circuit_breakers": {
                component: {
                    "state": breaker["state"],
                    "failure_count": breaker["failure_count"],
                    "total_requests": breaker["total_requests"],
                    "success_rate": breaker["successful_requests"] / breaker["total_requests"] if breaker["total_requests"] > 0 else 0
                }
                for component, breaker in self.circuit_breakers.items()
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "error_rate": self.metrics.error_rate,
                "availability": self.metrics.availability
            }
        }
    
    def get_resilience_report(self) -> Dict[str, Any]:
        """Generate comprehensive resilience report"""
        return {
            "test_summary": {
                "total_scenarios": len(self.scenarios),
                "active_scenarios": len(self.active_chaos),
                "is_testing_active": self.is_running
            },
            "system_health": {
                "overall_availability": self.metrics.availability,
                "error_rate": self.metrics.error_rate,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests
            },
            "circuit_breakers": self.circuit_breakers,
            "recommendations": self._generate_recommendations(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate resilience recommendations"""
        recommendations = []
        
        if self.metrics.error_rate > 0.1:
            recommendations.append("High error rate detected - consider implementing retry mechanisms")
        
        if self.metrics.availability < 99.0:
            recommendations.append("Availability below 99% - review system architecture for single points of failure")
        
        open_breakers = [comp for comp, breaker in self.circuit_breakers.items() if breaker["state"] == "open"]
        if open_breakers:
            recommendations.append(f"Circuit breakers open for: {', '.join(open_breakers)} - investigate root causes")
        
        if not recommendations:
            recommendations.append("System showing good resilience - continue monitoring")
        
        return recommendations

# Global chaos engine instance
chaos_engine = ChaosEngine()