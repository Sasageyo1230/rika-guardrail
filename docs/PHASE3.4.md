# Rika Phase 3.4 - Complete Documentation

## Overview

Rika Phase 3.4 is a comprehensive AI-powered development assistant featuring:

- **Multi-Agent Chat System**: Rika (General), Rig (Technical), Craft (Creative), Scout (Research)
- **Streaming Responses**: Real-time SSE (Server-Sent Events) streaming
- **Multi-LLM Support**: Anthropic Claude, OpenAI GPT, Local/Ollama models
- **Memory System**: JSON-based conversation memory with PostgreSQL fallback
- **Tool Integration**: n8n workflow execution
- **AI Designer**: Design Mode for AI-driven UI modifications
- **Atlas UI**: Modern React/TypeScript interface with Tailwind CSS
- **PowerShell 5.1 Compatible**: Zero venv activation issues on Windows

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Windows PowerShell 5.1+

### One-Command Setup

```powershell
.\phase3.4\scripts\COMPLETE-SETUP.ps1
```

This will:
1. Run system diagnostics
2. Install all dependencies
3. Configure the system
4. Run comprehensive tests
5. Optionally start the development environment

### Manual Setup

```powershell
# 1. Setup
.\phase3.4\scripts\setup.ps1

# 2. Configure API keys in .env file
# Edit .env and add your Anthropic/OpenAI keys

# 3. Start development servers
.\phase3.4\scripts\start-dev.ps1

# 4. Open http://localhost:5173
```

## Architecture

### Core API (Port 5317)

- **FastAPI** application with async support
- **SSE Streaming** for real-time responses
- **Multi-LLM routing** based on agent selection
- **Memory management** with session persistence
- **Tool execution** framework for n8n integration
- **UI patch system** for Design Mode

### Atlas UI (Port 5173)

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Vite** for build tooling
- **Real-time chat** with streaming support
- **Design Mode** for AI-driven UI changes
- **Multi-agent selection** interface

### Directory Structure

```
rika-core/
├── core/                    # Core API
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration management
│   ├── llm_client.py       # Multi-LLM client
│   ├── memory.py           # Memory system
│   ├── chat.py             # Chat endpoints
│   ├── ui_patch.py         # Design Mode system
│   └── tools/              # Tool integrations
│       ├── __init__.py     # Tool registry
│       └── n8n_client.py   # n8n integration
├── ui/                     # Atlas UI
│   ├── src/
│   │   ├── App.tsx         # Main application
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Build configuration
├── config/                 # Configuration files
│   └── config.json         # System configuration
├── phase3.4/scripts/       # PowerShell scripts
│   ├── setup.ps1           # Installation script
│   ├── start-dev.ps1       # Development servers
│   ├── start-prod.ps1      # Production servers
│   ├── test.ps1            # Comprehensive tests
│   ├── diagnose.ps1        # System diagnostics
│   └── COMPLETE-SETUP.ps1  # One-command setup
├── .env                    # Environment variables
└── docs/                   # Documentation
    └── PHASE3.4.md         # This file
```

## Configuration

### Environment Variables (.env)

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=5317
API_RELOAD=true

# LLM Providers
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
LOCAL_LLM_URL=http://localhost:11434

# Database (Optional)
DATABASE_URL=sqlite:///./rika.db

# n8n Integration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key_here

# Development
DEBUG=true
LOG_LEVEL=info
```

### System Configuration (config/config.json)

```json
{
  "llm": {
    "default_provider": "anthropic",
    "providers": {
      "anthropic": {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4000
      },
      "openai": {
        "model": "gpt-4",
        "max_tokens": 4000
      },
      "local": {
        "model": "llama2:7b",
        "max_tokens": 4000
      }
    }
  },
  "memory": {
    "provider": "json",
    "max_history": 50
  },
  "tools": {
    "n8n": {
      "enabled": true,
      "timeout": 30
    }
  },
  "ui": {
    "design_mode_enabled": true,
    "auto_backup": true
  }
}
```

## Features

### Multi-Agent Chat

- **Rika (General)**: Default assistant for general queries
- **Rig (Technical)**: Specialized for technical and programming tasks
- **Craft (Creative)**: Focused on creative and design work
- **Scout (Research)**: Optimized for research and information gathering

### Streaming Responses

Real-time streaming using Server-Sent Events (SSE):

```typescript
const stream = await chatService.sendMessage({
  session_id: "session-123",
  message: "Hello Rika",
  agent: "rika",
  stream: true
});

for await (const event of stream) {
  switch (event.type) {
    case 'token':
      // Handle streaming token
      break;
    case 'tools_start':
      // Handle tool execution start
      break;
    case 'complete':
      // Handle completion
      break;
  }
}
```

### Design Mode (AI Designer)

Modify the UI using natural language:

1. Press `Ctrl+D` to open Design Mode
2. Describe the change you want (e.g., "Make the chat bubble bigger")
3. Review the generated patch
4. Apply if safe

### Tool Integration

Execute n8n workflows through chat:

```python
# Example tool execution
result = await n8n_client.execute_workflow(
    workflow_id="workflow-123",
    data={"message": "Process this data"}
)
```

## API Reference

### Chat Endpoints

#### POST /chat/

Start a chat conversation with streaming support.

**Request:**
```json
{
  "session_id": "string",
  "message": "string",
  "agent": "rika|rig|craft|scout",
  "stream": true
}
```

**Response:** SSE stream or JSON response

#### GET /chat/sessions

List active chat sessions.

#### DELETE /chat/sessions/{session_id}

Clear a specific session.

### UI Endpoints

#### POST /ui/patch

Create a UI modification patch.

**Request:**
```json
{
  "request": "string",
  "target_files": ["string"],
  "preview_only": true
}
```

#### POST /ui/patch/{patch_id}/apply

Apply a generated patch.

#### GET /ui/patches

List available patches.

### Health Endpoint

#### GET /health

Check API health status.

## Scripts Reference

### setup.ps1

Installs all dependencies and configures the system.

**Parameters:**
- `-Force`: Recreate virtual environment
- `-Verbose`: Enable verbose output

### start-dev.ps1

Starts development servers with hot reload.

**Parameters:**
- `-SkipUI`: Skip UI server
- `-SkipAPI`: Skip API server
- `-Verbose`: Enable verbose output

### start-prod.ps1

Starts production-optimized servers.

**Parameters:**
- `-SkipUI`: Skip UI server
- `-SkipAPI`: Skip API server
- `-Verbose`: Enable verbose output

### test.ps1

Runs comprehensive test suite.

**Parameters:**
- `-SkipUI`: Skip UI tests
- `-SkipAPI`: Skip API tests
- `-SkipIntegration`: Skip integration tests
- `-Verbose`: Enable verbose output

### diagnose.ps1

Performs system health check and diagnostics.

**Parameters:**
- `-Detailed`: Show detailed information
- `-FixIssues`: Attempt to fix issues automatically
- `-Verbose`: Enable verbose output

## Troubleshooting

### Common Issues

#### Port Already in Use

```powershell
# Free ports 5317 and 5173
.\phase3.4\scripts\diagnose.ps1 -FixIssues
```

#### Virtual Environment Issues

```powershell
# Recreate virtual environment
.\phase3.4\scripts\setup.ps1 -Force
```

#### API Keys Not Working

1. Check `.env` file exists
2. Verify API keys are correctly formatted
3. Test connectivity: `curl http://localhost:5317/health`

#### UI Build Failures

```powershell
# Clean install UI dependencies
cd ui
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Logs and Debugging

- **API Logs**: Check console output from start-dev.ps1
- **UI Logs**: Check browser developer console
- **System Logs**: Use diagnose.ps1 for system status

## Development

### Adding New Agents

1. Update `core/chat.py` with new agent logic
2. Add agent to UI agent selector in `ChatPanel.tsx`
3. Update configuration in `config.json`

### Adding New Tools

1. Create tool in `core/tools/`
2. Register in `core/tools/__init__.py`
3. Update configuration as needed

### Modifying UI

1. Edit React components in `ui/src/components/`
2. Use Design Mode for simple changes
3. Rebuild with `npm run build`

## License

MIT License - See LICENSE file for details.

## Support

For issues and feedback:
- Create an issue in the project repository
- Run diagnostics: `.\phase3.4\scripts\diagnose.ps1`
- Check logs for error messages