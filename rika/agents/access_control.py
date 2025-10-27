"""
Agent Access Control System
Manages what data each agent can access and enforces boundaries
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentAccessControl:
    """Manages what data each agent can access"""

    def __init__(self, boundaries_config: Dict):
        """
        Initialize access control with boundaries configuration

        Args:
            boundaries_config: Boundaries configuration dict
        """
        self.boundaries = boundaries_config
        self.logger = logging.getLogger(__name__)

    def can_agent_access(self, agent_name: str, data_type: str) -> bool:
        """
        Check if agent is allowed to access data type

        Args:
            agent_name: Name of the agent
            data_type: Type of data to access

        Returns:
            True if allowed, False otherwise
        """
        try:
            agent_bounds = self.boundaries.get("agents", {}).get(agent_name, {})
            allowed_data = agent_bounds.get("allowed_data", [])

            # Check if data type is explicitly allowed
            if data_type in allowed_data:
                return True

            # Check if data type is explicitly blocked
            blocked_data = agent_bounds.get("blocked_data", [])
            if data_type in blocked_data:
                return False

            # Default deny
            return False

        except Exception as e:
            self.logger.error(f"Error checking access for {agent_name}.{data_type}: {e}")
            return False

    def can_agent_perform_action(self, agent_name: str, action: str) -> bool:
        """
        Check if agent is allowed to perform action

        Args:
            agent_name: Name of the agent
            action: Action to perform

        Returns:
            True if allowed, False otherwise
        """
        try:
            agent_bounds = self.boundaries.get("agents", {}).get(agent_name, {})
            allowed_actions = agent_bounds.get("allowed_actions", [])

            return action in allowed_actions

        except Exception as e:
            self.logger.error(f"Error checking action permission for {agent_name}.{action}: {e}")
            return False

    def requires_approval(self, agent_name: str, action: str) -> bool:
        """
        Check if action requires user approval

        Args:
            agent_name: Name of the agent
            action: Action to check

        Returns:
            True if approval required
        """
        try:
            agent_bounds = self.boundaries.get("agents", {}).get(agent_name, {})
            approval_required = agent_bounds.get("approval_required", [])

            return action in approval_required

        except Exception as e:
            self.logger.error(f"Error checking approval requirement: {e}")
            return True  # Safer to require approval on error

    def get_agent_boundaries(self, agent_name: str) -> Dict:
        """
        Get all boundaries for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Boundaries dict
        """
        return self.boundaries.get("agents", {}).get(agent_name, {
            "name": agent_name,
            "allowed_data": [],
            "blocked_data": [],
            "allowed_actions": [],
            "approval_required": []
        })

    def get_all_agents(self) -> List[str]:
        """
        Get list of all registered agents

        Returns:
            List of agent names
        """
        return list(self.boundaries.get("agents", {}).keys())

    def request_data_access(self, agent_name: str, data_types: List[str],
                           reason: str = "") -> Dict:
        """
        Agent requests access to specific data.
        Checks boundaries and returns approved/denied lists.

        Args:
            agent_name: Name of requesting agent
            data_types: List of data types requested
            reason: Reason for access request

        Returns:
            Dict with approved, denied, and timestamp
        """
        try:
            approved = []
            denied = []

            for data_type in data_types:
                if self.can_agent_access(agent_name, data_type):
                    approved.append(data_type)
                else:
                    denied.append(data_type)

            if denied:
                self.logger.warning(
                    f"Agent {agent_name} denied access to: {denied}. Reason: {reason}"
                )

            if approved:
                self.logger.info(
                    f"Agent {agent_name} granted access to: {approved}. Reason: {reason}"
                )

            return {
                "agent": agent_name,
                "approved": approved,
                "denied": denied,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error processing data access request: {e}")
            return {
                "agent": agent_name,
                "approved": [],
                "denied": data_types,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def validate_action_request(self, agent_name: str, action: str,
                               data_types: List[str] = None) -> Dict:
        """
        Validate an action request from an agent

        Args:
            agent_name: Name of the agent
            action: Action to perform
            data_types: Data types involved (optional)

        Returns:
            Validation result dict
        """
        try:
            result = {
                "allowed": False,
                "requires_approval": False,
                "denied_reasons": []
            }

            # Check if action is allowed
            if not self.can_agent_perform_action(agent_name, action):
                result["denied_reasons"].append(f"Action '{action}' not in allowed actions")
                return result

            # Check if action requires approval
            if self.requires_approval(agent_name, action):
                result["requires_approval"] = True

            # Check data access if specified
            if data_types:
                denied_data = [
                    dt for dt in data_types
                    if not self.can_agent_access(agent_name, dt)
                ]

                if denied_data:
                    result["denied_reasons"].append(
                        f"Access denied to data types: {', '.join(denied_data)}"
                    )
                    return result

            # All checks passed
            result["allowed"] = True
            return result

        except Exception as e:
            self.logger.error(f"Error validating action request: {e}")
            return {
                "allowed": False,
                "requires_approval": False,
                "denied_reasons": [f"Validation error: {str(e)}"]
            }

    def log_access_attempt(self, agent_name: str, data_type: str,
                          action: str, allowed: bool, reason: str = "") -> Dict:
        """
        Log an access attempt for audit trail

        Args:
            agent_name: Name of the agent
            data_type: Data type accessed
            action: Action performed
            allowed: Whether access was allowed
            reason: Reason for access

        Returns:
            Log entry dict
        """
        log_entry = {
            "agent": agent_name,
            "data_type": data_type,
            "action": action,
            "allowed": allowed,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # Log to system
        if allowed:
            self.logger.info(f"Access granted: {agent_name} -> {data_type} ({action})")
        else:
            self.logger.warning(f"Access denied: {agent_name} -> {data_type} ({action})")

        return log_entry

    def get_agent_permissions_summary(self, agent_name: str) -> Dict:
        """
        Get a summary of an agent's permissions

        Args:
            agent_name: Name of the agent

        Returns:
            Permissions summary dict
        """
        boundaries = self.get_agent_boundaries(agent_name)

        return {
            "agent": agent_name,
            "display_name": boundaries.get("name", agent_name),
            "allowed_data": boundaries.get("allowed_data", []),
            "blocked_data": boundaries.get("blocked_data", []),
            "allowed_actions": boundaries.get("allowed_actions", []),
            "approval_required_actions": boundaries.get("approval_required", []),
            "data_access_count": len(boundaries.get("allowed_data", [])),
            "action_count": len(boundaries.get("allowed_actions", []))
        }

    def compare_agent_permissions(self, agent1: str, agent2: str) -> Dict:
        """
        Compare permissions between two agents

        Args:
            agent1: First agent name
            agent2: Second agent name

        Returns:
            Comparison dict
        """
        bounds1 = self.get_agent_boundaries(agent1)
        bounds2 = self.get_agent_boundaries(agent2)

        data1 = set(bounds1.get("allowed_data", []))
        data2 = set(bounds2.get("allowed_data", []))

        actions1 = set(bounds1.get("allowed_actions", []))
        actions2 = set(bounds2.get("allowed_actions", []))

        return {
            "agent1": agent1,
            "agent2": agent2,
            "common_data": list(data1 & data2),
            "unique_to_agent1_data": list(data1 - data2),
            "unique_to_agent2_data": list(data2 - data1),
            "common_actions": list(actions1 & actions2),
            "unique_to_agent1_actions": list(actions1 - actions2),
            "unique_to_agent2_actions": list(actions2 - actions1)
        }

    def update_agent_boundaries(self, agent_name: str, updates: Dict) -> bool:
        """
        Update agent boundaries (requires admin privileges)

        Args:
            agent_name: Name of the agent
            updates: Updates to apply

        Returns:
            True if successful
        """
        try:
            if "agents" not in self.boundaries:
                self.boundaries["agents"] = {}

            if agent_name not in self.boundaries["agents"]:
                self.boundaries["agents"][agent_name] = {}

            agent_bounds = self.boundaries["agents"][agent_name]

            # Apply updates
            for key, value in updates.items():
                if key in ["name", "allowed_data", "blocked_data",
                          "allowed_actions", "approval_required"]:
                    agent_bounds[key] = value

            self.logger.info(f"Updated boundaries for agent {agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating agent boundaries: {e}")
            return False

    def enforce_strict_mode(self) -> None:
        """
        Enable strict mode - denies all access not explicitly allowed
        """
        self.boundaries["strict_mode"] = True
        self.logger.info("Strict mode enabled - all non-explicit access denied")

    def is_strict_mode(self) -> bool:
        """Check if strict mode is enabled"""
        return self.boundaries.get("strict_mode", False)
