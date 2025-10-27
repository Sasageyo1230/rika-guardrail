"""
Phase 2 Integration Tests
Tests for Rika Orchestrator, Cognitive Sphere, and Mint agent
"""

import pytest
import json
import yaml
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Import Phase 2 components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rika.cognitive_sphere.ingestor import CognitiveSphereIngestor
from rika.orchestrator_v2 import RikaOrchestrator
from rika.agents.mint import MintAgent
from rika.agents.access_control import AgentAccessControl
from rika.llm.inference import RikaLLM, MockLLM


# Fixtures

@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = [1]
    db.cursor.return_value = cursor
    return db


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    vector_store = MagicMock()
    vector_store.similarity_search_with_score.return_value = [
        {
            "content": "User prefers morning focus time",
            "source": "calendar",
            "score": 0.9
        }
    ]
    return vector_store


@pytest.fixture
def mock_encryption():
    """Mock encryption manager"""
    encryption = MagicMock()
    encryption.encrypt.return_value = b"encrypted_data"
    encryption.decrypt.return_value = "decrypted_data"
    return encryption


@pytest.fixture
def mock_auth():
    """Mock authentication manager"""
    auth = MagicMock()
    auth.verify_token.return_value = "test_user"
    return auth


@pytest.fixture
def mock_llm():
    """Mock LLM"""
    return MockLLM()


@pytest.fixture
def boundaries_config():
    """Load boundaries configuration"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'boundaries.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return default config if file not found
        return {
            "agents": {
                "mint": {
                    "name": "Mint",
                    "allowed_data": ["youtube_channel_info", "video_analytics"],
                    "blocked_data": ["email_content"],
                    "allowed_actions": ["analyze_performance", "schedule_post"],
                    "approval_required": ["schedule_post"]
                }
            }
        }


@pytest.fixture
def orchestrator(mock_db, mock_vector_store, mock_llm, mock_auth, mock_encryption):
    """Create orchestrator instance"""
    # Create temp config
    config = {
        "llm_model_path": "models/test.gguf",
        "boundaries_config": "config/boundaries.yaml",
        "system_prompt": "config/system_prompt.yaml"
    }

    rika = RikaOrchestrator.__new__(RikaOrchestrator)
    rika.config = config
    rika.db = mock_db
    rika.vector_store = mock_vector_store
    rika.llm = mock_llm
    rika.auth_manager = mock_auth
    rika.encryption_manager = mock_encryption
    rika.agents = {}
    rika.data_access_log = []
    rika.logger = MagicMock()

    return rika


# Tests

class TestCognitiveSphereIngestor:
    """Test Cognitive Sphere data ingestion"""

    def test_ingestor_initialization(self, mock_db, mock_vector_store, mock_encryption):
        """Test ingestor initializes correctly"""
        ingestor = CognitiveSphereIngestor(mock_db, mock_vector_store, mock_encryption)
        assert ingestor.db == mock_db
        assert ingestor.vector_store == mock_vector_store
        assert ingestor.encryption == mock_encryption

    def test_ingest_emails(self, mock_db, mock_vector_store, mock_encryption):
        """Test email ingestion"""
        ingestor = CognitiveSphereIngestor(mock_db, mock_vector_store, mock_encryption)

        # Ingest with mock data (no gmail connection)
        result = ingestor.ingest_emails(gmail_connection=None, limit=10)

        assert result["emails_processed"] >= 0
        assert "relationships_identified" in result
        assert "topics_extracted" in result

    def test_ingest_calendar(self, mock_db, mock_vector_store, mock_encryption):
        """Test calendar ingestion"""
        ingestor = CognitiveSphereIngestor(mock_db, mock_vector_store, mock_encryption)

        result = ingestor.ingest_calendar(calendar_connection=None)

        assert result["events_processed"] >= 0
        assert "patterns_identified" in result

    def test_ingest_code_repositories(self, mock_db, mock_vector_store, mock_encryption):
        """Test code repository ingestion"""
        ingestor = CognitiveSphereIngestor(mock_db, mock_vector_store, mock_encryption)

        result = ingestor.ingest_code_repositories(github_token=None)

        assert "repos_analyzed" in result
        assert "patterns_identified" in result

    def test_build_cognitive_profile(self, mock_db, mock_vector_store, mock_encryption):
        """Test cognitive profile building"""
        ingestor = CognitiveSphereIngestor(mock_db, mock_vector_store, mock_encryption)

        profile = ingestor.build_cognitive_profile()

        assert "working_style" in profile
        assert "communication_style" in profile
        assert "values" in profile
        assert "patterns" in profile
        assert "preferences" in profile


class TestRikaOrchestrator:
    """Test Rika Orchestrator"""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator.db is not None
        assert orchestrator.llm is not None
        assert orchestrator.agents == {}

    def test_register_agent(self, orchestrator, mock_db, mock_encryption):
        """Test agent registration"""
        orchestrator.register_agent("mint", MintAgent)

        assert "mint" in orchestrator.agents
        assert isinstance(orchestrator.agents["mint"], MintAgent)

    def test_retrieve_context(self, orchestrator):
        """Test context retrieval from Cognitive Sphere"""
        context = orchestrator.retrieve_context("What's on my calendar?")

        assert "documents" in context
        assert "sources" in context
        assert isinstance(context["documents"], list)

    def test_process_request_simple(self, orchestrator):
        """Test simple request processing"""
        response = orchestrator.process_request(
            user_input="What's my schedule like?",
            session_token="valid_token"
        )

        assert response["status"] == "SUCCESS"
        assert "response" in response
        assert "confidence" in response

    def test_process_request_with_action(self, orchestrator, mock_db, mock_encryption):
        """Test request that triggers an action"""
        # Register Mint agent
        orchestrator.register_agent("mint", MintAgent)

        # Mock LLM to return action
        orchestrator.llm.generate = lambda prompt: """
        I'll analyze your YouTube performance.

        ACTION: mint analyze_performance {"limit": 10}

        REASONING: User asked about YouTube
        CONFIDENCE: 0.9
        """

        response = orchestrator.process_request(
            user_input="How are my YouTube videos doing?",
            session_token="valid_token"
        )

        assert response["status"] in ["SUCCESS", "PENDING_APPROVAL"]

    def test_authentication_failure(self, orchestrator):
        """Test request with invalid token"""
        orchestrator.auth_manager.verify_token.return_value = None

        response = orchestrator.process_request(
            user_input="Test",
            session_token="invalid_token"
        )

        assert response["status"] == "DENIED"


class TestMintAgent:
    """Test Mint agent"""

    def test_mint_initialization(self, mock_db, mock_encryption, orchestrator):
        """Test Mint agent initializes"""
        mint = MintAgent(orchestrator, mock_db, mock_encryption)
        mint.initialize()

        assert mint.youtube_client is not None

    def test_analyze_performance(self, mock_db, mock_encryption, orchestrator):
        """Test video performance analysis"""
        mint = MintAgent(orchestrator, mock_db, mock_encryption)
        mint.initialize()

        result = mint.analyze_video_performance({"limit": 5})

        assert result["status"] == "SUCCESS"
        assert "data" in result
        assert "recommendation" in result

    def test_suggest_post_time(self, mock_db, mock_encryption, orchestrator):
        """Test optimal post time suggestion"""
        mint = MintAgent(orchestrator, mock_db, mock_encryption)
        mint.initialize()

        result = mint.suggest_optimal_post_time()

        assert result["status"] == "SUCCESS"
        assert "optimal_times" in result

    def test_generate_thumbnail(self, mock_db, mock_encryption, orchestrator):
        """Test thumbnail generation"""
        mint = MintAgent(orchestrator, mock_db, mock_encryption)

        result = mint.generate_thumbnail({
            "title": "How to Build AI Agents",
            "description": "Tutorial on building AI agents"
        })

        assert result["status"] == "SUCCESS"
        assert "thumbnail_suggestion" in result

    def test_execute_unknown_action(self, mock_db, mock_encryption, orchestrator):
        """Test unknown action handling"""
        mint = MintAgent(orchestrator, mock_db, mock_encryption)

        result = mint.execute("unknown_action", {}, "test_user")

        assert result["status"] == "ERROR"


class TestAgentAccessControl:
    """Test agent access control"""

    def test_access_control_initialization(self, boundaries_config):
        """Test access control initializes"""
        access_control = AgentAccessControl(boundaries_config)
        assert access_control.boundaries == boundaries_config

    def test_can_agent_access_allowed(self, boundaries_config):
        """Test allowed data access"""
        access_control = AgentAccessControl(boundaries_config)

        # Mint should access YouTube data
        assert access_control.can_agent_access("mint", "youtube_channel_info")

    def test_can_agent_access_blocked(self, boundaries_config):
        """Test blocked data access"""
        access_control = AgentAccessControl(boundaries_config)

        # Mint should NOT access email
        assert not access_control.can_agent_access("mint", "email_content")

    def test_can_agent_perform_action(self, boundaries_config):
        """Test action permissions"""
        access_control = AgentAccessControl(boundaries_config)

        # Mint should perform analysis
        assert access_control.can_agent_perform_action("mint", "analyze_performance")

    def test_requires_approval(self, boundaries_config):
        """Test approval requirements"""
        access_control = AgentAccessControl(boundaries_config)

        # schedule_post should require approval
        assert access_control.requires_approval("mint", "schedule_post")

        # analyze_performance should not
        assert not access_control.requires_approval("mint", "analyze_performance")

    def test_request_data_access(self, boundaries_config):
        """Test data access request"""
        access_control = AgentAccessControl(boundaries_config)

        result = access_control.request_data_access(
            "mint",
            ["youtube_channel_info", "email_content"],
            "Need data for analysis"
        )

        assert "youtube_channel_info" in result["approved"]
        assert "email_content" in result["denied"]

    def test_validate_action_request(self, boundaries_config):
        """Test action validation"""
        access_control = AgentAccessControl(boundaries_config)

        # Valid action
        result = access_control.validate_action_request(
            "mint",
            "analyze_performance",
            ["youtube_channel_info"]
        )

        assert result["allowed"]

        # Invalid action
        result = access_control.validate_action_request(
            "mint",
            "invalid_action",
            []
        )

        assert not result["allowed"]


class TestLLMInference:
    """Test LLM inference"""

    def test_mock_llm_generate(self):
        """Test mock LLM generation"""
        llm = MockLLM()

        response = llm.generate("What's on my calendar?")

        assert isinstance(response, str)
        assert len(response) > 0

    def test_mock_llm_embed(self):
        """Test mock LLM embedding"""
        llm = MockLLM()

        embedding = llm.embed("Test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_rika_llm_initialization(self):
        """Test Rika LLM initialization"""
        llm = RikaLLM(model_path="test.gguf")
        llm.initialize()

        assert llm.model is not None

    def test_rika_llm_generate(self):
        """Test Rika LLM generation with mock"""
        llm = RikaLLM(model_path="test.gguf")
        llm.initialize()

        response = llm.generate("Test prompt")

        assert isinstance(response, str)


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_full_request_flow(self, orchestrator, mock_db, mock_encryption):
        """Test complete request flow"""
        # 1. Register Mint agent
        orchestrator.register_agent("mint", MintAgent)

        # 2. Process request
        response = orchestrator.process_request(
            user_input="What's my schedule like?",
            session_token="valid_token"
        )

        # 3. Verify response
        assert response["status"] in ["SUCCESS", "ERROR"]
        assert "response" in response

    def test_agent_data_access_enforcement(self, orchestrator, boundaries_config,
                                          mock_db, mock_encryption):
        """Test that agent data access is enforced"""
        # Register Mint agent
        orchestrator.register_agent("mint", MintAgent)

        # Request data access
        mint = orchestrator.agents["mint"]

        # Mint should get YouTube data
        result = orchestrator.request_agent_data_access(
            "mint",
            ["youtube_channel_info"],
            "Need for analysis"
        )

        assert "youtube_channel_info" in result

    def test_approval_workflow(self, orchestrator, mock_db, mock_encryption):
        """Test approval workflow for actions"""
        # Register Mint agent
        orchestrator.register_agent("mint", MintAgent)

        # Execute action requiring approval
        result = orchestrator.execute_action(
            action="schedule_post",
            agent_name="mint",
            params={"title": "Test Video"},
            user_id="test_user"
        )

        # Should be pending approval
        assert result["status"] in ["PENDING_APPROVAL", "ERROR"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
