# Rika Phase 2 - Quick Start Guide

Get Rika Phase 2 running in 5 minutes.

---

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Git

---

## Installation

### 1. Install Dependencies

```bash
cd rika-core
pip install -r rika/requirements_phase2.txt
```

### 2. Setup Database

```bash
# Create database and user
createdb rika_db
createuser rika_user

# Run schema migration
psql -U rika_user -d rika_db -f rika/cognitive_sphere/schema.sql
```

### 3. Configure Environment

Create `.env` file in `rika-core/`:

```bash
# Database
RIKA_DB_PASSWORD=your_password_here

# Encryption (generate random key)
RIKA_ENCRYPTION_KEY=your_32_char_encryption_key_here

# Optional: GitHub token for repo ingestion
GITHUB_TOKEN=your_github_token
```

### 4. Update Config

Edit `config/rika.yaml`:

```yaml
database:
  host: "localhost"
  port: 5432
  database: "rika_db"
  user: "rika_user"
  password: "${RIKA_DB_PASSWORD}"

llm:
  use_mock: true  # Use MockLLM for testing
```

---

## Run Rika

### Option 1: Interactive Mode (Recommended for first run)

```bash
cd rika-core
python rika/run_rika.py interactive
```

This will:
1. Deploy all components
2. Register agents
3. Open interactive chat

**Try these commands**:
```
You: What's on my calendar?
You: How are my YouTube videos performing?
You: What projects am I working on?
```

### Option 2: Test Mode

```bash
python rika/run_rika.py test
```

Runs predefined test queries.

### Option 3: Programmatic Use

```python
from rika.orchestrator_v2 import RikaOrchestrator
from rika.agents.mint import MintAgent

# Initialize
orchestrator = RikaOrchestrator("config/rika.yaml")
# ... setup components ...

# Register Mint
orchestrator.register_agent("mint", MintAgent)

# Process request
response = orchestrator.process_request(
    "How are my videos doing?",
    session_token="your_token"
)

print(response["response"])
```

---

## Verify Installation

### Run Tests

```bash
pytest tests/test_phase2_integration.py -v
```

All tests should pass (some may skip if optional components unavailable).

### Check Dashboard

```bash
python rika/dashboard/phase2_dashboard.py
```

Should show:
- ✓ Database connected
- ✓ LLM loaded (mock)
- ✓ Agents registered
- ✓ System operational

---

## Initial Data Ingestion

### Option 1: Automatic (on startup)

Edit `config/rika.yaml`:

```yaml
cognitive_sphere:
  ingestion:
    auto_ingest_on_startup: true
```

### Option 2: Manual

```python
from rika.cognitive_sphere.ingestor import CognitiveSphereIngestor

ingestor = CognitiveSphereIngestor(db, vector_store, encryption)

# Ingest code repositories
ingestor.ingest_code_repositories()

# Ingest projects
ingestor.ingest_projects("~/projects")

# Build profile
ingestor.build_cognitive_profile()
```

---

## Enable Real Features

### 1. Use Real LLM

Download a GGUF model (e.g., Llama 2, Mistral):

```bash
# Download model (example)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  -O models/rika-llm.gguf
```

Update `config/rika.yaml`:

```yaml
llm:
  model_path: "models/rika-llm.gguf"
  use_mock: false
```

### 2. Enable Gmail/Calendar

1. Get OAuth credentials from Google Cloud Console
2. Save as `credentials/gmail_oauth.json` and `credentials/calendar_oauth.json`
3. Update config:

```yaml
cognitive_sphere:
  sources:
    gmail:
      enabled: true
      credentials: "credentials/gmail_oauth.json"
    calendar:
      enabled: true
      credentials: "credentials/calendar_oauth.json"
```

### 3. Enable YouTube (Mint Agent)

1. Get YouTube Data API credentials
2. Save as `credentials/youtube_oauth.json`
3. Update config:

```yaml
agents:
  mint:
    enabled: true
    credentials: "credentials/youtube_oauth.json"
```

---

## Common Issues

### Database connection fails

```bash
# Check PostgreSQL is running
pg_isready

# Verify credentials
psql -U rika_user -d rika_db -c "SELECT 1"
```

### Import errors

```bash
# Ensure in correct directory
cd rika-core

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests fail

```bash
# Check database schema
psql -U rika_user -d rika_db -c "\dt"

# Should show: cognitive_data, cognitive_profile, conversations, etc.
```

---

## Next Steps

1. ✅ **Verify installation** - Run tests
2. ✅ **Try interactive mode** - Ask Rika questions
3. ✅ **Ingest your data** - Enable email/calendar/projects
4. ✅ **Configure Mint** - Set up YouTube credentials
5. ✅ **Customize boundaries** - Edit `config/boundaries.yaml`
6. ✅ **Add more agents** - Build Rig, Scout, etc.

---

## Example Session

```bash
$ python rika/run_rika.py interactive

[INFO] Starting Rika deployment...
[INFO] Database connected
[INFO] LLM initialized (mock)
[INFO] Agent registered: mint
[INFO] Rika Orchestrator initialized

==============================================================
Rika Interactive Mode
Type 'exit' to quit
==============================================================

You: What's on my calendar tomorrow?

Rika: Based on your calendar, you have focus time from 9-11 AM
and a team meeting at 2 PM. Your schedule is light in the morning,
which is when you typically do your best work.

REASONING: Retrieved calendar patterns from Cognitive Sphere
(Confidence: 0.8)

You: How are my YouTube videos doing?

Rika: I'll analyze your recent video performance.

ACTION: mint analyze_performance {"limit": 10}

Your videos are performing well with an average CTR of 5.2%.
The tutorial series is getting the most engagement. Consider
posting during peak hours (7-9 PM) for maximum reach.

(Confidence: 0.9)

You: exit

Goodbye!
```

---

## Resources

- **Full Documentation**: `PHASE2_COMPLETE.md`
- **Configuration Guide**: `config/rika.yaml` (comments)
- **API Reference**: See `PHASE2_COMPLETE.md` section
- **Tests**: `tests/test_phase2_integration.py`

---

## Support

Having issues? Check:

1. **Logs**: `logs/rika.log`
2. **Dashboard**: `python rika/dashboard/phase2_dashboard.py`
3. **Tests**: `pytest tests/ -v`
4. **Config**: Verify all paths and credentials in `config/rika.yaml`

---

**You're ready!** Start chatting with Rika and explore the Cognitive Sphere.
