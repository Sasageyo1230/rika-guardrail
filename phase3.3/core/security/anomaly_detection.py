"""
Overseer Hardening - Anomaly Detection System
Advanced behavioral analysis and threat detection for Rika agents

Phase 3.3 Enhancement:
- Real-time behavioral monitoring and analysis
- Machine learning-based anomaly detection
- Pattern recognition for suspicious activities
- Adaptive threat response and mitigation
- Integration with capability policies system
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    BEHAVIORAL_DEVIATION = "behavioral_deviation"
    RESOURCE_ABUSE = "resource_abuse"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    ACCESS_PATTERN_ANOMALY = "access_pattern_anomaly"
    COMMUNICATION_ANOMALY = "communication_anomaly"
    PERFORMANCE_ANOMALY = "performance_anomaly"
    SECURITY_VIOLATION = "security_violation"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_PAYLOAD = "suspicious_payload"

class SeverityLevel(Enum):
    """Severity levels for anomalies"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

class ResponseAction(Enum):
    """Automated response actions"""
    LOG_ONLY = "log_only"
    ALERT = "alert"
    THROTTLE = "throttle"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    TERMINATE = "terminate"

@dataclass
class BehavioralProfile:
    """Behavioral profile for an agent"""
    agent_id: str
    agent_type: str
    creation_date: datetime
    
    # Activity patterns
    average_actions_per_minute: float = 0.0
    peak_activity_hours: List[int] = None
    common_resources: Dict[str, float] = None  # resource -> frequency
    typical_session_duration: float = 0.0  # minutes
    
    # Communication patterns
    communication_frequency: Dict[str, float] = None  # agent_id -> frequency
    api_usage_patterns: Dict[str, float] = None  # endpoint -> frequency
    
    # Resource usage patterns
    cpu_usage_baseline: float = 0.0
    memory_usage_baseline: float = 0.0
    network_usage_baseline: float = 0.0
    
    # Error patterns
    error_rate_baseline: float = 0.0
    common_error_types: Dict[str, float] = None
    
    # Learning metrics
    sample_count: int = 0
    last_updated: datetime = None
    confidence_score: float = 0.0  # 0.0 to 1.0
    
    def __post_init__(self):
        if self.peak_activity_hours is None:
            self.peak_activity_hours = []
        if self.common_resources is None:
            self.common_resources = {}
        if self.communication_frequency is None:
            self.communication_frequency = {}
        if self.api_usage_patterns is None:
            self.api_usage_patterns = {}
        if self.common_error_types is None:
            self.common_error_types = {}
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

@dataclass
class AnomalyEvent:
    """Detected anomaly event"""
    event_id: str
    agent_id: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    confidence: float  # 0.0 to 1.0
    description: str
    detected_at: datetime
    
    # Context data
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    deviation_score: Optional[float] = None
    related_events: List[str] = None
    context_data: Dict[str, Any] = None
    
    # Response tracking
    response_actions: List[ResponseAction] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    false_positive: bool = False
    
    def __post_init__(self):
        if self.related_events is None:
            self.related_events = []
        if self.context_data is None:
            self.context_data = {}
        if self.response_actions is None:
            self.response_actions = []

@dataclass
class AgentActivity:
    """Current activity snapshot for an agent"""
    agent_id: str
    timestamp: datetime
    
    # Activity metrics
    actions_last_minute: int = 0
    actions_last_hour: int = 0
    session_duration: float = 0.0  # minutes
    
    # Resource usage
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_received: int = 0
    
    # Recent actions
    recent_resources: List[str] = None
    recent_api_calls: List[str] = None
    recent_communications: List[str] = None
    recent_errors: List[str] = None
    
    def __post_init__(self):
        if self.recent_resources is None:
            self.recent_resources = []
        if self.recent_api_calls is None:
            self.recent_api_calls = []
        if self.recent_communications is None:
            self.recent_communications = []
        if self.recent_errors is None:
            self.recent_errors = []

class StatisticalAnalyzer:
    """Statistical methods for anomaly detection"""
    
    @staticmethod
    def z_score(value: float, mean: float, std: float) -> float:
        """Calculate Z-score for outlier detection"""
        if std == 0:
            return 0.0
        return abs(value - mean) / std
    
    @staticmethod
    def moving_average(values: List[float], window_size: int = 10) -> float:
        """Calculate moving average"""
        if not values:
            return 0.0
        recent_values = values[-window_size:]
        return sum(recent_values) / len(recent_values)
    
    @staticmethod
    def exponential_smoothing(values: List[float], alpha: float = 0.3) -> float:
        """Calculate exponentially smoothed value"""
        if not values:
            return 0.0
        
        result = values[0]
        for value in values[1:]:
            result = alpha * value + (1 - alpha) * result
        return result
    
    @staticmethod
    def interquartile_range_outlier(values: List[float], value: float) -> Tuple[bool, float]:
        """Detect outliers using IQR method"""
        if len(values) < 4:
            return False, 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        is_outlier = value < lower_bound or value > upper_bound
        outlier_score = 0.0
        
        if value < lower_bound:
            outlier_score = (lower_bound - value) / (iqr or 1.0)
        elif value > upper_bound:
            outlier_score = (value - upper_bound) / (iqr or 1.0)
        
        return is_outlier, outlier_score

class PatternMatcher:
    """Pattern matching for behavioral analysis"""
    
    def __init__(self):
        self.suspicious_patterns = {
            # File system patterns
            "mass_file_access": r"(\w+_read_file).*(\w+_read_file).*(\w+_read_file)",
            "sensitive_file_access": r".*(config|secret|key|password|credential).*",
            "system_file_access": r".*(\/etc\/|\/sys\/|\/proc\/|C:\\Windows\\System32).*",
            
            # Network patterns
            "port_scanning": r"network_request.*:(\d+).*network_request.*:(\d+)",
            "data_exfiltration": r"network_request.*(upload|post|send).*large_payload",
            "c2_communication": r"network_request.*(base64|encoded|encrypted).*external",
            
            # Command patterns
            "privilege_escalation": r".*(sudo|runas|admin|root|administrator).*",
            "process_injection": r".*(inject|dll|shellcode|payload).*",
            "persistence": r".*(registry|startup|cron|service|task).*",
            
            # API patterns
            "api_enumeration": r"api_call.*error.*api_call.*error.*api_call",
            "credential_stuffing": r"auth.*failed.*auth.*failed.*auth",
            "rate_limit_abuse": r"(api_call.*){10,}"
        }
    
    def check_patterns(self, activity_log: List[str]) -> List[Tuple[str, float]]:
        """Check activity log against suspicious patterns"""
        import re
        matches = []
        
        activity_text = " ".join(activity_log)
        
        for pattern_name, pattern in self.suspicious_patterns.items():
            try:
                if re.search(pattern, activity_text, re.IGNORECASE):
                    confidence = self._calculate_pattern_confidence(pattern_name, activity_text)
                    matches.append((pattern_name, confidence))
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern_name}")
        
        return matches
    
    def _calculate_pattern_confidence(self, pattern_name: str, activity_text: str) -> float:
        """Calculate confidence score for pattern match"""
        # Simple heuristic based on pattern type and frequency
        base_confidence = {
            "mass_file_access": 0.7,
            "sensitive_file_access": 0.8,
            "system_file_access": 0.9,
            "port_scanning": 0.8,
            "data_exfiltration": 0.95,
            "c2_communication": 0.9,
            "privilege_escalation": 0.95,
            "process_injection": 0.9,
            "persistence": 0.85,
            "api_enumeration": 0.6,
            "credential_stuffing": 0.8,
            "rate_limit_abuse": 0.7
        }
        
        return base_confidence.get(pattern_name, 0.5)

class AnomalyDetector:
    """Main anomaly detection system"""
    
    def __init__(self, learning_period_hours: int = 24):
        self.learning_period = timedelta(hours=learning_period_hours)
        self.profiles: Dict[str, BehavioralProfile] = {}
        self.activity_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_events: List[AnomalyEvent] = []
        self.statistical_analyzer = StatisticalAnalyzer()
        self.pattern_matcher = PatternMatcher()
        
        # Detection thresholds
        self.z_score_threshold = 3.0
        self.confidence_threshold = 0.7
        self.min_samples_for_detection = 10
        
        # Response configuration
        self.response_rules = {
            SeverityLevel.INFO: [ResponseAction.LOG_ONLY],
            SeverityLevel.LOW: [ResponseAction.LOG_ONLY, ResponseAction.ALERT],
            SeverityLevel.MEDIUM: [ResponseAction.ALERT, ResponseAction.THROTTLE],
            SeverityLevel.HIGH: [ResponseAction.ALERT, ResponseAction.QUARANTINE],
            SeverityLevel.CRITICAL: [ResponseAction.ALERT, ResponseAction.BLOCK]
        }

    async def learn_behavior(self, agent_id: str, activity: AgentActivity):
        """Learn normal behavior patterns for an agent"""
        if agent_id not in self.profiles:
            self.profiles[agent_id] = BehavioralProfile(
                agent_id=agent_id,
                agent_type=agent_id.split('_')[0],
                creation_date=datetime.utcnow()
            )
        
        profile = self.profiles[agent_id]
        self.activity_history[agent_id].append(activity)
        
        # Only learn during the learning period or if we don't have enough samples
        age = datetime.utcnow() - profile.creation_date
        if age <= self.learning_period or profile.sample_count < self.min_samples_for_detection:
            await self._update_behavioral_profile(profile, activity)
            
            # Increase confidence as we gather more samples
            profile.sample_count += 1
            profile.confidence_score = min(1.0, profile.sample_count / 100.0)
            profile.last_updated = datetime.utcnow()
        
        logger.debug(f"Updated behavioral profile for {agent_id} (samples: {profile.sample_count})")

    async def _update_behavioral_profile(self, profile: BehavioralProfile, activity: AgentActivity):
        """Update behavioral profile with new activity data"""
        # Update activity patterns
        if profile.sample_count == 0:
            profile.average_actions_per_minute = activity.actions_last_minute
            profile.typical_session_duration = activity.session_duration
            profile.cpu_usage_baseline = activity.cpu_usage
            profile.memory_usage_baseline = activity.memory_usage
            profile.network_usage_baseline = activity.network_bytes_sent + activity.network_bytes_received
        else:
            # Exponential moving average for smooth updates
            alpha = 0.1
            profile.average_actions_per_minute = (
                alpha * activity.actions_last_minute + 
                (1 - alpha) * profile.average_actions_per_minute
            )
            profile.typical_session_duration = (
                alpha * activity.session_duration + 
                (1 - alpha) * profile.typical_session_duration
            )
            profile.cpu_usage_baseline = (
                alpha * activity.cpu_usage + 
                (1 - alpha) * profile.cpu_usage_baseline
            )
            profile.memory_usage_baseline = (
                alpha * activity.memory_usage + 
                (1 - alpha) * profile.memory_usage_baseline
            )
            profile.network_usage_baseline = (
                alpha * (activity.network_bytes_sent + activity.network_bytes_received) + 
                (1 - alpha) * profile.network_usage_baseline
            )
        
        # Update resource patterns
        for resource in activity.recent_resources:
            if resource in profile.common_resources:
                profile.common_resources[resource] = (
                    alpha * 1.0 + (1 - alpha) * profile.common_resources[resource]
                )
            else:
                profile.common_resources[resource] = alpha
        
        # Update API patterns
        for api_call in activity.recent_api_calls:
            if api_call in profile.api_usage_patterns:
                profile.api_usage_patterns[api_call] = (
                    alpha * 1.0 + (1 - alpha) * profile.api_usage_patterns[api_call]
                )
            else:
                profile.api_usage_patterns[api_call] = alpha
        
        # Update communication patterns
        for comm in activity.recent_communications:
            if comm in profile.communication_frequency:
                profile.communication_frequency[comm] = (
                    alpha * 1.0 + (1 - alpha) * profile.communication_frequency[comm]
                )
            else:
                profile.communication_frequency[comm] = alpha
        
        # Update peak activity hours
        current_hour = activity.timestamp.hour
        if current_hour not in profile.peak_activity_hours and activity.actions_last_minute > 0:
            profile.peak_activity_hours.append(current_hour)
        
        # Update error patterns
        error_count = len(activity.recent_errors)
        if error_count > 0:
            if profile.sample_count == 0:
                profile.error_rate_baseline = error_count
            else:
                profile.error_rate_baseline = (
                    alpha * error_count + (1 - alpha) * profile.error_rate_baseline
                )
            
            for error in activity.recent_errors:
                if error in profile.common_error_types:
                    profile.common_error_types[error] = (
                        alpha * 1.0 + (1 - alpha) * profile.common_error_types[error]
                    )
                else:
                    profile.common_error_types[error] = alpha

    async def detect_anomalies(self, agent_id: str, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect anomalies in agent activity"""
        if agent_id not in self.profiles:
            await self.learn_behavior(agent_id, activity)
            return []
        
        profile = self.profiles[agent_id]
        
        # Skip detection if we don't have enough learning data
        if profile.confidence_score < self.confidence_threshold:
            await self.learn_behavior(agent_id, activity)
            return []
        
        anomalies = []
        
        # Detect various types of anomalies
        anomalies.extend(await self._detect_behavioral_anomalies(profile, activity))
        anomalies.extend(await self._detect_resource_anomalies(profile, activity))
        anomalies.extend(await self._detect_temporal_anomalies(profile, activity))
        anomalies.extend(await self._detect_access_pattern_anomalies(profile, activity))
        anomalies.extend(await self._detect_communication_anomalies(profile, activity))
        anomalies.extend(await self._detect_pattern_based_anomalies(agent_id, activity))
        
        # Process and respond to detected anomalies
        for anomaly in anomalies:
            await self._process_anomaly(anomaly)
        
        return anomalies

    async def _detect_behavioral_anomalies(self, profile: BehavioralProfile, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect behavioral deviations from normal patterns"""
        anomalies = []
        
        # Activity rate anomaly
        activity_z_score = self.statistical_analyzer.z_score(
            activity.actions_last_minute,
            profile.average_actions_per_minute,
            profile.average_actions_per_minute * 0.5  # Assume 50% std dev
        )
        
        if activity_z_score > self.z_score_threshold:
            severity = SeverityLevel.MEDIUM if activity_z_score > 5 else SeverityLevel.LOW
            anomaly = AnomalyEvent(
                event_id=self._generate_id("anomaly"),
                agent_id=profile.agent_id,
                anomaly_type=AnomalyType.BEHAVIORAL_DEVIATION,
                severity=severity,
                confidence=min(0.95, activity_z_score / 10.0),
                description=f"Activity rate significantly higher than baseline: {activity.actions_last_minute} vs {profile.average_actions_per_minute:.1f}",
                detected_at=datetime.utcnow(),
                baseline_value=profile.average_actions_per_minute,
                observed_value=float(activity.actions_last_minute),
                deviation_score=activity_z_score
            )
            anomalies.append(anomaly)
        
        # Session duration anomaly
        if profile.typical_session_duration > 0:
            duration_ratio = activity.session_duration / profile.typical_session_duration
            if duration_ratio > 3.0 or (duration_ratio < 0.1 and activity.session_duration > 1):
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.BEHAVIORAL_DEVIATION,
                    severity=SeverityLevel.LOW,
                    confidence=0.6,
                    description=f"Unusual session duration: {activity.session_duration:.1f} min vs typical {profile.typical_session_duration:.1f} min",
                    detected_at=datetime.utcnow(),
                    baseline_value=profile.typical_session_duration,
                    observed_value=activity.session_duration,
                    deviation_score=abs(duration_ratio - 1.0)
                )
                anomalies.append(anomaly)
        
        return anomalies

    async def _detect_resource_anomalies(self, profile: BehavioralProfile, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect resource usage anomalies"""
        anomalies = []
        
        # CPU usage anomaly
        if profile.cpu_usage_baseline > 0:
            cpu_ratio = activity.cpu_usage / profile.cpu_usage_baseline
            if cpu_ratio > 5.0:
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.RESOURCE_ABUSE,
                    severity=SeverityLevel.HIGH if cpu_ratio > 10 else SeverityLevel.MEDIUM,
                    confidence=0.8,
                    description=f"Excessive CPU usage: {activity.cpu_usage:.1f}% vs baseline {profile.cpu_usage_baseline:.1f}%",
                    detected_at=datetime.utcnow(),
                    baseline_value=profile.cpu_usage_baseline,
                    observed_value=activity.cpu_usage,
                    deviation_score=cpu_ratio
                )
                anomalies.append(anomaly)
        
        # Memory usage anomaly
        if profile.memory_usage_baseline > 0:
            memory_ratio = activity.memory_usage / profile.memory_usage_baseline
            if memory_ratio > 5.0:
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.RESOURCE_ABUSE,
                    severity=SeverityLevel.HIGH if memory_ratio > 10 else SeverityLevel.MEDIUM,
                    confidence=0.8,
                    description=f"Excessive memory usage: {activity.memory_usage:.1f} MB vs baseline {profile.memory_usage_baseline:.1f} MB",
                    detected_at=datetime.utcnow(),
                    baseline_value=profile.memory_usage_baseline,
                    observed_value=activity.memory_usage,
                    deviation_score=memory_ratio
                )
                anomalies.append(anomaly)
        
        # Network usage anomaly
        current_network = activity.network_bytes_sent + activity.network_bytes_received
        if profile.network_usage_baseline > 0:
            network_ratio = current_network / profile.network_usage_baseline
            if network_ratio > 10.0:
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.DATA_EXFILTRATION if network_ratio > 50 else AnomalyType.RESOURCE_ABUSE,
                    severity=SeverityLevel.CRITICAL if network_ratio > 100 else SeverityLevel.HIGH,
                    confidence=0.9,
                    description=f"Excessive network usage: {current_network} bytes vs baseline {profile.network_usage_baseline:.1f}",
                    detected_at=datetime.utcnow(),
                    baseline_value=profile.network_usage_baseline,
                    observed_value=float(current_network),
                    deviation_score=network_ratio
                )
                anomalies.append(anomaly)
        
        return anomalies

    async def _detect_temporal_anomalies(self, profile: BehavioralProfile, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect temporal anomalies (activity at unusual times)"""
        anomalies = []
        
        current_hour = activity.timestamp.hour
        
        # Check if activity is happening outside normal hours
        if (profile.peak_activity_hours and 
            current_hour not in profile.peak_activity_hours and 
            activity.actions_last_minute > profile.average_actions_per_minute):
            
            # Calculate how unusual this time is
            time_distance = min(
                abs(current_hour - peak_hour) for peak_hour in profile.peak_activity_hours
            )
            
            if time_distance > 6:  # More than 6 hours from normal activity
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.TEMPORAL_ANOMALY,
                    severity=SeverityLevel.MEDIUM if time_distance > 10 else SeverityLevel.LOW,
                    confidence=0.7,
                    description=f"Activity at unusual time: {current_hour}:00 (normal hours: {profile.peak_activity_hours})",
                    detected_at=datetime.utcnow(),
                    context_data={"current_hour": current_hour, "normal_hours": profile.peak_activity_hours},
                    deviation_score=float(time_distance)
                )
                anomalies.append(anomaly)
        
        return anomalies

    async def _detect_access_pattern_anomalies(self, profile: BehavioralProfile, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect unusual resource access patterns"""
        anomalies = []
        
        # Check for access to unusual resources
        unusual_resources = []
        for resource in activity.recent_resources:
            if resource not in profile.common_resources:
                unusual_resources.append(resource)
            elif profile.common_resources[resource] < 0.01:  # Very rare resource
                unusual_resources.append(resource)
        
        if unusual_resources:
            # Check for sensitive patterns
            sensitive_keywords = ['config', 'secret', 'key', 'password', 'credential', 'admin', 'root']
            sensitive_resources = [r for r in unusual_resources if any(kw in r.lower() for kw in sensitive_keywords)]
            
            if sensitive_resources:
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.ACCESS_PATTERN_ANOMALY,
                    severity=SeverityLevel.HIGH,
                    confidence=0.9,
                    description=f"Access to sensitive resources: {sensitive_resources}",
                    detected_at=datetime.utcnow(),
                    context_data={"sensitive_resources": sensitive_resources},
                    deviation_score=float(len(sensitive_resources))
                )
                anomalies.append(anomaly)
            elif len(unusual_resources) > 10:
                anomaly = AnomalyEvent(
                    event_id=self._generate_id("anomaly"),
                    agent_id=profile.agent_id,
                    anomaly_type=AnomalyType.ACCESS_PATTERN_ANOMALY,
                    severity=SeverityLevel.MEDIUM,
                    confidence=0.7,
                    description=f"Mass access to unusual resources: {len(unusual_resources)} resources",
                    detected_at=datetime.utcnow(),
                    context_data={"unusual_resource_count": len(unusual_resources)},
                    deviation_score=float(len(unusual_resources))
                )
                anomalies.append(anomaly)
        
        return anomalies

    async def _detect_communication_anomalies(self, profile: BehavioralProfile, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect unusual communication patterns"""
        anomalies = []
        
        # Check for communication with unusual agents
        unusual_communications = []
        for comm in activity.recent_communications:
            if comm not in profile.communication_frequency:
                unusual_communications.append(comm)
            elif profile.communication_frequency[comm] < 0.01:
                unusual_communications.append(comm)
        
        if len(unusual_communications) > 5:
            anomaly = AnomalyEvent(
                event_id=self._generate_id("anomaly"),
                agent_id=profile.agent_id,
                anomaly_type=AnomalyType.COMMUNICATION_ANOMALY,
                severity=SeverityLevel.MEDIUM,
                confidence=0.6,
                description=f"Communication with many unusual agents: {len(unusual_communications)} new contacts",
                detected_at=datetime.utcnow(),
                context_data={"unusual_communications": unusual_communications[:10]},  # Limit for storage
                deviation_score=float(len(unusual_communications))
            )
            anomalies.append(anomaly)
        
        # Check for potential C&C communication patterns
        external_comms = [comm for comm in unusual_communications if 'external' in comm.lower() or 'unknown' in comm.lower()]
        if external_comms:
            anomaly = AnomalyEvent(
                event_id=self._generate_id("anomaly"),
                agent_id=profile.agent_id,
                anomaly_type=AnomalyType.COMMUNICATION_ANOMALY,
                severity=SeverityLevel.HIGH,
                confidence=0.8,
                description=f"Communication with external/unknown entities: {external_comms}",
                detected_at=datetime.utcnow(),
                context_data={"external_communications": external_comms},
                deviation_score=float(len(external_comms))
            )
            anomalies.append(anomaly)
        
        return anomalies

    async def _detect_pattern_based_anomalies(self, agent_id: str, activity: AgentActivity) -> List[AnomalyEvent]:
        """Detect anomalies using pattern matching"""
        anomalies = []
        
        # Build activity log from recent activities
        activity_log = []
        activity_log.extend(activity.recent_resources)
        activity_log.extend(activity.recent_api_calls)
        activity_log.extend(activity.recent_communications)
        activity_log.extend(activity.recent_errors)
        
        # Check against suspicious patterns
        pattern_matches = self.pattern_matcher.check_patterns(activity_log)
        
        for pattern_name, confidence in pattern_matches:
            # Determine severity based on pattern type
            severity_mapping = {
                "mass_file_access": SeverityLevel.MEDIUM,
                "sensitive_file_access": SeverityLevel.HIGH,
                "system_file_access": SeverityLevel.CRITICAL,
                "port_scanning": SeverityLevel.HIGH,
                "data_exfiltration": SeverityLevel.CRITICAL,
                "c2_communication": SeverityLevel.CRITICAL,
                "privilege_escalation": SeverityLevel.CRITICAL,
                "process_injection": SeverityLevel.CRITICAL,
                "persistence": SeverityLevel.HIGH,
                "api_enumeration": SeverityLevel.MEDIUM,
                "credential_stuffing": SeverityLevel.HIGH,
                "rate_limit_abuse": SeverityLevel.MEDIUM
            }
            
            severity = severity_mapping.get(pattern_name, SeverityLevel.LOW)
            
            # Determine anomaly type
            if pattern_name in ["data_exfiltration"]:
                anomaly_type = AnomalyType.DATA_EXFILTRATION
            elif pattern_name in ["privilege_escalation", "process_injection"]:
                anomaly_type = AnomalyType.PRIVILEGE_ESCALATION
            elif pattern_name in ["c2_communication", "port_scanning"]:
                anomaly_type = AnomalyType.COMMUNICATION_ANOMALY
            else:
                anomaly_type = AnomalyType.SUSPICIOUS_PAYLOAD
            
            anomaly = AnomalyEvent(
                event_id=self._generate_id("anomaly"),
                agent_id=agent_id,
                anomaly_type=anomaly_type,
                severity=severity,
                confidence=confidence,
                description=f"Suspicious pattern detected: {pattern_name}",
                detected_at=datetime.utcnow(),
                context_data={"pattern_name": pattern_name, "activity_log": activity_log[:50]}  # Limit for storage
            )
            anomalies.append(anomaly)
        
        return anomalies

    async def _process_anomaly(self, anomaly: AnomalyEvent):
        """Process detected anomaly and trigger appropriate responses"""
        # Add to anomaly history
        self.anomaly_events.append(anomaly)
        
        # Determine response actions
        response_actions = self.response_rules.get(anomaly.severity, [ResponseAction.LOG_ONLY])
        anomaly.response_actions = response_actions
        
        # Execute response actions
        for action in response_actions:
            await self._execute_response_action(action, anomaly)
        
        logger.warning(
            f"Anomaly detected: {anomaly.agent_id} - {anomaly.anomaly_type.value} "
            f"(severity: {anomaly.severity.name}, confidence: {anomaly.confidence:.2f})"
        )

    async def _execute_response_action(self, action: ResponseAction, anomaly: AnomalyEvent):
        """Execute a specific response action"""
        if action == ResponseAction.LOG_ONLY:
            logger.info(f"Logged anomaly: {anomaly.event_id}")
        
        elif action == ResponseAction.ALERT:
            await self._send_alert(anomaly)
        
        elif action == ResponseAction.THROTTLE:
            await self._throttle_agent(anomaly.agent_id)
        
        elif action == ResponseAction.QUARANTINE:
            await self._quarantine_agent(anomaly.agent_id)
        
        elif action == ResponseAction.BLOCK:
            await self._block_agent(anomaly.agent_id)
        
        elif action == ResponseAction.TERMINATE:
            await self._terminate_agent(anomaly.agent_id)

    async def _send_alert(self, anomaly: AnomalyEvent):
        """Send alert notification"""
        alert_data = {
            "type": "anomaly_detection",
            "event_id": anomaly.event_id,
            "agent_id": anomaly.agent_id,
            "anomaly_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.name,
            "confidence": anomaly.confidence,
            "description": anomaly.description,
            "timestamp": anomaly.detected_at.isoformat()
        }
        
        # In a real implementation, this would send to a monitoring system
        logger.warning(f"ANOMALY ALERT: {json.dumps(alert_data)}")

    async def _throttle_agent(self, agent_id: str):
        """Throttle agent activity"""
        logger.info(f"Throttling agent: {agent_id}")
        # Implementation would integrate with agent management system

    async def _quarantine_agent(self, agent_id: str):
        """Quarantine agent (limited access)"""
        logger.warning(f"Quarantining agent: {agent_id}")
        # Implementation would isolate agent to limited sandbox

    async def _block_agent(self, agent_id: str):
        """Block agent from all activities"""
        logger.warning(f"Blocking agent: {agent_id}")
        # Implementation would disable agent completely

    async def _terminate_agent(self, agent_id: str):
        """Terminate agent process"""
        logger.critical(f"Terminating agent: {agent_id}")
        # Implementation would forcibly stop agent process

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex

    # Management and analysis methods
    def get_agent_profile(self, agent_id: str) -> Optional[BehavioralProfile]:
        """Get behavioral profile for agent"""
        return self.profiles.get(agent_id)

    def get_recent_anomalies(self, agent_id: Optional[str] = None, hours: int = 24) -> List[AnomalyEvent]:
        """Get recent anomaly events"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        anomalies = [a for a in self.anomaly_events if a.detected_at >= cutoff]
        
        if agent_id:
            anomalies = [a for a in anomalies if a.agent_id == agent_id]
        
        return anomalies

    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        recent_anomalies = self.get_recent_anomalies(hours=24)
        
        stats = {
            "total_anomalies_24h": len(recent_anomalies),
            "anomaly_types": defaultdict(int),
            "severity_distribution": defaultdict(int),
            "agents_with_anomalies": set(),
            "average_confidence": 0.0
        }
        
        for anomaly in recent_anomalies:
            stats["anomaly_types"][anomaly.anomaly_type.value] += 1
            stats["severity_distribution"][anomaly.severity.name] += 1
            stats["agents_with_anomalies"].add(anomaly.agent_id)
        
        if recent_anomalies:
            stats["average_confidence"] = sum(a.confidence for a in recent_anomalies) / len(recent_anomalies)
        
        stats["agents_with_anomalies"] = len(stats["agents_with_anomalies"])
        stats["anomaly_types"] = dict(stats["anomaly_types"])
        stats["severity_distribution"] = dict(stats["severity_distribution"])
        
        return stats

# Example usage and testing
async def main():
    """Example usage of the anomaly detection system"""
    detector = AnomalyDetector(learning_period_hours=1)  # Short learning period for demo
    
    # Simulate normal activity for learning
    normal_activity = AgentActivity(
        agent_id="rig_001",
        timestamp=datetime.utcnow(),
        actions_last_minute=5,
        actions_last_hour=300,
        session_duration=30.0,
        cpu_usage=25.0,
        memory_usage=128.0,
        network_bytes_sent=1024,
        network_bytes_received=2048,
        recent_resources=["/tmp/file1.txt", "/home/user/doc.txt"],
        recent_api_calls=["get_status", "update_config"],
        recent_communications=["craft_001", "atlas_001"]
    )
    
    # Learn normal behavior
    for i in range(20):
        await detector.learn_behavior("rig_001", normal_activity)
        await asyncio.sleep(0.01)  # Small delay for simulation
    
    # Simulate anomalous activity
    anomalous_activity = AgentActivity(
        agent_id="rig_001",
        timestamp=datetime.utcnow(),
        actions_last_minute=100,  # Much higher than normal
        actions_last_hour=6000,
        session_duration=30.0,
        cpu_usage=95.0,  # Very high CPU
        memory_usage=1024.0,  # Very high memory
        network_bytes_sent=1048576,  # 1MB sent (very high)
        network_bytes_received=2048,
        recent_resources=["/etc/passwd", "/etc/shadow", "/root/.ssh/id_rsa"],  # Sensitive files
        recent_api_calls=["admin_access", "root_shell", "system_config"],
        recent_communications=["external_unknown_host", "suspicious_agent"]
    )
    
    # Detect anomalies
    anomalies = await detector.detect_anomalies("rig_001", anomalous_activity)
    
    print(f"Detected {len(anomalies)} anomalies:")
    for anomaly in anomalies:
        print(f"- {anomaly.anomaly_type.value}: {anomaly.description} (confidence: {anomaly.confidence:.2f})")
    
    # Get statistics
    stats = detector.get_anomaly_statistics()
    print(f"\nAnomaly Statistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())