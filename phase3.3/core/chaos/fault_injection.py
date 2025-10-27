"""
Chaos Testing - Fault Injection System
Advanced fault injection and resilience testing for Rika agents

Phase 3.3 Enhancement:
- Configurable fault injection scenarios
- Circuit breaker pattern implementation
- Intelligent backoff strategies
- Auto-recovery mechanisms
- Resilience scoring and metrics
"""

import asyncio
import logging
import json
import random
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import time
import threading
from collections import defaultdict, deque
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaultType(Enum):
    """Types of faults that can be injected"""
    NETWORK_LATENCY = "network_latency"
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_DISCONNECT = "network_disconnect"
    NETWORK_PACKET_LOSS = "network_packet_loss"
    
    SERVICE_UNAVAILABLE = "service_unavailable"
    SERVICE_SLOW_RESPONSE = "service_slow_response"
    SERVICE_ERROR_RESPONSE = "service_error_response"
    
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_FULL = "disk_full"
    CPU_SPIKE = "cpu_spike"
    
    DATABASE_CONNECTION_FAILURE = "database_connection_failure"
    DATABASE_LOCK_TIMEOUT = "database_lock_timeout"
    DATABASE_SLOW_QUERY = "database_slow_query"
    
    FILE_SYSTEM_ERROR = "file_system_error"
    PERMISSION_DENIED = "permission_denied"
    FILE_CORRUPTION = "file_corruption"
    
    DEPENDENCY_FAILURE = "dependency_failure"
    CONFIGURATION_ERROR = "configuration_error"
    SECURITY_ERROR = "security_error"

class RecoveryStrategy(Enum):
    """Recovery strategies for fault tolerance"""
    RETRY_EXPONENTIAL_BACKOFF = "retry_exponential_backoff"
    RETRY_LINEAR_BACKOFF = "retry_linear_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER = "failover"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    RESTART_COMPONENT = "restart_component"
    ESCALATE_TO_HUMAN = "escalate_to_human"

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"    # Normal operation
    OPEN = "open"        # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class FaultScenario:
    """Configuration for a fault injection scenario"""
    scenario_id: str
    name: str
    description: str
    fault_type: FaultType
    target_agents: List[str]  # Agent IDs or patterns
    target_operations: List[str]  # Operation names or patterns
    
    # Fault parameters
    probability: float  # 0.0 to 1.0
    duration_min: float  # seconds
    duration_max: float  # seconds
    severity: float  # 0.0 to 1.0
    
    # Timing
    schedule: Optional[Dict[str, Any]] = None  # When to activate
    max_activations: Optional[int] = None
    activation_count: int = 0
    
    # Recovery
    recovery_strategies: List[RecoveryStrategy] = None
    auto_recovery: bool = True
    recovery_timeout: float = 30.0  # seconds
    
    # Monitoring
    created_at: datetime = None
    last_activated: Optional[datetime] = None
    is_active: bool = False
    
    def __post_init__(self):
        if self.recovery_strategies is None:
            self.recovery_strategies = [RecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF]
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class FaultInjectionEvent:
    """Record of a fault injection event"""
    event_id: str
    scenario_id: str
    agent_id: str
    operation: str
    fault_type: FaultType
    
    # Timing
    injected_at: datetime
    duration: float
    resolved_at: Optional[datetime] = None
    
    # Impact
    success_before: bool = True  # Was operation succeeding before?
    recovery_attempts: int = 0
    recovery_strategies_used: List[RecoveryStrategy] = None
    recovery_successful: bool = False
    
    # Metrics
    impact_score: float = 0.0  # 0.0 to 1.0
    resilience_score: float = 0.0  # 0.0 to 1.0
    context_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.recovery_strategies_used is None:
            self.recovery_strategies_used = []
        if self.context_data is None:
            self.context_data = {}

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before trying half-open
    
    # Rolling window for failure counting
    window_size: int = 100  # Number of recent calls to consider
    minimum_calls: int = 10  # Minimum calls before circuit can open

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.call_history = deque(maxlen=config.window_size)
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Tuple[Any, bool]:
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result, True
                
            except Exception as e:
                self._record_failure()
                raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout

    def _record_success(self):
        """Record a successful call"""
        self.call_history.append(True)
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} CLOSED after recovery")

    def _record_failure(self):
        """Record a failed call"""
        self.call_history.append(False)
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            logger.warning(f"Circuit breaker {self.name} OPEN again after failure in HALF_OPEN")
            return
        
        # Count failures in recent window
        recent_failures = sum(1 for call in self.call_history if not call)
        total_calls = len(self.call_history)
        
        if (total_calls >= self.config.minimum_calls and 
            recent_failures >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {self.name} OPENED due to failures: {recent_failures}/{total_calls}")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        recent_calls = len(self.call_history)
        recent_failures = sum(1 for call in self.call_history if not call) if recent_calls > 0 else 0
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "recent_calls": recent_calls,
            "recent_failures": recent_failures,
            "failure_rate": recent_failures / recent_calls if recent_calls > 0 else 0,
            "last_failure_time": self.last_failure_time
        }

class RetryStrategy:
    """Configurable retry strategies with backoff"""
    
    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Exponential backoff with jitter"""
        delay = min(base_delay * (2 ** attempt), max_delay)
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.5, 1.5)
        return delay * jitter

    @staticmethod
    def linear_backoff(attempt: int, base_delay: float = 1.0, increment: float = 1.0) -> float:
        """Linear backoff with jitter"""
        delay = base_delay + (attempt * increment)
        jitter = random.uniform(0.8, 1.2)
        return delay * jitter

    @staticmethod
    def fixed_delay(attempt: int, delay: float = 1.0) -> float:
        """Fixed delay between retries"""
        return delay

    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_attempts: int = 3,
        backoff_strategy: str = "exponential",
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple = (Exception,)
    ) -> Any:
        """Retry function with configurable backoff strategy"""
        
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
                    
            except exceptions as e:
                if attempt == max_attempts - 1:
                    raise e
                
                # Calculate delay based on strategy
                if backoff_strategy == "exponential":
                    delay = RetryStrategy.exponential_backoff(attempt, base_delay, max_delay)
                elif backoff_strategy == "linear":
                    delay = RetryStrategy.linear_backoff(attempt, base_delay, base_delay)
                else:
                    delay = RetryStrategy.fixed_delay(attempt, base_delay)
                
                logger.info(f"Retry attempt {attempt + 1}/{max_attempts} after {delay:.2f}s delay")
                await asyncio.sleep(delay)
        
        raise Exception(f"All {max_attempts} retry attempts failed")

class FaultInjector:
    """Main fault injection engine"""
    
    def __init__(self):
        self.scenarios: Dict[str, FaultScenario] = {}
        self.active_faults: Dict[str, FaultInjectionEvent] = {}
        self.fault_history: List[FaultInjectionEvent] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Monitoring
        self.resilience_metrics = defaultdict(list)
        self.agent_health_scores = defaultdict(float)
        
        # Control
        self.enabled = True
        self._injection_lock = asyncio.Lock()

    def add_scenario(self, scenario: FaultScenario):
        """Add a fault injection scenario"""
        self.scenarios[scenario.scenario_id] = scenario
        logger.info(f"Added fault scenario: {scenario.name}")

    def remove_scenario(self, scenario_id: str):
        """Remove a fault injection scenario"""
        if scenario_id in self.scenarios:
            del self.scenarios[scenario_id]
            logger.info(f"Removed fault scenario: {scenario_id}")

    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]

    async def should_inject_fault(self, agent_id: str, operation: str) -> Optional[FaultScenario]:
        """Determine if a fault should be injected for this operation"""
        if not self.enabled:
            return None
        
        async with self._injection_lock:
            applicable_scenarios = []
            
            for scenario in self.scenarios.values():
                if self._scenario_matches(scenario, agent_id, operation):
                    if await self._should_activate_scenario(scenario):
                        applicable_scenarios.append(scenario)
            
            if applicable_scenarios:
                # Select scenario based on probability
                for scenario in applicable_scenarios:
                    if random.random() < scenario.probability:
                        return scenario
        
        return None

    def _scenario_matches(self, scenario: FaultScenario, agent_id: str, operation: str) -> bool:
        """Check if scenario matches the current context"""
        # Check agent targeting
        agent_matches = False
        for target in scenario.target_agents:
            if target == "*" or target == agent_id or agent_id.startswith(target):
                agent_matches = True
                break
        
        if not agent_matches:
            return False
        
        # Check operation targeting
        operation_matches = False
        for target in scenario.target_operations:
            if target == "*" or target == operation or operation.startswith(target):
                operation_matches = True
                break
        
        return operation_matches

    async def _should_activate_scenario(self, scenario: FaultScenario) -> bool:
        """Check if scenario should be activated based on schedule and limits"""
        # Check activation limit
        if (scenario.max_activations is not None and 
            scenario.activation_count >= scenario.max_activations):
            return False
        
        # Check if already active
        if scenario.is_active:
            return False
        
        # Check schedule if specified
        if scenario.schedule:
            if not self._check_schedule(scenario.schedule):
                return False
        
        return True

    def _check_schedule(self, schedule: Dict[str, Any]) -> bool:
        """Check if current time matches schedule"""
        now = datetime.utcnow()
        
        # Check time ranges
        if "hours" in schedule:
            if now.hour not in schedule["hours"]:
                return False
        
        if "days" in schedule:
            if now.weekday() not in schedule["days"]:
                return False
        
        if "date_range" in schedule:
            start = datetime.fromisoformat(schedule["date_range"]["start"])
            end = datetime.fromisoformat(schedule["date_range"]["end"])
            if not (start <= now <= end):
                return False
        
        return True

    async def inject_fault(self, scenario: FaultScenario, agent_id: str, operation: str) -> FaultInjectionEvent:
        """Inject a fault based on scenario"""
        event_id = self._generate_id("fault")
        duration = random.uniform(scenario.duration_min, scenario.duration_max)
        
        event = FaultInjectionEvent(
            event_id=event_id,
            scenario_id=scenario.scenario_id,
            agent_id=agent_id,
            operation=operation,
            fault_type=scenario.fault_type,
            injected_at=datetime.utcnow(),
            duration=duration,
            context_data={
                "scenario_name": scenario.name,
                "severity": scenario.severity,
                "recovery_strategies": [s.value for s in scenario.recovery_strategies]
            }
        )
        
        # Mark scenario as active
        scenario.is_active = True
        scenario.activation_count += 1
        scenario.last_activated = datetime.utcnow()
        
        # Track active fault
        self.active_faults[event_id] = event
        
        # Schedule fault resolution
        asyncio.create_task(self._resolve_fault_after_duration(event))
        
        logger.warning(f"Injected fault: {scenario.fault_type.value} for {agent_id}:{operation}")
        return event

    async def _resolve_fault_after_duration(self, event: FaultInjectionEvent):
        """Resolve fault after its duration"""
        await asyncio.sleep(event.duration)
        await self.resolve_fault(event.event_id)

    async def resolve_fault(self, event_id: str, recovery_successful: bool = True):
        """Resolve an active fault"""
        if event_id not in self.active_faults:
            return
        
        event = self.active_faults[event_id]
        event.resolved_at = datetime.utcnow()
        event.recovery_successful = recovery_successful
        
        # Calculate resilience score
        event.resilience_score = self._calculate_resilience_score(event)
        
        # Mark scenario as inactive
        scenario = self.scenarios.get(event.scenario_id)
        if scenario:
            scenario.is_active = False
        
        # Move to history
        self.fault_history.append(event)
        del self.active_faults[event_id]
        
        # Update metrics
        self._update_resilience_metrics(event)
        
        logger.info(f"Resolved fault: {event.event_id} (recovery: {recovery_successful})")

    def _calculate_resilience_score(self, event: FaultInjectionEvent) -> float:
        """Calculate resilience score for the fault event"""
        score = 0.0
        
        # Base score for successful recovery
        if event.recovery_successful:
            score += 0.5
        
        # Bonus for fast recovery
        if event.resolved_at and event.injected_at:
            recovery_time = (event.resolved_at - event.injected_at).total_seconds()
            if recovery_time < event.duration * 0.5:
                score += 0.2  # Quick recovery
            elif recovery_time < event.duration:
                score += 0.1  # Reasonable recovery
        
        # Penalty for multiple recovery attempts
        if event.recovery_attempts > 1:
            penalty = min(0.3, event.recovery_attempts * 0.1)
            score -= penalty
        
        # Bonus for using appropriate recovery strategies
        if len(event.recovery_strategies_used) > 0:
            score += 0.2
        
        return max(0.0, min(1.0, score))

    def _update_resilience_metrics(self, event: FaultInjectionEvent):
        """Update resilience metrics for agent"""
        agent_id = event.agent_id
        
        # Add to metrics history
        self.resilience_metrics[agent_id].append({
            "timestamp": event.injected_at,
            "fault_type": event.fault_type.value,
            "resilience_score": event.resilience_score,
            "recovery_time": (event.resolved_at - event.injected_at).total_seconds() if event.resolved_at else 0,
            "recovery_attempts": event.recovery_attempts
        })
        
        # Update overall health score (weighted average)
        recent_scores = [m["resilience_score"] for m in self.resilience_metrics[agent_id][-10:]]
        self.agent_health_scores[agent_id] = sum(recent_scores) / len(recent_scores)

    async def execute_with_fault_tolerance(
        self,
        func: Callable,
        agent_id: str,
        operation: str,
        recovery_strategies: Optional[List[RecoveryStrategy]] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with automatic fault tolerance"""
        
        # Check for fault injection
        scenario = await self.should_inject_fault(agent_id, operation)
        
        if scenario:
            event = await self.inject_fault(scenario, agent_id, operation)
            
            # Apply fault effects
            await self._apply_fault_effects(scenario.fault_type, scenario.severity)
            
            # Attempt recovery
            if scenario.auto_recovery:
                return await self._attempt_recovery(
                    func, event, recovery_strategies or scenario.recovery_strategies, 
                    *args, **kwargs
                )
            else:
                # Simulate failure without recovery
                raise Exception(f"Simulated fault: {scenario.fault_type.value}")
        
        # Normal execution
        return await self._execute_safely(func, *args, **kwargs)

    async def _apply_fault_effects(self, fault_type: FaultType, severity: float):
        """Apply the effects of a specific fault type"""
        
        if fault_type == FaultType.NETWORK_LATENCY:
            delay = severity * 5.0  # Up to 5 seconds delay
            await asyncio.sleep(delay)
            
        elif fault_type == FaultType.NETWORK_TIMEOUT:
            # Simulate timeout by waiting longer than expected
            await asyncio.sleep(severity * 30.0)  # Up to 30 seconds
            raise TimeoutError("Network timeout")
            
        elif fault_type == FaultType.SERVICE_UNAVAILABLE:
            raise ConnectionError("Service unavailable")
            
        elif fault_type == FaultType.MEMORY_PRESSURE:
            # Simulate memory pressure (in real implementation, would actually consume memory)
            await asyncio.sleep(severity * 2.0)
            
        elif fault_type == FaultType.DATABASE_CONNECTION_FAILURE:
            raise ConnectionError("Database connection failed")
            
        elif fault_type == FaultType.PERMISSION_DENIED:
            raise PermissionError("Access denied")
            
        # Add more fault types as needed

    async def _attempt_recovery(
        self,
        func: Callable,
        event: FaultInjectionEvent,
        strategies: List[RecoveryStrategy],
        *args,
        **kwargs
    ) -> Any:
        """Attempt recovery using specified strategies"""
        
        for strategy in strategies:
            try:
                event.recovery_attempts += 1
                event.recovery_strategies_used.append(strategy)
                
                if strategy == RecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF:
                    result = await RetryStrategy.retry_with_backoff(
                        lambda: self._execute_safely(func, *args, **kwargs),
                        max_attempts=3,
                        backoff_strategy="exponential"
                    )
                    event.recovery_successful = True
                    return result
                    
                elif strategy == RecoveryStrategy.RETRY_LINEAR_BACKOFF:
                    result = await RetryStrategy.retry_with_backoff(
                        lambda: self._execute_safely(func, *args, **kwargs),
                        max_attempts=3,
                        backoff_strategy="linear"
                    )
                    event.recovery_successful = True
                    return result
                    
                elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                    breaker_name = f"{event.agent_id}:{event.operation}"
                    circuit_breaker = self.get_circuit_breaker(breaker_name)
                    
                    result, success = circuit_breaker.call(
                        lambda: self._execute_safely(func, *args, **kwargs)
                    )
                    if success:
                        event.recovery_successful = True
                        return result
                        
                elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                    # Return a degraded response instead of failing
                    logger.info(f"Graceful degradation for {event.agent_id}:{event.operation}")
                    event.recovery_successful = True
                    return self._get_degraded_response(event.operation)
                    
                # Add more recovery strategies as needed
                
            except Exception as e:
                logger.warning(f"Recovery strategy {strategy.value} failed: {e}")
                continue
        
        # All recovery strategies failed
        event.recovery_successful = False
        raise Exception(f"All recovery strategies failed for {event.fault_type.value}")

    async def _execute_safely(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function safely, handling both sync and async"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _get_degraded_response(self, operation: str) -> Any:
        """Get a degraded response for graceful degradation"""
        # This would be customized based on the operation
        return {
            "status": "degraded",
            "message": f"Service operating in degraded mode for {operation}",
            "data": None
        }

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex

    # Analysis and reporting methods
    def get_resilience_report(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get resilience analysis report"""
        if agent_id:
            agents = [agent_id]
        else:
            agents = list(self.agent_health_scores.keys())
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "agents": {},
            "overall_stats": {
                "total_faults_injected": len(self.fault_history),
                "active_faults": len(self.active_faults),
                "average_resilience_score": 0.0,
                "fault_type_distribution": defaultdict(int),
                "recovery_success_rate": 0.0
            }
        }
        
        all_scores = []
        recovery_successes = 0
        
        for agent in agents:
            agent_metrics = self.resilience_metrics.get(agent, [])
            agent_faults = [f for f in self.fault_history if f.agent_id == agent]
            
            if agent_metrics:
                avg_score = sum(m["resilience_score"] for m in agent_metrics) / len(agent_metrics)
                avg_recovery_time = sum(m["recovery_time"] for m in agent_metrics) / len(agent_metrics)
                all_scores.append(avg_score)
            else:
                avg_score = 0.0
                avg_recovery_time = 0.0
            
            agent_recovery_successes = sum(1 for f in agent_faults if f.recovery_successful)
            if agent_faults:
                agent_recovery_rate = agent_recovery_successes / len(agent_faults)
                recovery_successes += agent_recovery_successes
            else:
                agent_recovery_rate = 0.0
            
            report["agents"][agent] = {
                "health_score": self.agent_health_scores.get(agent, 0.0),
                "total_faults": len(agent_faults),
                "average_resilience_score": avg_score,
                "average_recovery_time": avg_recovery_time,
                "recovery_success_rate": agent_recovery_rate,
                "recent_metrics": agent_metrics[-5:]  # Last 5 events
            }
        
        # Overall statistics
        if self.fault_history:
            report["overall_stats"]["average_resilience_score"] = sum(all_scores) / len(all_scores) if all_scores else 0.0
            report["overall_stats"]["recovery_success_rate"] = recovery_successes / len(self.fault_history)
            
            # Fault type distribution
            for fault in self.fault_history:
                report["overall_stats"]["fault_type_distribution"][fault.fault_type.value] += 1
        
        return report

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            name: breaker.get_stats() 
            for name, breaker in self.circuit_breakers.items()
        }

    def export_scenarios(self) -> Dict[str, Any]:
        """Export all scenarios for backup/sharing"""
        return {
            "scenarios": {
                sid: asdict(scenario) for sid, scenario in self.scenarios.items()
            },
            "exported_at": datetime.utcnow().isoformat()
        }

    def import_scenarios(self, data: Dict[str, Any]):
        """Import scenarios from backup/sharing"""
        for sid, scenario_data in data.get("scenarios", {}).items():
            # Convert datetime strings back to datetime objects
            scenario_data["created_at"] = datetime.fromisoformat(scenario_data["created_at"])
            if scenario_data.get("last_activated"):
                scenario_data["last_activated"] = datetime.fromisoformat(scenario_data["last_activated"])
            
            scenario = FaultScenario(**scenario_data)
            self.scenarios[sid] = scenario
        
        logger.info(f"Imported {len(data.get('scenarios', {}))} scenarios")

# Predefined fault scenarios for common testing
def create_common_scenarios() -> List[FaultScenario]:
    """Create common fault injection scenarios"""
    scenarios = []
    
    # Network latency scenario
    scenarios.append(FaultScenario(
        scenario_id="network_latency_moderate",
        name="Moderate Network Latency",
        description="Inject moderate network latency to test timeout handling",
        fault_type=FaultType.NETWORK_LATENCY,
        target_agents=["*"],
        target_operations=["api_call", "network_request"],
        probability=0.1,
        duration_min=1.0,
        duration_max=5.0,
        severity=0.3,
        recovery_strategies=[RecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF]
    ))
    
    # Service unavailable scenario
    scenarios.append(FaultScenario(
        scenario_id="service_unavailable_brief",
        name="Brief Service Unavailability",
        description="Simulate brief service outages",
        fault_type=FaultType.SERVICE_UNAVAILABLE,
        target_agents=["*"],
        target_operations=["database_query", "api_call"],
        probability=0.05,
        duration_min=2.0,
        duration_max=10.0,
        severity=0.8,
        recovery_strategies=[
            RecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF,
            RecoveryStrategy.CIRCUIT_BREAKER
        ]
    ))
    
    # Memory pressure scenario
    scenarios.append(FaultScenario(
        scenario_id="memory_pressure_high",
        name="High Memory Pressure",
        description="Simulate high memory usage conditions",
        fault_type=FaultType.MEMORY_PRESSURE,
        target_agents=["rig", "craft"],
        target_operations=["process_large_file", "render_scene"],
        probability=0.03,
        duration_min=5.0,
        duration_max=30.0,
        severity=0.7,
        recovery_strategies=[RecoveryStrategy.GRACEFUL_DEGRADATION]
    ))
    
    return scenarios

# Example usage and testing
async def main():
    """Example usage of the chaos testing system"""
    # Initialize fault injector
    injector = FaultInjector()
    
    # Add common scenarios
    scenarios = create_common_scenarios()
    for scenario in scenarios:
        injector.add_scenario(scenario)
    
    # Example function to test
    async def example_api_call():
        await asyncio.sleep(0.1)  # Simulate work
        return {"status": "success", "data": "example response"}
    
    # Test with fault tolerance
    for i in range(10):
        try:
            result = await injector.execute_with_fault_tolerance(
                example_api_call,
                agent_id="test_agent",
                operation="api_call"
            )
            print(f"Call {i}: Success - {result}")
            
        except Exception as e:
            print(f"Call {i}: Failed - {e}")
        
        await asyncio.sleep(0.5)
    
    # Get resilience report
    report = injector.get_resilience_report()
    print("\nResilience Report:")
    print(json.dumps(report, indent=2, default=str))
    
    # Get circuit breaker status
    cb_status = injector.get_circuit_breaker_status()
    print("\nCircuit Breaker Status:")
    print(json.dumps(cb_status, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())