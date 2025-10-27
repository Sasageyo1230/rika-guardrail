"""
Overseer Hardening - Capability Policies System
Fine-grained access control and security policies for Rika agents

Phase 3.3 Enhancement:
- Granular capability management per agent
- Dynamic policy enforcement with real-time updates
- Security context evaluation and risk assessment
- Audit logging with tamper detection
- Policy inheritance and role-based permissions
"""

import json
import logging
import hashlib
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapabilityLevel(Enum):
    """Capability access levels"""
    DENIED = 0
    READ_ONLY = 1
    LIMITED = 2
    FULL = 3
    ELEVATED = 4

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ActionType(Enum):
    """Types of actions that can be controlled"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write" 
    FILE_EXECUTE = "file_execute"
    NETWORK_REQUEST = "network_request"
    SYSTEM_COMMAND = "system_command"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    API_CALL = "api_call"
    RESOURCE_ACCESS = "resource_access"
    AGENT_COMMUNICATION = "agent_communication"
    CONFIGURATION_CHANGE = "configuration_change"
    SERVICE_CONTROL = "service_control"

@dataclass
class SecurityContext:
    """Current security context for evaluation"""
    agent_id: str
    session_id: str
    user_id: Optional[str]
    timestamp: datetime
    source_ip: Optional[str] = None
    authentication_method: Optional[str] = None
    session_duration: Optional[timedelta] = None
    previous_actions: List[Dict[str, Any]] = None
    risk_factors: List[str] = None
    
    def __post_init__(self):
        if self.previous_actions is None:
            self.previous_actions = []
        if self.risk_factors is None:
            self.risk_factors = []

@dataclass
class PolicyRule:
    """Individual policy rule definition"""
    rule_id: str
    name: str
    description: str
    action_type: ActionType
    resource_pattern: str  # Regex pattern for resource matching
    capability_level: CapabilityLevel
    conditions: Dict[str, Any]  # Conditional requirements
    time_restrictions: Optional[Dict[str, Any]] = None
    rate_limits: Optional[Dict[str, Any]] = None
    audit_level: str = "standard"  # standard, detailed, full
    expires_at: Optional[datetime] = None
    priority: int = 100  # Higher number = higher priority
    
    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

@dataclass
class AgentCapabilities:
    """Capability profile for an agent"""
    agent_id: str
    agent_type: str  # rig, craft, scout, echo, pulse, atlas
    base_capabilities: Set[ActionType]
    elevated_capabilities: Set[ActionType]
    denied_capabilities: Set[ActionType]
    custom_rules: List[PolicyRule]
    inheritance_chain: List[str]  # Parent policies to inherit
    risk_tolerance: RiskLevel
    created_at: datetime
    updated_at: datetime
    version: int = 1

@dataclass
class PolicyViolation:
    """Policy violation record"""
    violation_id: str
    agent_id: str
    action_type: ActionType
    resource: str
    attempted_at: datetime
    policy_rule: str
    severity: RiskLevel
    context: SecurityContext
    blocked: bool
    reason: str
    remediation_suggested: Optional[str] = None

@dataclass
class AuditEvent:
    """Security audit event"""
    event_id: str
    agent_id: str
    action_type: ActionType
    resource: str
    capability_level: CapabilityLevel
    allowed: bool
    timestamp: datetime
    context: SecurityContext
    policy_rules_applied: List[str]
    execution_time_ms: float
    hash_signature: str  # For tamper detection

class PolicyEngine:
    """Core policy evaluation engine"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/security_policies.json")
        self.agent_capabilities: Dict[str, AgentCapabilities] = {}
        self.global_policies: List[PolicyRule] = []
        self.violation_history: List[PolicyViolation] = []
        self.audit_events: List[AuditEvent] = []
        self.policy_cache: Dict[str, Any] = {}
        self._policy_lock = asyncio.Lock()
        
        # Load default policies
        self._load_default_policies()
        
        # Load custom policies if config exists
        if self.config_path.exists():
            self._load_policies_from_file()

    def _load_default_policies(self):
        """Load default security policies for each agent type"""
        default_policies = {
            "rig": {
                "base_capabilities": {
                    ActionType.FILE_READ,
                    ActionType.FILE_WRITE,
                    ActionType.SYSTEM_COMMAND,
                    ActionType.RESOURCE_ACCESS
                },
                "elevated_capabilities": {
                    ActionType.FILE_EXECUTE,
                    ActionType.SERVICE_CONTROL
                },
                "denied_capabilities": {
                    ActionType.DATABASE_WRITE,
                    ActionType.CONFIGURATION_CHANGE
                },
                "risk_tolerance": RiskLevel.MEDIUM
            },
            "craft": {
                "base_capabilities": {
                    ActionType.FILE_READ,
                    ActionType.FILE_WRITE,
                    ActionType.API_CALL,
                    ActionType.RESOURCE_ACCESS
                },
                "elevated_capabilities": {
                    ActionType.NETWORK_REQUEST,
                    ActionType.DATABASE_READ
                },
                "denied_capabilities": {
                    ActionType.SYSTEM_COMMAND,
                    ActionType.FILE_EXECUTE
                },
                "risk_tolerance": RiskLevel.LOW
            },
            "scout": {
                "base_capabilities": {
                    ActionType.FILE_READ,
                    ActionType.NETWORK_REQUEST,
                    ActionType.API_CALL,
                    ActionType.DATABASE_READ
                },
                "elevated_capabilities": {
                    ActionType.FILE_WRITE,
                    ActionType.DATABASE_WRITE
                },
                "denied_capabilities": {
                    ActionType.SYSTEM_COMMAND,
                    ActionType.SERVICE_CONTROL
                },
                "risk_tolerance": RiskLevel.LOW
            },
            "echo": {
                "base_capabilities": {
                    ActionType.NETWORK_REQUEST,
                    ActionType.API_CALL,
                    ActionType.AGENT_COMMUNICATION,
                    ActionType.DATABASE_READ
                },
                "elevated_capabilities": {
                    ActionType.DATABASE_WRITE,
                    ActionType.FILE_WRITE
                },
                "denied_capabilities": {
                    ActionType.SYSTEM_COMMAND,
                    ActionType.CONFIGURATION_CHANGE
                },
                "risk_tolerance": RiskLevel.MEDIUM
            },
            "pulse": {
                "base_capabilities": {
                    ActionType.FILE_READ,
                    ActionType.DATABASE_READ,
                    ActionType.RESOURCE_ACCESS,
                    ActionType.AGENT_COMMUNICATION
                },
                "elevated_capabilities": {
                    ActionType.DATABASE_WRITE,
                    ActionType.API_CALL
                },
                "denied_capabilities": {
                    ActionType.FILE_EXECUTE,
                    ActionType.SYSTEM_COMMAND
                },
                "risk_tolerance": RiskLevel.LOW
            },
            "atlas": {
                "base_capabilities": set(ActionType),  # All capabilities
                "elevated_capabilities": set(),
                "denied_capabilities": set(),
                "risk_tolerance": RiskLevel.HIGH
            }
        }
        
        for agent_type, config in default_policies.items():
            capabilities = AgentCapabilities(
                agent_id=f"default_{agent_type}",
                agent_type=agent_type,
                base_capabilities=config["base_capabilities"],
                elevated_capabilities=config["elevated_capabilities"],
                denied_capabilities=config["denied_capabilities"],
                custom_rules=[],
                inheritance_chain=["global"],
                risk_tolerance=config["risk_tolerance"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.agent_capabilities[agent_type] = capabilities

    def _load_policies_from_file(self):
        """Load policies from configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Load global policies
            if 'global_policies' in config:
                for rule_data in config['global_policies']:
                    rule = self._deserialize_policy_rule(rule_data)
                    self.global_policies.append(rule)
            
            # Load agent-specific policies
            if 'agent_capabilities' in config:
                for agent_id, cap_data in config['agent_capabilities'].items():
                    capabilities = self._deserialize_agent_capabilities(cap_data)
                    self.agent_capabilities[agent_id] = capabilities
            
            logger.info(f"Loaded policies from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load policies from file: {e}")

    def _deserialize_policy_rule(self, data: Dict[str, Any]) -> PolicyRule:
        """Deserialize policy rule from JSON data"""
        return PolicyRule(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            action_type=ActionType(data["action_type"]),
            resource_pattern=data["resource_pattern"],
            capability_level=CapabilityLevel(data["capability_level"]),
            conditions=data.get("conditions", {}),
            time_restrictions=data.get("time_restrictions"),
            rate_limits=data.get("rate_limits"),
            audit_level=data.get("audit_level", "standard"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            priority=data.get("priority", 100)
        )

    def _deserialize_agent_capabilities(self, data: Dict[str, Any]) -> AgentCapabilities:
        """Deserialize agent capabilities from JSON data"""
        return AgentCapabilities(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            base_capabilities={ActionType(action) for action in data["base_capabilities"]},
            elevated_capabilities={ActionType(action) for action in data["elevated_capabilities"]},
            denied_capabilities={ActionType(action) for action in data["denied_capabilities"]},
            custom_rules=[self._deserialize_policy_rule(rule) for rule in data.get("custom_rules", [])],
            inheritance_chain=data.get("inheritance_chain", ["global"]),
            risk_tolerance=RiskLevel(data["risk_tolerance"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1)
        )

    async def evaluate_capability(
        self,
        agent_id: str,
        action_type: ActionType,
        resource: str,
        context: SecurityContext
    ) -> tuple[bool, CapabilityLevel, List[str]]:
        """
        Evaluate if an agent has capability to perform an action
        Returns: (allowed, capability_level, applied_rules)
        """
        start_time = datetime.utcnow()
        applied_rules = []
        
        try:
            async with self._policy_lock:
                # Get agent capabilities
                agent_caps = await self._get_agent_capabilities(agent_id)
                if not agent_caps:
                    return False, CapabilityLevel.DENIED, ["no_agent_capabilities"]
                
                # Check for explicit denial first
                if action_type in agent_caps.denied_capabilities:
                    await self._log_violation(
                        agent_id, action_type, resource, context,
                        "explicit_denial", RiskLevel.HIGH
                    )
                    return False, CapabilityLevel.DENIED, ["explicit_denial"]
                
                # Evaluate global policies
                global_result = await self._evaluate_global_policies(
                    action_type, resource, context, agent_caps
                )
                
                # Evaluate agent-specific rules
                agent_result = await self._evaluate_agent_rules(
                    agent_caps, action_type, resource, context
                )
                
                # Determine final capability level
                final_capability = self._merge_capability_results(global_result, agent_result)
                allowed = final_capability != CapabilityLevel.DENIED
                
                applied_rules.extend(global_result.get("rules", []))
                applied_rules.extend(agent_result.get("rules", []))
                
                # Check risk assessment
                if allowed:
                    risk_assessment = await self._assess_risk(
                        agent_id, action_type, resource, context, agent_caps
                    )
                    
                    if risk_assessment["level"] > agent_caps.risk_tolerance:
                        allowed = False
                        final_capability = CapabilityLevel.DENIED
                        await self._log_violation(
                            agent_id, action_type, resource, context,
                            f"risk_too_high_{risk_assessment['level'].name}", 
                            risk_assessment["level"]
                        )
                        applied_rules.append("risk_assessment")
                
                # Log audit event
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                await self._log_audit_event(
                    agent_id, action_type, resource, final_capability,
                    allowed, context, applied_rules, execution_time
                )
                
                return allowed, final_capability, applied_rules
                
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            return False, CapabilityLevel.DENIED, ["evaluation_error"]

    async def _get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilities]:
        """Get capabilities for an agent, with inheritance"""
        # Check direct agent capabilities
        if agent_id in self.agent_capabilities:
            return self.agent_capabilities[agent_id]
        
        # Check by agent type (e.g., "rig_001" -> "rig")
        agent_type = agent_id.split('_')[0]
        if agent_type in self.agent_capabilities:
            return self.agent_capabilities[agent_type]
        
        return None

    async def _evaluate_global_policies(
        self,
        action_type: ActionType,
        resource: str,
        context: SecurityContext,
        agent_caps: AgentCapabilities
    ) -> Dict[str, Any]:
        """Evaluate global policies"""
        applicable_rules = []
        capability_level = CapabilityLevel.FULL
        
        for rule in self.global_policies:
            if rule.action_type == action_type and self._matches_resource(rule.resource_pattern, resource):
                if await self._evaluate_rule_conditions(rule, context, agent_caps):
                    applicable_rules.append(rule.rule_id)
                    capability_level = min(capability_level, rule.capability_level, key=lambda x: x.value)
        
        return {
            "capability_level": capability_level,
            "rules": applicable_rules
        }

    async def _evaluate_agent_rules(
        self,
        agent_caps: AgentCapabilities,
        action_type: ActionType,
        resource: str,
        context: SecurityContext
    ) -> Dict[str, Any]:
        """Evaluate agent-specific rules"""
        applicable_rules = []
        
        # Base capability check
        if action_type in agent_caps.base_capabilities:
            capability_level = CapabilityLevel.FULL
        elif action_type in agent_caps.elevated_capabilities:
            capability_level = CapabilityLevel.ELEVATED
        else:
            capability_level = CapabilityLevel.LIMITED
        
        # Check custom rules
        for rule in agent_caps.custom_rules:
            if rule.action_type == action_type and self._matches_resource(rule.resource_pattern, resource):
                if await self._evaluate_rule_conditions(rule, context, agent_caps):
                    applicable_rules.append(rule.rule_id)
                    capability_level = min(capability_level, rule.capability_level, key=lambda x: x.value)
        
        return {
            "capability_level": capability_level,
            "rules": applicable_rules
        }

    def _matches_resource(self, pattern: str, resource: str) -> bool:
        """Check if resource matches pattern (regex)"""
        import re
        try:
            return bool(re.match(pattern, resource))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False

    async def _evaluate_rule_conditions(
        self,
        rule: PolicyRule,
        context: SecurityContext,
        agent_caps: AgentCapabilities
    ) -> bool:
        """Evaluate rule conditions"""
        if rule.is_expired():
            return False
        
        # Time restrictions
        if rule.time_restrictions:
            if not self._check_time_restrictions(rule.time_restrictions, context.timestamp):
                return False
        
        # Rate limits
        if rule.rate_limits:
            if not await self._check_rate_limits(rule.rate_limits, context.agent_id, rule.action_type):
                return False
        
        # Custom conditions
        for condition_key, condition_value in rule.conditions.items():
            if not await self._evaluate_condition(condition_key, condition_value, context, agent_caps):
                return False
        
        return True

    def _check_time_restrictions(self, restrictions: Dict[str, Any], timestamp: datetime) -> bool:
        """Check if current time meets restrictions"""
        if "allowed_hours" in restrictions:
            current_hour = timestamp.hour
            allowed_hours = restrictions["allowed_hours"]
            if isinstance(allowed_hours, list):
                if current_hour not in allowed_hours:
                    return False
            elif isinstance(allowed_hours, dict):
                start = allowed_hours.get("start", 0)
                end = allowed_hours.get("end", 23)
                if not (start <= current_hour <= end):
                    return False
        
        if "allowed_days" in restrictions:
            current_day = timestamp.weekday()  # 0 = Monday
            if current_day not in restrictions["allowed_days"]:
                return False
        
        return True

    async def _check_rate_limits(
        self,
        limits: Dict[str, Any],
        agent_id: str,
        action_type: ActionType
    ) -> bool:
        """Check rate limits for agent/action"""
        # Get recent actions for this agent/action type
        now = datetime.utcnow()
        recent_events = []
        
        for event in self.audit_events:
            if (event.agent_id == agent_id and 
                event.action_type == action_type and
                event.allowed):
                time_diff = now - event.timestamp
                recent_events.append(time_diff.total_seconds())
        
        # Check each rate limit
        for period, max_count in limits.items():
            if period == "per_minute":
                recent_count = len([e for e in recent_events if e <= 60])
            elif period == "per_hour":
                recent_count = len([e for e in recent_events if e <= 3600])
            elif period == "per_day":
                recent_count = len([e for e in recent_events if e <= 86400])
            else:
                continue
            
            if recent_count >= max_count:
                return False
        
        return True

    async def _evaluate_condition(
        self,
        condition_key: str,
        condition_value: Any,
        context: SecurityContext,
        agent_caps: AgentCapabilities
    ) -> bool:
        """Evaluate custom condition"""
        if condition_key == "require_user":
            return context.user_id is not None
        elif condition_key == "min_session_duration":
            if context.session_duration:
                return context.session_duration.total_seconds() >= condition_value
        elif condition_key == "allowed_ips":
            if context.source_ip:
                return context.source_ip in condition_value
        elif condition_key == "require_auth_method":
            return context.authentication_method == condition_value
        elif condition_key == "max_risk_factors":
            return len(context.risk_factors) <= condition_value
        
        return True

    def _merge_capability_results(
        self,
        global_result: Dict[str, Any],
        agent_result: Dict[str, Any]
    ) -> CapabilityLevel:
        """Merge capability results from global and agent policies"""
        # Take the more restrictive capability level
        global_level = global_result.get("capability_level", CapabilityLevel.FULL)
        agent_level = agent_result.get("capability_level", CapabilityLevel.FULL)
        
        return min(global_level, agent_level, key=lambda x: x.value)

    async def _assess_risk(
        self,
        agent_id: str,
        action_type: ActionType,
        resource: str,
        context: SecurityContext,
        agent_caps: AgentCapabilities
    ) -> Dict[str, Any]:
        """Assess risk level for the action"""
        risk_score = 0
        risk_factors = []
        
        # Base risk by action type
        action_risk = {
            ActionType.FILE_READ: 1,
            ActionType.FILE_WRITE: 2,
            ActionType.FILE_EXECUTE: 4,
            ActionType.SYSTEM_COMMAND: 4,
            ActionType.NETWORK_REQUEST: 2,
            ActionType.DATABASE_WRITE: 3,
            ActionType.CONFIGURATION_CHANGE: 4,
            ActionType.SERVICE_CONTROL: 4
        }
        risk_score += action_risk.get(action_type, 1)
        
        # Resource-based risk
        if "system" in resource.lower() or "config" in resource.lower():
            risk_score += 2
            risk_factors.append("sensitive_resource")
        
        if resource.startswith("/"):
            risk_score += 1
            risk_factors.append("absolute_path")
        
        # Context-based risk
        if not context.user_id:
            risk_score += 1
            risk_factors.append("no_user_context")
        
        if context.source_ip and context.source_ip.startswith("127."):
            pass  # Local connections are safer
        elif context.source_ip:
            risk_score += 1
            risk_factors.append("remote_connection")
        
        if len(context.previous_actions) > 10:
            risk_score += 1
            risk_factors.append("high_activity")
        
        # Historical risk
        recent_violations = [v for v in self.violation_history 
                           if v.agent_id == agent_id and 
                           (datetime.utcnow() - v.attempted_at).days <= 7]
        if recent_violations:
            risk_score += len(recent_violations)
            risk_factors.append("recent_violations")
        
        # Determine risk level
        if risk_score <= 2:
            risk_level = RiskLevel.LOW
        elif risk_score <= 4:
            risk_level = RiskLevel.MEDIUM
        elif risk_score <= 6:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors
        }

    async def _log_violation(
        self,
        agent_id: str,
        action_type: ActionType,
        resource: str,
        context: SecurityContext,
        reason: str,
        severity: RiskLevel
    ):
        """Log a policy violation"""
        violation = PolicyViolation(
            violation_id=self._generate_id("violation"),
            agent_id=agent_id,
            action_type=action_type,
            resource=resource,
            attempted_at=datetime.utcnow(),
            policy_rule=reason,
            severity=severity,
            context=context,
            blocked=True,
            reason=reason
        )
        
        self.violation_history.append(violation)
        
        # Alert on high severity violations
        if severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            await self._send_security_alert(violation)
        
        logger.warning(f"Policy violation: {agent_id} attempted {action_type.value} on {resource} - {reason}")

    async def _log_audit_event(
        self,
        agent_id: str,
        action_type: ActionType,
        resource: str,
        capability_level: CapabilityLevel,
        allowed: bool,
        context: SecurityContext,
        applied_rules: List[str],
        execution_time_ms: float
    ):
        """Log audit event with tamper detection"""
        event = AuditEvent(
            event_id=self._generate_id("audit"),
            agent_id=agent_id,
            action_type=action_type,
            resource=resource,
            capability_level=capability_level,
            allowed=allowed,
            timestamp=datetime.utcnow(),
            context=context,
            policy_rules_applied=applied_rules,
            execution_time_ms=execution_time_ms,
            hash_signature=""  # Will be set below
        )
        
        # Generate tamper-proof hash
        event_data = {
            "event_id": event.event_id,
            "agent_id": event.agent_id,
            "action_type": event.action_type.value,
            "resource": event.resource,
            "allowed": event.allowed,
            "timestamp": event.timestamp.isoformat()
        }
        event.hash_signature = hashlib.sha256(
            json.dumps(event_data, sort_keys=True).encode()
        ).hexdigest()
        
        self.audit_events.append(event)
        
        # Trim old events to prevent unbounded growth
        if len(self.audit_events) > 10000:
            self.audit_events = self.audit_events[-5000:]

    async def _send_security_alert(self, violation: PolicyViolation):
        """Send security alert for high-severity violations"""
        alert_data = {
            "type": "security_violation",
            "severity": violation.severity.name,
            "agent_id": violation.agent_id,
            "action": violation.action_type.value,
            "resource": violation.resource,
            "reason": violation.reason,
            "timestamp": violation.attempted_at.isoformat()
        }
        
        # In a real implementation, this would send to monitoring system
        logger.critical(f"SECURITY ALERT: {json.dumps(alert_data)}")

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex

    # Management methods
    async def add_policy_rule(self, rule: PolicyRule, global_rule: bool = True):
        """Add a new policy rule"""
        async with self._policy_lock:
            if global_rule:
                self.global_policies.append(rule)
            else:
                # Add to specific agent (requires agent_id in rule context)
                pass
            
            await self._save_policies()
            logger.info(f"Added policy rule: {rule.rule_id}")

    async def update_agent_capabilities(self, agent_id: str, capabilities: AgentCapabilities):
        """Update agent capabilities"""
        async with self._policy_lock:
            capabilities.updated_at = datetime.utcnow()
            capabilities.version += 1
            self.agent_capabilities[agent_id] = capabilities
            
            await self._save_policies()
            logger.info(f"Updated capabilities for agent: {agent_id}")

    async def get_violations(self, agent_id: Optional[str] = None, hours: int = 24) -> List[PolicyViolation]:
        """Get recent policy violations"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        violations = [v for v in self.violation_history if v.attempted_at >= cutoff]
        
        if agent_id:
            violations = [v for v in violations if v.agent_id == agent_id]
        
        return violations

    async def get_audit_events(self, agent_id: Optional[str] = None, hours: int = 24) -> List[AuditEvent]:
        """Get recent audit events"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        events = [e for e in self.audit_events if e.timestamp >= cutoff]
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        return events

    async def _save_policies(self):
        """Save current policies to file"""
        try:
            config_data = {
                "global_policies": [self._serialize_policy_rule(rule) for rule in self.global_policies],
                "agent_capabilities": {
                    agent_id: self._serialize_agent_capabilities(caps)
                    for agent_id, caps in self.agent_capabilities.items()
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Saved policies to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")

    def _serialize_policy_rule(self, rule: PolicyRule) -> Dict[str, Any]:
        """Serialize policy rule to JSON-compatible dict"""
        return {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "action_type": rule.action_type.value,
            "resource_pattern": rule.resource_pattern,
            "capability_level": rule.capability_level.value,
            "conditions": rule.conditions,
            "time_restrictions": rule.time_restrictions,
            "rate_limits": rule.rate_limits,
            "audit_level": rule.audit_level,
            "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
            "priority": rule.priority
        }

    def _serialize_agent_capabilities(self, caps: AgentCapabilities) -> Dict[str, Any]:
        """Serialize agent capabilities to JSON-compatible dict"""
        return {
            "agent_id": caps.agent_id,
            "agent_type": caps.agent_type,
            "base_capabilities": [action.value for action in caps.base_capabilities],
            "elevated_capabilities": [action.value for action in caps.elevated_capabilities],
            "denied_capabilities": [action.value for action in caps.denied_capabilities],
            "custom_rules": [self._serialize_policy_rule(rule) for rule in caps.custom_rules],
            "inheritance_chain": caps.inheritance_chain,
            "risk_tolerance": caps.risk_tolerance.value,
            "created_at": caps.created_at.isoformat(),
            "updated_at": caps.updated_at.isoformat(),
            "version": caps.version
        }

# Example usage and testing
async def main():
    """Example usage of the capability policy system"""
    # Initialize policy engine
    engine = PolicyEngine()
    
    # Create security context
    context = SecurityContext(
        agent_id="rig_001",
        session_id="session_123",
        user_id="user_456",
        timestamp=datetime.utcnow(),
        source_ip="192.168.1.100",
        authentication_method="api_key"
    )
    
    # Test capability evaluation
    allowed, capability, rules = await engine.evaluate_capability(
        "rig_001",
        ActionType.FILE_WRITE,
        "/tmp/test_file.txt",
        context
    )
    
    print(f"File write allowed: {allowed}")
    print(f"Capability level: {capability.name}")
    print(f"Applied rules: {rules}")
    
    # Test denied action
    allowed, capability, rules = await engine.evaluate_capability(
        "craft_001",
        ActionType.SYSTEM_COMMAND,
        "rm -rf /",
        context
    )
    
    print(f"System command allowed: {allowed}")
    print(f"Capability level: {capability.name}")
    
    # Get recent violations
    violations = await engine.get_violations(hours=1)
    print(f"Recent violations: {len(violations)}")

if __name__ == "__main__":
    asyncio.run(main())