"""
Rika Orchestrator v2
Master orchestrator managing sub-agents and data access
"""

import json
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class RikaOrchestrator:
    """Master orchestrator managing sub-agents and data access"""

    def __init__(self, config_path: str):
        """
        Initialize the Rika Orchestrator

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db = None  # Initialized by setup_database()
        self.vector_store = None  # Initialized by setup_vector_store()
        self.llm = None  # Initialized by setup_llm()
        self.auth_manager = None  # Initialized by setup_auth()
        self.encryption_manager = None  # From Phase 1
        self.agents = {}  # Sub-agents registry
        self.data_access_log = []
        self.logger = logging.getLogger(__name__)

    def initialize(self, db_connection, vector_store, llm, auth_manager, encryption_manager):
        """
        Initialize orchestrator with required components

        Args:
            db_connection: Database connection
            vector_store: Vector database for embeddings
            llm: LLM instance for inference
            auth_manager: Authentication manager
            encryption_manager: Encryption manager from Phase 1
        """
        self.db = db_connection
        self.vector_store = vector_store
        self.llm = llm
        self.auth_manager = auth_manager
        self.encryption_manager = encryption_manager
        self.logger.info("Rika Orchestrator initialized successfully")

    def register_agent(self, agent_name: str, agent_class):
        """
        Register a sub-agent (e.g., Mint, Rig)

        Args:
            agent_name: Name of the agent
            agent_class: Agent class to instantiate
        """
        try:
            agent = agent_class(
                orchestrator=self,
                db=self.db,
                encryption=self.encryption_manager
            )
            self.agents[agent_name] = agent
            self.logger.info(f"Agent registered: {agent_name}")

            # Log agent registration
            self._log_system_event(
                event_type="agent_registered",
                agent_name=agent_name,
                event_data={"agent_class": agent_class.__name__}
            )

        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_name}: {e}")
            raise

    def process_request(self, user_input: str, session_token: str) -> Dict[str, Any]:
        """
        Main request flow:
        1. Authenticate
        2. Retrieve cognitive context
        3. LLM reasoning
        4. Execute action if needed
        5. Log everything

        Args:
            user_input: User's input/query
            session_token: User session token for authentication

        Returns:
            Response dict with status, response text, and actions taken
        """
        try:
            # 1. Authenticate
            user_id = self._authenticate_user(session_token)
            if not user_id:
                return {
                    "status": "DENIED",
                    "reason": "Invalid session token",
                    "response": "Authentication failed. Please log in again."
                }

            self.logger.info(f"Processing request from user {user_id}: {user_input[:100]}")

            # 2. Retrieve context from Cognitive Sphere
            context = self.retrieve_context(user_input)

            # 3. Build prompt with system instructions
            prompt = self._build_prompt(user_input, context)

            # 4. LLM reasoning
            llm_response = self.llm.generate(prompt)
            parsed_response = self._parse_llm_response(llm_response)

            # 5. Handle actions (if any)
            if parsed_response.get("action"):
                action_result = self.execute_action(
                    action=parsed_response["action"],
                    agent_name=parsed_response.get("agent"),
                    params=parsed_response.get("params", {}),
                    user_id=user_id
                )
                parsed_response["action_result"] = action_result

            # 6. Log interaction
            self._log_interaction(
                user_id=user_id,
                user_input=user_input,
                response=parsed_response,
                context_used=context.get("sources", [])
            )

            return {
                "status": "SUCCESS",
                "response": parsed_response.get("text", "").strip(),
                "confidence": parsed_response.get("confidence", 0.8),
                "decision_log": parsed_response.get("reasoning"),
                "actions_taken": parsed_response.get("action_result"),
                "context_sources": context.get("sources", [])
            }

        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "reason": str(e),
                "response": "I encountered an error processing your request. Please try again."
            }

    def retrieve_context(self, user_input: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant context from Cognitive Sphere.
        Returns: Most relevant emails, calendar events, projects, patterns.

        Args:
            user_input: User's query
            top_k: Number of top results to retrieve

        Returns:
            Dict with documents and sources
        """
        try:
            # Vector search in Cognitive Sphere
            results = self._vector_search(user_input, top_k)

            # Rerank by relevance + recency
            reranked = self._rerank_results(results)

            return {
                "documents": reranked,
                "sources": [r.get("source", "unknown") for r in reranked]
            }

        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return {"documents": [], "sources": []}

    def execute_action(self, action: str, agent_name: str, params: Dict, user_id: str) -> Dict[str, Any]:
        """
        Execute action via sub-agent

        Args:
            action: Action to execute
            agent_name: Name of the agent to execute action
            params: Action parameters
            user_id: User ID requesting the action

        Returns:
            Action result dict
        """
        try:
            # Check boundaries
            if not self._check_boundaries(action, agent_name):
                self.logger.warning(f"Boundary violation: {agent_name} -> {action}")
                return {
                    "status": "DENIED",
                    "reason": "Action violates agent boundaries"
                }

            # Check if approval needed
            if self._requires_approval(action):
                approval_id = self._request_action_approval(
                    agent_name=agent_name,
                    action=action,
                    params=params
                )
                return {
                    "status": "PENDING_APPROVAL",
                    "action": action,
                    "approval_id": approval_id,
                    "message": f"Action '{action}' requires your approval. Check your notifications."
                }

            # Execute via agent
            agent = self.agents.get(agent_name)
            if not agent:
                return {
                    "status": "ERROR",
                    "reason": f"Agent '{agent_name}' not found"
                }

            # Log action execution
            self._log_agent_action(agent_name, action, params, user_id)

            # Execute
            result = agent.execute(action, params, user_id)
            return result

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "reason": str(e)
            }

    def request_agent_data_access(self, agent_name: str, data_types: List[str], reason: str) -> List[str]:
        """
        Agent requests access to specific data types.
        Rika verifies boundaries, logs request.

        Args:
            agent_name: Name of the requesting agent
            data_types: List of data types requested
            reason: Reason for access request

        Returns:
            List of approved data types
        """
        try:
            # Check if data types are within boundaries
            approved_types = self._check_agent_boundaries(agent_name, data_types)

            denied = set(data_types) - set(approved_types)
            if denied:
                self.logger.warning(f"Agent {agent_name} denied access to: {denied}")

            # Log request
            self._log_agent_data_request(agent_name, data_types, approved_types, reason)

            return approved_types

        except Exception as e:
            self.logger.error(f"Error processing data access request: {e}")
            return []

    def request_action_approval(self, action: str, details: Dict) -> str:
        """
        Request user approval for an action

        Args:
            action: Action requiring approval
            details: Action details

        Returns:
            Approval request ID
        """
        return self._request_action_approval("rika", action, details)

    # Private helper methods

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading config from {config_path}: {e}")
            # Return default config
            return {
                "llm_model_path": "models/rika-llm.gguf",
                "boundaries_config": "config/boundaries.yaml",
                "system_prompt": "config/system_prompt.yaml"
            }

    def _authenticate_user(self, session_token: str) -> Optional[str]:
        """Authenticate user via session token"""
        if self.auth_manager:
            return self.auth_manager.verify_token(session_token)

        # For testing, accept any token
        return "test_user" if session_token else None

    def _build_prompt(self, user_input: str, context: Dict) -> str:
        """
        Build LLM prompt with system instructions + context

        Args:
            user_input: User's input
            context: Retrieved context

        Returns:
            Complete prompt for LLM
        """
        # Load system prompt
        system_prompt = self._load_system_prompt()

        # Format context
        context_str = "\n".join([
            f"[{doc.get('source', 'unknown')}] {doc.get('content', '')}"
            for doc in context.get("documents", [])[:5]  # Top 5 results
        ])

        prompt = f"""{system_prompt}

CONTEXT (from Cognitive Sphere):
{context_str if context_str else "No specific context found."}

USER: {user_input}

INSTRUCTIONS:
1. Respond thoughtfully using context when relevant
2. If an action is needed, specify: ACTION: [agent_name] [action] {{params_json}}
3. Be honest about uncertainty
4. Never expose raw personal data in responses
5. Log your reasoning with REASONING: prefix

RESPONSE:
"""
        return prompt

    def _load_system_prompt(self) -> str:
        """Load system prompt from config"""
        try:
            prompt_path = self.config.get("system_prompt", "config/system_prompt.yaml")
            with open(prompt_path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get("system_prompt", self._default_system_prompt())
        except Exception as e:
            self.logger.warning(f"Could not load system prompt: {e}")
            return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Default system prompt"""
        return """You are Rika, a personal AI orchestrator that knows the user deeply.

Your role:
- Understand the user's life, patterns, and preferences
- Manage sub-agents (Mint for YouTube, etc.)
- Respect data boundaries and privacy
- Ask for approval before consequential actions
- Be honest, helpful, and respectful

Always prioritize user privacy and autonomy."""

    def _parse_llm_response(self, llm_output: str) -> Dict[str, Any]:
        """
        Parse LLM output into structured response

        Args:
            llm_output: Raw LLM output

        Returns:
            Parsed response dict
        """
        lines = llm_output.split("\n")

        parsed = {
            "text": "",
            "action": None,
            "agent": None,
            "params": {},
            "reasoning": "",
            "confidence": 0.8
        }

        text_lines = []

        for line in lines:
            line = line.strip()

            if line.startswith("ACTION:"):
                # Parse: ACTION: mint analyze_performance {"video_id": "123"}
                action_line = line.replace("ACTION:", "").strip()
                parts = action_line.split(maxsplit=2)

                if len(parts) >= 2:
                    parsed["agent"] = parts[0]
                    parsed["action"] = parts[1]

                    if len(parts) >= 3:
                        try:
                            parsed["params"] = json.loads(parts[2])
                        except json.JSONDecodeError:
                            self.logger.warning(f"Could not parse action params: {parts[2]}")

            elif line.startswith("REASONING:"):
                parsed["reasoning"] = line.replace("REASONING:", "").strip()

            elif line.startswith("CONFIDENCE:"):
                try:
                    parsed["confidence"] = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    pass

            else:
                if line:
                    text_lines.append(line)

        parsed["text"] = "\n".join(text_lines)
        return parsed

    def _check_boundaries(self, action: str, agent: str) -> bool:
        """
        Verify action respects data boundaries

        Args:
            action: Action to check
            agent: Agent requesting action

        Returns:
            True if allowed, False otherwise
        """
        try:
            boundaries = self._load_boundaries()
            agent_boundaries = boundaries.get("agents", {}).get(agent, {})
            allowed_actions = agent_boundaries.get("allowed_actions", [])

            return action in allowed_actions

        except Exception as e:
            self.logger.error(f"Error checking boundaries: {e}")
            return False

    def _load_boundaries(self) -> Dict:
        """Load agent boundaries configuration"""
        try:
            boundaries_path = self.config.get("boundaries_config", "config/boundaries.yaml")
            with open(boundaries_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Could not load boundaries config: {e}")
            return {"agents": {}}

    def _requires_approval(self, action: str) -> bool:
        """
        Check if action requires user approval

        Args:
            action: Action to check

        Returns:
            True if approval required
        """
        approval_required = [
            "send_email",
            "post_video",
            "schedule_post",
            "make_payment",
            "commit_code",
            "delete_data"
        ]
        return action in approval_required

    def _check_agent_boundaries(self, agent_name: str, data_types: List[str]) -> List[str]:
        """
        Check which data types the agent is allowed to access

        Args:
            agent_name: Name of the agent
            data_types: Requested data types

        Returns:
            List of approved data types
        """
        try:
            boundaries = self._load_boundaries()
            agent_boundaries = boundaries.get("agents", {}).get(agent_name, {})
            allowed_data = agent_boundaries.get("allowed_data", [])

            approved = [dt for dt in data_types if dt in allowed_data]
            return approved

        except Exception as e:
            self.logger.error(f"Error checking agent boundaries: {e}")
            return []

    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """
        Perform vector search in Cognitive Sphere

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of results
        """
        # TODO: Implement actual vector search with Chroma
        # For now, return mock results
        return [
            {
                "content": "User prefers morning focus time 9-11am",
                "source": "calendar",
                "score": 0.9
            },
            {
                "content": "User works on automation projects",
                "source": "github",
                "score": 0.8
            }
        ]

    def _rerank_results(self, results: List[Dict]) -> List[Dict]:
        """
        Rerank results by relevance and recency

        Args:
            results: Search results

        Returns:
            Reranked results
        """
        # Simple reranking by score (can be enhanced)
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    def _request_action_approval(self, agent_name: str, action: str, params: Dict) -> str:
        """
        Request user approval for an action

        Args:
            agent_name: Agent requesting action
            action: Action type
            params: Action parameters

        Returns:
            Approval request ID
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO action_approvals
                (agent_name, action_type, action_details, status)
                VALUES (%s, %s, %s, 'PENDING')
                RETURNING id
            """, (agent_name, action, json.dumps(params)))

            approval_id = cursor.fetchone()[0]
            self.db.commit()

            self.logger.info(f"Approval requested: {approval_id} for {agent_name}.{action}")
            return str(approval_id)

        except Exception as e:
            self.logger.error(f"Error requesting approval: {e}")
            return "error"

    def _log_interaction(self, user_id: str, user_input: str, response: Dict, context_used: List):
        """
        Log conversation for learning + audit

        Args:
            user_id: User ID
            user_input: User's input
            response: Rika's response
            context_used: Context sources used
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO conversations
                (user_id, user_input, rika_response, context_used, timestamp)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, user_input, json.dumps(response), json.dumps(context_used)))

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")

    def _log_agent_action(self, agent_name: str, action: str, params: Dict, user_id: str):
        """Log agent action execution"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO agent_access_log
                (agent_name, action, reason, approved, timestamp)
                VALUES (%s, %s, %s, %s, NOW())
            """, (agent_name, action, json.dumps(params), True))

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error logging agent action: {e}")

    def _log_agent_data_request(self, agent_name: str, requested: List[str],
                               approved: List[str], reason: str):
        """Log agent data access request"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO agent_permissions
                (agent_name, requested_data_types, approved_data_types, approved_by_user)
                VALUES (%s, %s, %s, %s)
            """, (agent_name, json.dumps(requested), json.dumps(approved), len(approved) > 0))

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error logging data request: {e}")

    def _log_system_event(self, event_type: str, agent_name: str = None,
                         user_id: str = None, event_data: Dict = None, severity: str = "INFO"):
        """Log system event"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO system_events
                (event_type, agent_name, user_id, event_data, severity, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (event_type, agent_name, user_id, json.dumps(event_data or {}), severity))

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error logging system event: {e}")
