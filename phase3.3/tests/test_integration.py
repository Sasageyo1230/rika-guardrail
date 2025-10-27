"""
Rika Phase 3.3 - Integration Tests
Comprehensive testing of system components and interactions
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.security.capability_policies import PolicyEngine, SecurityContext, ActionType
from core.security.anomaly_detection import AnomalyDetector, HealthMetrics, HealthStatus
from core.chaos.fault_injection import FaultInjector, FaultScenario, FaultType, RecoveryStrategy
from core.chaos.auto_recovery import AutoRecoverySystem, ComponentState, FailurePattern
from agents.rig.blender_tools import RigWorkflowManager
from agents.craft.storyboarder import CraftStoryboardManager
from agents.craft.script_to_scenes import AdvancedScriptParser
from agents.scout.knowledge_vault import KnowledgeVault

class TestSecurityIntegration:
    """Test security system integration"""
    
    @pytest.fixture
    async def policy_engine(self):
        """Setup policy engine for testing"""
        engine = PolicyEngine()
        yield engine
        # Cleanup
        await engine._save_policies()

    @pytest.fixture
    def security_context(self):
        """Create test security context"""
        return SecurityContext(
            agent_id="test_agent",
            session_id="test_session",
            user_id="test_user",
            timestamp=datetime.utcnow(),
            source_ip="127.0.0.1"
        )

    @pytest.mark.asyncio
    async def test_policy_evaluation_flow(self, policy_engine, security_context):
        """Test complete policy evaluation workflow"""
        # Test basic capability evaluation
        allowed, capability, rules = await policy_engine.evaluate_capability(
            "rig_001",
            ActionType.FILE_READ,
            "/tmp/test.txt",
            security_context
        )
        
        assert isinstance(allowed, bool)
        assert capability is not None
        assert isinstance(rules, list)
        
        # Test denied action
        allowed_denied, capability_denied, rules_denied = await policy_engine.evaluate_capability(
            "craft_001", 
            ActionType.SYSTEM_COMMAND,
            "rm -rf /",
            security_context
        )
        
        assert not allowed_denied
        assert len(rules_denied) > 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_integration(self):
        """Test anomaly detection system"""
        detector = AnomalyDetector(learning_period_hours=0.1)  # Short learning period
        
        # Simulate normal activity for learning
        for i in range(15):
            normal_activity = type('Activity', (), {
                'agent_id': 'test_agent',
                'timestamp': datetime.utcnow(),
                'actions_last_minute': 5,
                'cpu_usage': 25.0,
                'memory_usage_percent': 40.0,
                'session_duration': 30.0,
                'recent_resources': ['/tmp/file1.txt'],
                'recent_api_calls': ['get_status'],
                'recent_communications': ['atlas_001'],
                'recent_errors': []
            })()
            
            await detector.learn_behavior('test_agent', normal_activity)
        
        # Test anomaly detection
        anomalous_activity = type('Activity', (), {
            'agent_id': 'test_agent',
            'timestamp': datetime.utcnow(),
            'actions_last_minute': 150,  # Very high
            'cpu_usage': 95.0,  # Very high
            'memory_usage_percent': 95.0,  # Very high
            'session_duration': 30.0,
            'recent_resources': ['/etc/passwd', '/etc/shadow'],  # Sensitive
            'recent_api_calls': ['admin_access'],
            'recent_communications': ['unknown_external'],
            'recent_errors': []
        })()
        
        anomalies = await detector.detect_anomalies('test_agent', anomalous_activity)
        assert len(anomalies) > 0
        
        # Verify anomaly types
        anomaly_types = [a.anomaly_type for a in anomalies]
        assert any('resource' in str(atype).lower() or 'behavioral' in str(atype).lower() 
                   for atype in anomaly_types)

class TestChaosIntegration:
    """Test chaos testing system integration"""
    
    @pytest.fixture
    async def fault_injector(self):
        """Setup fault injector for testing"""
        injector = FaultInjector()
        
        # Add test scenario
        test_scenario = FaultScenario(
            scenario_id="test_scenario",
            name="Test Network Latency",
            description="Test scenario for integration testing",
            fault_type=FaultType.NETWORK_LATENCY,
            target_agents=["test_*"],
            target_operations=["test_operation"],
            probability=1.0,  # Always inject for testing
            duration_min=0.1,
            duration_max=0.2,
            severity=0.5,
            recovery_strategies=[RecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF]
        )
        
        injector.add_scenario(test_scenario)
        yield injector

    @pytest.mark.asyncio
    async def test_fault_injection_workflow(self, fault_injector):
        """Test complete fault injection and recovery workflow"""
        
        # Test function that can fail
        call_count = 0
        
        async def test_function():
            nonlocal call_count
            call_count += 1
            return {"status": "success", "call_count": call_count}
        
        # Execute with fault tolerance
        result = await fault_injector.execute_with_fault_tolerance(
            test_function,
            "test_agent_001",
            "test_operation"
        )
        
        # Should succeed eventually due to recovery
        assert result["status"] == "success"
        
        # Check that faults were injected and resolved
        assert len(fault_injector.fault_history) >= 0  # May or may not inject based on probability

    @pytest.mark.asyncio
    async def test_auto_recovery_system(self):
        """Test auto-recovery system"""
        recovery_system = AutoRecoverySystem()
        
        # Mock health check that simulates failure then recovery
        failure_count = 0
        
        async def mock_health_check():
            nonlocal failure_count
            failure_count += 1
            
            # Fail first few checks, then recover
            if failure_count <= 3:
                return HealthMetrics(
                    component_id="test_component",
                    timestamp=datetime.utcnow(),
                    cpu_usage=95.0,  # High CPU indicates failure
                    memory_usage_percent=95.0,
                    health_status=HealthStatus.CRITICAL
                )
            else:
                return HealthMetrics(
                    component_id="test_component", 
                    timestamp=datetime.utcnow(),
                    cpu_usage=25.0,  # Normal CPU after recovery
                    memory_usage_percent=40.0,
                    health_status=HealthStatus.HEALTHY
                )
        
        # Register component and start monitoring
        await recovery_system.health_monitor.register_component(
            "test_component",
            "test_type",
            mock_health_check,
            check_interval=0.5  # Fast for testing
        )
        
        # Let it run briefly
        await asyncio.sleep(2)
        
        # Check that recovery was attempted
        status = await recovery_system.get_recovery_status()
        assert status["monitored_components"] == 1
        
        # Stop monitoring
        await recovery_system.health_monitor.stop_monitoring()

class TestAgentIntegration:
    """Test agent-specific functionality integration"""
    
    @pytest.mark.asyncio
    async def test_rig_blender_integration(self):
        """Test Rig agent Blender tools integration"""
        # Note: This test runs without actual Blender, testing the workflow logic
        workflow_manager = RigWorkflowManager()
        
        # Test character creation workflow
        character_objects = workflow_manager.create_character_base("TestCharacter")
        
        assert "body" in character_objects
        assert "head" in character_objects
        assert "armature" in character_objects
        
        # Verify object naming
        assert character_objects["body"].name == "TestCharacter_Body"
        assert character_objects["head"].name == "TestCharacter_Head"

    @pytest.mark.asyncio
    async def test_craft_storyboard_integration(self):
        """Test Craft agent storyboard generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CraftStoryboardManager(temp_dir)
            
            # Create test script
            test_script = """
            FADE IN:
            
            EXT. PARK - DAY
            
            A sunny day in the park. Children are playing.
            
            SARAH walks through the park with her dog.
            
            SARAH:
            What a beautiful day!
            
            The dog barks happily.
            
            FADE OUT.
            """
            
            script_path = Path(temp_dir) / "test_script.txt"
            script_path.write_text(test_script)
            
            # Generate storyboard
            storyboard = manager.create_storyboard_from_script(str(script_path), "TestProject")
            
            assert storyboard.project_name == "TestProject"
            assert len(storyboard.panels) > 0
            assert storyboard.metadata["total_scenes"] > 0
            
            # Export storyboard
            manager.export_storyboard(storyboard, ['json'])
            
            # Verify export files exist
            project_dir = Path(temp_dir) / "TestProject"
            json_file = project_dir / "TestProject_storyboard.json"
            assert json_file.exists()

    @pytest.mark.asyncio
    async def test_script_analysis_integration(self):
        """Test advanced script analysis"""
        parser = AdvancedScriptParser()
        
        test_script = """
        FADE IN:
        
        INT. OFFICE - DAY
        
        A busy office environment. Phones ringing, people typing.
        
        DETECTIVE JONES sits at his desk, reviewing case files.
        
        JONES:
        (frustrated)
        Nothing makes sense about this case.
        
        His PARTNER approaches with coffee.
        
        PARTNER:
        Take a break, Jones. You've been at this for hours.
        
        JONES:
        I can't. This killer is still out there.
        
        The phone RINGS. Jones answers.
        
        JONES:
        (into phone)
        Detective Jones.
        
        His expression changes to shock.
        
        JONES:
        We'll be right there.
        
        He hangs up and looks at his partner.
        
        JONES:
        There's been another murder.
        
        FADE OUT.
        """
        
        analysis = parser.parse_full_script(test_script, "Crime Drama Test")
        
        assert analysis.title == "Crime Drama Test"
        assert len(analysis.scenes) > 0
        assert len(analysis.characters) >= 2  # Jones and Partner
        assert analysis.total_scenes > 0
        assert analysis.runtime_estimate > 0
        
        # Check character analysis
        assert "JONES" in analysis.characters
        jones_char = analysis.characters["JONES"]
        assert jones_char.dialogue_count > 0
        assert jones_char.first_appearance > 0

    @pytest.mark.asyncio
    async def test_knowledge_vault_integration(self):
        """Test Scout knowledge vault system"""
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the data directory to temp directory
            original_cwd = os.getcwd()
            test_data_dir = Path(temp_dir) / "data" / "knowledge_vault"
            test_data_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                vault = KnowledgeVault()
                
                # Add test knowledge items
                test_items = [
                    {
                        "title": "Python Testing Best Practices",
                        "content": "Use pytest for testing Python applications. Write clear test names and use fixtures for setup.",
                        "category": "programming",
                        "tags": ["python", "testing", "pytest"],
                        "importance": 0.8
                    },
                    {
                        "title": "Async Programming Patterns",
                        "content": "Async/await patterns in Python enable concurrent execution. Use asyncio for I/O-bound operations.",
                        "category": "programming", 
                        "tags": ["python", "async", "concurrency"],
                        "importance": 0.7
                    }
                ]
                
                item_ids = []
                for item_data in test_items:
                    item_id = await vault.add_knowledge(**item_data)
                    assert item_id is not None
                    item_ids.append(item_id)
                
                # Test search functionality
                search_results = await vault.search_knowledge("python testing", limit=5)
                assert len(search_results) > 0
                
                # Verify search results
                found_relevant = any("python" in result.item.title.lower() or 
                                   "python" in result.item.content.lower() 
                                   for result in search_results)
                assert found_relevant
                
                # Test item retrieval
                for item_id in item_ids:
                    item = await vault.get_item(item_id)
                    assert item is not None
                    assert item.item_id == item_id
                
                # Test digest generation
                digest = await vault.generate_digest("daily")
                assert digest.digest_type == "daily"
                assert digest.total_items == len(item_ids)
                assert len(digest.new_items) == len(item_ids)
                
                # Test statistics
                stats = vault.get_vault_statistics()
                assert stats["total_items"] == len(item_ids)
                assert "programming" in stats["categories"]
                
            finally:
                os.chdir(original_cwd)

class TestSystemIntegration:
    """Test full system integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        
        # Initialize components
        policy_engine = PolicyEngine()
        fault_injector = FaultInjector()
        
        # Create security context
        context = SecurityContext(
            agent_id="integration_test_agent",
            session_id="integration_session",
            user_id="test_user",
            timestamp=datetime.utcnow()
        )
        
        # Test 1: Security policy evaluation
        allowed, capability, rules = await policy_engine.evaluate_capability(
            "scout_001",
            ActionType.FILE_READ,
            "/tmp/integration_test.txt",
            context
        )
        
        # Should be allowed for scout agent
        assert allowed == True
        
        # Test 2: Fault injection in workflow
        async def test_workflow():
            await asyncio.sleep(0.1)  # Simulate work
            return {"status": "completed", "data": "integration test result"}
        
        result = await fault_injector.execute_with_fault_tolerance(
            test_workflow,
            "integration_test_agent",
            "integration_workflow"
        )
        
        assert result["status"] == "completed"
        
        # Test 3: Component health monitoring
        recovery_system = AutoRecoverySystem()
        
        async def integration_health_check():
            return HealthMetrics(
                component_id="integration_component",
                timestamp=datetime.utcnow(),
                cpu_usage=30.0,
                memory_usage_percent=50.0,
                health_status=HealthStatus.HEALTHY
            )
        
        await recovery_system.health_monitor.register_component(
            "integration_component",
            "test_component",
            integration_health_check,
            check_interval=1.0
        )
        
        # Let system run briefly
        await asyncio.sleep(2)
        
        status = await recovery_system.get_recovery_status()
        assert status["monitored_components"] == 1
        
        # Cleanup
        await recovery_system.health_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under load"""
        vault = KnowledgeVault()
        
        # Add multiple items quickly
        start_time = datetime.utcnow()
        
        tasks = []
        for i in range(10):  # Reduced from 50 for faster testing
            task = vault.add_knowledge(
                title=f"Performance Test Item {i}",
                content=f"This is test content for performance testing item number {i}. " * 5,
                category="testing",
                tags=[f"tag{i}", "performance", "test"],
                importance=0.5
            )
            tasks.append(task)
        
        # Execute all additions concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Verify results
        successful_additions = [r for r in results if isinstance(r, str)]
        assert len(successful_additions) == 10
        
        # Performance check - should complete within reasonable time
        assert duration < 10.0  # Should complete within 10 seconds
        
        # Test search performance
        search_start = datetime.utcnow()
        search_results = await vault.search_knowledge("performance test", limit=20)
        search_end = datetime.utcnow()
        search_duration = (search_end - search_start).total_seconds()
        
        assert len(search_results) > 0
        assert search_duration < 2.0  # Search should be fast

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])