# Rika Phase 3.3 🚀

**Advanced Agent Ecosystem with Enhanced Capabilities**

Phase 3.3 represents a significant evolution of the Rika agent system, introducing sophisticated UI/UX enhancements, creative power tools, advanced security hardening, chaos testing capabilities, and a comprehensive knowledge vault system.

## 🌟 What's New in Phase 3.3

### Part A: UI/UX Polish
- **Agent-Specific Visual Identity**: Each agent (Rig, Craft, Scout, Echo, Pulse, Atlas) has distinct colors, animations, and voice synthesis
- **Enhanced HUD System**: Smooth bubble animations, presence banners, and status watermarks
- **Advanced Chat Panel**: Streaming message display, citation management, and code highlighting
- **Smart Command Palette**: Searchable actions with parameter forms and intelligent suggestions

### Part B: Creative Power Tools
- **Rig Blender Integration**: Python API helpers for modeling, rigging, and automation workflows
- **Craft Storyboard Generator**: Automated storyboard creation from scripts with visual composition analysis
- **Script-to-Scenes Pipeline**: Intelligent script parsing with emotional arc analysis and character mapping
- **Task Progress Management**: Advanced task drawer with progress tracking, logs, and retry mechanisms

### Part C: Overseer Hardening
- **Granular Security Policies**: Fine-grained capability management per agent with dynamic policy updates
- **Behavioral Anomaly Detection**: Machine learning-based threat detection with adaptive response
- **Tamper-Evident Auditing**: Comprehensive security logging with integrity verification
- **Risk Assessment Engine**: Real-time risk evaluation with automated threat response

### Part D: Chaos Testing & Auto-Recovery
- **Intelligent Fault Injection**: Configurable failure scenarios with realistic fault simulation
- **Circuit Breaker Patterns**: Automatic failure isolation and recovery orchestration
- **Self-Healing Components**: Automated recovery workflows with predictive failure detection
- **Resilience Metrics**: Comprehensive fault tolerance scoring and improvement recommendations

### Part E: Scout Knowledge Vault
- **Semantic Search Engine**: Vector-based knowledge retrieval with Qdrant integration
- **Persistent Storage**: MinIO object storage for files with metadata management
- **Daily/Weekly Digests**: Automated knowledge summaries with trend analysis
- **Atlas Integration**: Seamless knowledge access through enhanced Atlas dashboard

## 🏗️ Architecture Overview

```
Rika Phase 3.3/
├── 🎨 UI Layer (Next.js + React)
│   ├── Enhanced HUD Components
│   ├── Agent-Specific Theming
│   ├── Advanced Interactions
│   └── Atlas Dashboard Integration
│
├── 🔧 Agent Layer (Python)
│   ├── Rig (Device Control + Blender)
│   ├── Craft (Code + Storyboards)
│   ├── Scout (Research + Knowledge)
│   ├── Echo (Communication Hub)
│   ├── Pulse (System Monitoring)
│   └── Atlas (Central Coordination)
│
├── 🛡️ Security Layer
│   ├── Capability Policies Engine
│   ├── Anomaly Detection System
│   ├── Audit & Compliance
│   └── Risk Assessment
│
├── 🔄 Resilience Layer
│   ├── Chaos Testing Framework
│   ├── Fault Injection Engine
│   ├── Auto-Recovery System
│   └── Health Monitoring
│
└── 📚 Knowledge Layer
    ├── Vector Database (Qdrant)
    ├── Object Storage (MinIO)
    ├── Semantic Search Engine
    └── Content Management
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm 9+
- **Python** 3.9+ with pip
- **Optional**: Docker (for Qdrant/MinIO), Git, Blender

### Windows-First Setup

1. **Clone and Navigate**
   ```powershell
   git clone <rika-repository>
   cd rika-core/phase3.3
   ```

2. **Run Setup Script**
   ```powershell
   # Development environment
   .\scripts\setup.ps1 -Development -Verbose
   
   # Production environment  
   .\scripts\setup.ps1 -Production -Environment production
   
   # Clean install
   .\scripts\setup.ps1 -Clean -Development
   ```

3. **Start Development Environment**
   ```powershell
   .\scripts\start-dev.ps1
   ```

4. **Access Applications**
   - **UI Dashboard**: http://localhost:3000
   - **API Backend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

### Manual Setup (if needed)

<details>
<summary>Click to expand manual setup instructions</summary>

1. **Install Python Dependencies**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

2. **Install Node.js Dependencies**
   ```powershell
   cd ui
   npm install
   cd ..
   ```

3. **Setup Optional Services**
   ```powershell
   # Start Qdrant (vector database)
   docker run -p 6333:6333 qdrant/qdrant
   
   # Start MinIO (object storage)
   docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
   ```

4. **Initialize Configuration**
   ```powershell
   # Configuration files are auto-created on first run
   # Customize config/rika_config.json as needed
   ```

</details>

## 🧪 Testing

### Run All Tests
```powershell
.\scripts\run-tests.ps1 -TestType all -Verbose -Coverage
```

### Specific Test Types
```powershell
# Python tests only
.\scripts\run-tests.ps1 -TestType python

# Node.js tests only  
.\scripts\run-tests.ps1 -TestType node

# Integration tests
.\scripts\run-tests.ps1 -TestType integration
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction testing
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability and penetration testing

## 📖 Component Documentation

### 🎨 UI Components

**Enhanced HUD System**
```typescript
// Agent-specific bubble with voice synthesis
<EnhancedBubble
  agent="rig"
  message="Blender workflow completed"
  priority="high"
  duration={5000}
  enableVoice={true}
/>

// Status banner with system mode
<StatusBanner
  mode="hands-on"
  agent="rig" 
  message="Device control active"
  position="top"
/>
```

**Advanced Chat Panel**
```typescript
// Streaming chat with citations
<EnhancedChatPanel
  enableStreaming={true}
  showCitations={true}
  enableCodeHighlight={true}
  agents={["rig", "craft", "scout"]}
/>
```

### 🔧 Agent Tools

**Rig Blender Integration**
```python
from agents.rig.blender_tools import RigWorkflowManager

# Create character workflow
workflow = RigWorkflowManager()
character = workflow.create_character_base("MyCharacter")

# Export for game engine
workflow.batch_export_for_game("./exports", "MyProject")
```

**Craft Storyboard Generation**
```python
from agents.craft.storyboarder import CraftStoryboardManager

# Generate storyboard from script
manager = CraftStoryboardManager()
storyboard = manager.create_storyboard_from_script("script.txt", "MyProject")
manager.export_storyboard(storyboard, ['html', 'json'])
```

### 🛡️ Security System

**Capability Policies**
```python
from core.security.capability_policies import PolicyEngine, SecurityContext

# Evaluate agent capability
engine = PolicyEngine()
allowed, capability, rules = await engine.evaluate_capability(
    agent_id="rig_001",
    action_type=ActionType.FILE_WRITE,
    resource="/project/files/model.blend",
    context=security_context
)
```

**Anomaly Detection**
```python
from core.security.anomaly_detection import AnomalyDetector

# Monitor agent behavior
detector = AnomalyDetector()
anomalies = await detector.detect_anomalies(agent_id, current_activity)
```

### 🔄 Chaos Testing

**Fault Injection**
```python
from core.chaos.fault_injection import FaultInjector

# Execute with fault tolerance
injector = FaultInjector()
result = await injector.execute_with_fault_tolerance(
    your_function,
    agent_id="test_agent", 
    operation="critical_task"
)
```

### 📚 Knowledge Vault

**Semantic Search**
```python
from agents.scout.knowledge_vault import KnowledgeVault

# Search knowledge base
vault = KnowledgeVault()
results = await vault.search_knowledge(
    "machine learning best practices",
    limit=10,
    category="ai-ml"
)
```

## 🌐 Production Deployment

### Docker Deployment
```yaml
# docker-compose.yml example
version: '3.8'
services:
  rika-api:
    build: .
    ports: ["8000:8000"]
    environment:
      - ENVIRONMENT=production
  
  rika-ui:
    build: ./ui
    ports: ["3000:3000"]
  
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
  
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
    command: server /data --console-address ":9001"
```

### Windows Service Setup
```powershell
# Create Windows service (run as administrator)
sc create "RikaPhase33" binPath="C:\path\to\rika\scripts\start-prod.ps1"
sc config "RikaPhase33" start=auto
sc start "RikaPhase33"
```

### Environment Configuration
```json
{
  "environment": "production",
  "services": {
    "minio": {
      "endpoint": "production-minio:9000",
      "access_key": "${MINIO_ACCESS_KEY}",
      "secret_key": "${MINIO_SECRET_KEY}"
    },
    "qdrant": {
      "host": "production-qdrant",
      "port": 6333
    }
  },
  "security": {
    "policies_enabled": true,
    "anomaly_detection": true,
    "audit_logging": true
  }
}
```

## 🔧 Development Guide

### Adding New Agents
1. Create agent directory: `agents/myagent/`
2. Implement base agent class with required methods
3. Add agent configuration to `config/rika_config.json`
4. Create UI components in `ui/components/Agents/`
5. Add agent-specific styling to `ui/styles/agents.css`

### Creating Custom Tools
1. Extend appropriate base tool class
2. Implement required methods and interfaces
3. Add tool registration in agent initialization
4. Create UI integration components
5. Write comprehensive tests

### Security Policy Development
1. Define capability requirements
2. Create policy rules in JSON format
3. Test with security evaluation engine
4. Deploy through configuration management
5. Monitor through audit logging

## 📊 Monitoring & Analytics

### Health Metrics
- **Agent Status**: Real-time health monitoring
- **Performance**: Response times, throughput, resource usage
- **Security**: Policy violations, anomaly detections, audit events
- **Resilience**: Fault injection results, recovery success rates

### Dashboard Access
- **Atlas Dashboard**: Comprehensive system overview
- **Security Center**: Policy management and threat monitoring  
- **Chaos Engineering**: Fault injection and resilience testing
- **Knowledge Analytics**: Search patterns and content insights

## 🤝 Contributing

### Development Workflow
1. Fork repository and create feature branch
2. Implement changes with comprehensive tests
3. Run full test suite: `.\scripts\run-tests.ps1 -Coverage`
4. Update documentation as needed
5. Submit pull request with detailed description

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **TypeScript**: ESLint/Prettier, strict mode, component documentation
- **Testing**: >90% coverage, integration tests for new features
- **Security**: Security review for all changes, no hardcoded secrets

## 📚 Resources

### Documentation
- [Agent Development Guide](docs/agents.md)
- [Security Framework](docs/security.md)
- [API Reference](docs/api.md)
- [UI Component Library](docs/components.md)

### External Dependencies
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Qdrant Vector Database](https://qdrant.tech/documentation/)
- [MinIO Object Storage](https://docs.min.io/)

## 🐛 Troubleshooting

### Common Issues

**Setup Script Fails**
```powershell
# Check system requirements
.\scripts\setup.ps1 -Verbose

# Clean and retry
.\scripts\setup.ps1 -Clean -Development
```

**Service Connection Errors**
```powershell
# Check service status
docker ps  # For containerized services
netstat -an | findstr "6333\|9000"  # Check port availability
```

**Import Errors**
```powershell
# Verify virtual environment
.\venv\Scripts\Activate.ps1
python -c "import sys; print(sys.path)"
pip list  # Check installed packages
```

### Performance Optimization
- Enable Redis caching for knowledge vault
- Configure Qdrant with appropriate hardware
- Use CDN for static assets in production
- Monitor resource usage and scale accordingly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Rika Phase 3.3** - Building the future of intelligent agent systems 🚀

For support, questions, or contributions, please visit our [GitHub repository](https://github.com/your-org/rika) or contact the development team.