# 🚀 Rika Project - Complete AI Ecosystem

**Phase 3.1 + 3.2 Implementation**

Rika is a comprehensive AI ecosystem featuring workflow automation, multi-agent personalities, environmental control, advanced research capabilities, and strategic reflection—all with built-in safety controls.

## 🌟 What's New in Phase 3.1 + 3.2

### Phase 3.1: n8n Mastery & Core Integration
- **n8n Gateway**: Centralized workflow automation with Overseer safety checks
- **Sub-Agent SDK**: Safe n8n interaction layer for all agents
- **Risk Assessment**: Automatic operation categorization and approval workflows
- **Execution Tracking**: Complete audit trails for all workflow operations

### Phase 3.2: Advanced Capabilities & UI Enhancement  
- **Personality System**: 5 distinct agent personalities (Rig, Craft, Scout, Echo, Pulse)
- **HUD Layer**: Animated notification bubbles with agent-specific styling
- **Atlas Chat Panel**: Natural language interface for direct agent communication
- **Command Palette**: Quick action interface (Ctrl/Cmd+K) 
- **Task Drawer**: Real-time operation progress monitoring
- **Desktop Agent**: Multi-modal device control (Bluetooth, HDMI-CEC, IR, gestures)
- **Research Engine**: Vector storage with MinIO + Qdrant for semantic search
- **Great Sage**: Strategic reflection system with weekly insights and planning

## 🏗️ System Architecture

```
Rika Ecosystem (Phase 3.1 + 3.2)
├── Core Services
│   ├── n8n Gateway (Port 5324) - Workflow automation hub
│   ├── Desktop Agent (Port 5325) - Device control & gestures  
│   ├── Research Engine (Port 5326) - Vector search & analysis
│   └── Great Sage (Port 5327) - Strategic reflection
├── Storage Layer
│   ├── PostgreSQL - Core data & execution logs
│   ├── MinIO - Research artifacts & documents
│   └── Qdrant - Vector embeddings for semantic search
├── Agent Personalities
│   ├── Rig 🔧 - Device Controller (methodical, reliable)
│   ├── Craft ⚡ - Code Architect (precise, innovative) 
│   ├── Scout 🔍 - Research Specialist (curious, thorough)
│   ├── Echo 📡 - Communication Hub (responsive, clear)
│   └── Pulse 💓 - System Monitor (vigilant, analytical)
├── UI Components (Phase 3.2)
│   ├── HUD Bubble System - Animated agent notifications
│   ├── Atlas Chat Panel - Direct agent communication
│   ├── Command Palette - Quick actions (Ctrl/Cmd+K)
│   └── Task Drawer - Progress monitoring
└── Safety Layer
    ├── Overseer - Policy enforcement & approvals
    ├── Safe Domains - Restricted operation scopes
    └── Risk Assessment - Operation categorization
```

## 🛠️ Quick Setup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm  
- **PostgreSQL 14+** running on port 5433
- **Docker Desktop** (recommended for storage services)

### One-Command Setup
```powershell
# Windows PowerShell (recommended)
cd rika-core/phase3.2/scripts
.\setup-rika-complete.ps1 -DockerMode

# Or without Docker (manual storage setup)
.\setup-rika-complete.ps1
```

### Manual Step-by-Step Setup
```powershell
# 1. Setup n8n Gateway (Phase 3.1)
.\n8n-setup.ps1

# 2. Setup Desktop Agent (Phase 3.2) 
.\setup-desktop-agent.ps1

# 3. Setup Research Engine (Phase 3.2)
.\setup-research-engine.ps1 -DockerMode

# 4. Great Sage is automatically configured
# All dependencies installed during complete setup
```

## 🚀 Starting the System

### Start All Services
```powershell
# Start complete Rika ecosystem
.\start-rika-complete.ps1

# Or start individual components
.\start-rika-complete.ps1 -SkipResearch -SkipSage
```

### Start Frontend
```bash
# In a separate terminal
cd phase2.5/ui
npm install
npm run dev
```

### Verify Installation
```powershell
# Test all services
.\test-rika-complete.ps1
```

## 🎯 Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **n8n Gateway** | http://localhost:5324 | Workflow automation with safety |
| **Desktop Agent** | http://localhost:5325 | Device control & gestures |
| **Research Engine** | http://localhost:5326 | Vector search & web research |
| **Great Sage** | http://localhost:5327 | Strategic reflection & planning |
| **Frontend UI** | http://localhost:5173 | Main Rika interface |
| **n8n Editor** | http://localhost:5678 | Workflow visual editor |
| **MinIO Console** | http://localhost:9001 | Object storage management |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector database interface |

## 🤖 Agent Personalities

Each agent has distinct capabilities and communication styles:

### Rig 🔧 (Device Controller)
- **Role**: Controls smart devices, automation routines, IoT ecosystems
- **Personality**: Methodical and reliable, safety-conscious
- **Capabilities**: Bluetooth, HDMI-CEC, IR control, gesture recognition
- **Communication**: Clear step-by-step confirmations

### Craft ⚡ (Code Architect)  
- **Role**: Handles code modification, deployment, testing workflows
- **Personality**: Precise and analytical, innovation-focused
- **Capabilities**: Code generation, CI/CD, Git operations, testing
- **Communication**: Technical precision with creative insights

### Scout 🔍 (Research Specialist)
- **Role**: Conducts research, gathers intelligence, analyzes patterns
- **Personality**: Curious and thorough, pattern-recognition driven  
- **Capabilities**: Web research, data analysis, competitive intelligence
- **Communication**: Informative with actionable insights

### Echo 📡 (Communication Hub)
- **Role**: Manages notifications, messaging, inter-agent coordination
- **Personality**: Responsive and clear, priority-aware
- **Capabilities**: Notification routing, alert prioritization, team coordination  
- **Communication**: Concise and urgent when needed

### Pulse 💓 (System Monitor)
- **Role**: Monitors system health, performance metrics, operational status
- **Personality**: Vigilant and analytical, proactive
- **Capabilities**: System monitoring, anomaly detection, predictive maintenance
- **Communication**: Data-driven reports with clear metrics

## 🎨 UI Components (Phase 3.2)

### HUD Bubble System
- **Animated Notifications**: Agent-specific visual styling and animations
- **Priority Levels**: Color-coded urgency (low/normal/high/urgent)
- **Interactive Actions**: Click-to-dismiss or action buttons
- **Smart Positioning**: Automatic layout with edge detection

### Atlas Chat Panel
- **Natural Language**: Direct communication with any agent
- **Slash Commands**: Quick actions (`/help`, `/status`, `/run <workflow>`)
- **Agent Routing**: Intelligent message routing based on content
- **Command History**: Persistent conversation history

### Command Palette (Ctrl/Cmd+K)
- **Quick Actions**: Instant access to common operations
- **Fuzzy Search**: Intelligent command matching
- **Agent Context**: Commands organized by responsible agent
- **Keyboard Shortcuts**: Full keyboard navigation

### Task Drawer
- **Real-time Progress**: Live updates for long-running operations
- **Agent Attribution**: See which agent is handling each task
- **Priority Management**: Visual priority indicators
- **Completion Tracking**: Success/failure status with error details

## 🔧 Device Control Capabilities

### Bluetooth Management
```python
# Auto-discovery and connection
bluetooth_devices = await desktop_agent.scan_bluetooth()
await desktop_agent.connect_device("AA:BB:CC:DD:EE:FF")
```

### HDMI-CEC Control  
```python
# TV and media device control
await desktop_agent.control_tv("power_on")
await desktop_agent.set_active_source(1)
```

### Gesture Recognition
- **Grab**: Device selection/power toggle
- **Point**: Navigation/selection
- **Open Palm**: Stop/reset commands
- **Peace Sign**: Custom actions

## 🔍 Research Capabilities

### Quick vs Deep Research
```python
# Quick research (5 sources, ~30 seconds)
result = await research_engine.research_quick("AI automation trends 2025")

# Deep research (15 sources, ~2 minutes)  
result = await research_engine.research_deep("enterprise AI adoption patterns")
```

### Vector Storage & Semantic Search
- **Automatic Embedding**: Content vectorized with sentence-transformers
- **Semantic Search**: Find related content across all research
- **Deduplication**: Hash-based content deduplication
- **Persistent Storage**: Research artifacts preserved in MinIO

## 🧠 Great Sage Strategic Reflection

### Weekly Cycle
- **System Analysis**: Health metrics and performance review
- **Documentation Review**: Coverage analysis and quality assessment  
- **Strategic Planning**: Long-term objectives and initiative planning
- **Tactical Review**: Recent activities and lessons learned

### Safety Controls
- **Safe Domains**: Restricted to documentation, planning, analysis, research
- **Overseer Approval**: Required for file creation and strategic planning
- **Output Isolation**: All outputs go to designated folders only

### Generated Artifacts
- **DIGEST.md**: Weekly summary of activities and insights
- **PLAN.md**: Strategic planning for upcoming week
- **Reflection Reports**: Detailed analysis stored in database

## 🛡️ Safety & Security

### Multi-Layer Safety
1. **Overseer Integration**: All risky operations require approval
2. **Safe Domain Restrictions**: Agents operate within defined boundaries  
3. **Risk Categorization**: Operations classified by potential impact
4. **Audit Trails**: Complete logging of all system activities

### Operation Risk Levels
- **Low**: Data reading, status checks, notifications
- **Medium**: External API calls, webhook operations
- **High**: File modifications, device control  
- **Critical**: Shell execution, system modifications

## 📊 Monitoring & Observability

### System Health Endpoints
```bash
# Check all service health
curl http://localhost:5324/health  # n8n Gateway
curl http://localhost:5325/health  # Desktop Agent  
curl http://localhost:5326/health  # Research Engine
curl http://localhost:5327/health  # Great Sage
```

### Execution Tracking
- **Workflow Executions**: Complete n8n execution logs
- **Agent Activities**: Per-agent operation history
- **Research Sessions**: Query history and result caching
- **Strategic Reflections**: Sage task completion records

## 🗂️ Directory Structure

```
rika-core/
├── phase2.5/                    # Existing UI and core services
│   ├── ui/                      # React frontend  
│   └── core/                    # Core Rika services
├── phase3.1/                    # n8n Integration (NEW)
│   ├── core/
│   │   └── n8n_gateway.py      # n8n Gateway with safety
│   ├── subagents/
│   │   └── sdk/
│   │       └── n8n_client.py   # Sub-agent SDK
│   └── scripts/
│       ├── n8n-setup.ps1       # n8n installation
│       ├── n8n-run.ps1         # Workflow execution
│       └── n8n-status.ps1      # Status monitoring
└── phase3.2/                   # Advanced Features (NEW)
    ├── agents/
    │   ├── personality_scaffold.json  # Agent personalities
    │   └── desktop/
    │       └── desktop_agent.py       # Device control
    ├── core/
    │   ├── research_engine.py          # Vector research
    │   └── great_sage.py               # Strategic reflection  
    ├── ui/
    │   └── components/
    │       ├── HUD/                    # Bubble system
    │       ├── ChatPanel.tsx           # Atlas chat
    │       ├── CommandPalette.tsx      # Quick actions
    │       └── TaskDrawer.tsx          # Progress tracking
    ├── scripts/
    │   ├── setup-rika-complete.ps1    # Complete setup
    │   ├── start-rika-complete.ps1    # Start all services
    │   └── test-rika-complete.ps1     # System testing
    ├── config/                         # Service configurations
    ├── logs/                           # System logs
    └── output/                         # Great Sage artifacts
```

## 🔄 Workflow Integration Examples

### Device Control via n8n
```javascript
// n8n workflow node - Control TV
const result = await $http.post('http://localhost:5325/device/control', {
  device_type: 'hdmi_cec',
  device_id: '0',  // TV address
  action: 'power_on'
});
```

### Research + Notification Pipeline
```javascript  
// Research workflow
const research = await $http.post('http://localhost:5326/research', {
  query: 'latest AI developments',
  mode: 'quick'
});

// Notify via Echo agent
await $http.post('http://localhost:5324/n8n/run', {
  workflow: 'notification-sender',
  input: {
    message: `Research completed: ${research.summary}`,
    urgency: 'normal'
  }
});
```

## 🎯 Usage Scenarios

### 1. Morning Briefing Automation
```powershell
# Automated morning routine via n8n
./n8n-run.ps1 -Workflow "morning-briefing" -Wait
```
- System health check via Pulse
- Research digest via Scout  
- Device status via Rig
- Priority notifications via Echo

### 2. Development Workflow
```powershell
# Code deployment pipeline
./n8n-run.ps1 -Workflow "code-deployer" -InputJson '{"project":"rika","branch":"main"}'
```
- Code analysis via Craft
- Test execution and reporting
- Deployment with monitoring
- Success notification

### 3. Research & Analysis
- **Quick Research**: "What are the latest trends in AI automation?"
- **Deep Research**: "Comprehensive analysis of enterprise AI adoption"
- **Semantic Search**: Find related content across all previous research
- **Weekly Insights**: Strategic patterns from accumulated knowledge

### 4. Smart Environment Control
- **Voice Commands**: "Turn on the TV and set it to HDMI 1"
- **Gesture Control**: Grab gesture to select device, point to control
- **Automation**: Time-based device schedules via n8n workflows
- **Status Monitoring**: Real-time device health and connectivity

## 🚀 Getting Started - First Steps

### 1. Install and Start
```powershell
# Complete setup in one command
cd rika-core/phase3.2/scripts  
.\setup-rika-complete.ps1 -DockerMode
.\start-rika-complete.ps1
```

### 2. Open Frontend
```bash
cd rika-core/phase2.5/ui
npm run dev
# Visit http://localhost:5173
```

### 3. Try Key Features
- **Press Ctrl/Cmd+K**: Open Command Palette
- **Try Chat**: Click Atlas chat icon, type "/help"
- **Watch HUD**: Agents will show notification bubbles
- **Check Tasks**: Open Task Drawer to see progress
- **Test Research**: Use Command Palette → "Quick Research"

### 4. Explore Workflows
- **Visit**: http://localhost:5678 (n8n editor)
- **Import**: Sample workflows from `phase3.1/workflows/`
- **Create**: New automations with safety controls
- **Monitor**: Execution logs at http://localhost:5324

## 🛠️ Troubleshooting

### Common Issues

#### Services Not Starting
```powershell
# Check dependencies
python --version  # Should be 3.8+
node --version    # Should be 18+
docker --version  # For storage services

# Check ports  
netstat -an | findstr ":5324"  # Should show n8n Gateway
netstat -an | findstr ":5433"  # Should show PostgreSQL
```

#### Storage Services Failed
```powershell  
# Restart Docker services
docker-compose -f ..\docker-compose-storage.yml down
docker-compose -f ..\docker-compose-storage.yml up -d

# Check storage health
curl http://localhost:9000/minio/health/live    # MinIO
curl http://localhost:6333/health               # Qdrant
```

#### Agent Communication Issues
```powershell
# Test individual services
.\test-rika-complete.ps1

# Check logs
Get-Content ..\logs\n8n_gateway.log -Tail 50
Get-Content ..\logs\desktop-agent.log -Tail 50
```

## 📈 Performance & Scaling

### Resource Requirements
- **Development**: 8GB RAM, 4 CPU cores, 10GB disk
- **Production**: 16GB RAM, 8 CPU cores, 50GB disk
- **Network**: Broadband for research operations

### Scaling Considerations
- **Database**: PostgreSQL with connection pooling
- **Storage**: MinIO supports distributed deployment  
- **Vectors**: Qdrant clustering for large datasets
- **Compute**: Individual service scaling via Docker/K8s

## 🔮 What's Next

### Planned Enhancements
- **Phase 4**: Multi-user support with role-based access
- **Mobile App**: React Native companion for remote control
- **Voice Interface**: Speech-to-text integration for hands-free operation
- **Advanced AI**: Large language model integration for enhanced reasoning
- **Enterprise Features**: SSO, advanced security, compliance reporting

### Contributing
This is a complete implementation of Phase 3.1 + 3.2. All components are production-ready with comprehensive error handling, logging, and safety controls.

---

## 🎉 Congratulations!

You now have a complete AI ecosystem with:
- ✅ **5 Agent Personalities** with distinct capabilities
- ✅ **Advanced UI Layer** with bubbles, chat, and command palette  
- ✅ **Device Control** via Bluetooth, HDMI-CEC, IR, and gestures
- ✅ **Semantic Research** with vector storage and web scraping
- ✅ **Strategic Reflection** with weekly insights and planning
- ✅ **Workflow Automation** with comprehensive safety controls
- ✅ **Complete Observability** with health checks and audit trails

**Rika Phase 3.1 + 3.2 is ready for production use! 🚀**