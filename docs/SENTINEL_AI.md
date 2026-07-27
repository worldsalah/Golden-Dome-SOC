# Sentinel AI — SOC Intelligence Engine

## Overview

Sentinel AI is the AI-driven security analyst assistant of the Golden Dome SOC platform. It runs entirely on free, open-source technologies and integrates with the existing FastAPI backend, React frontend, PostgreSQL database, and Ollama-compatible local LLMs.

## Capabilities

- **Alert Explanation & Summarization** — Translate raw Wazuh alerts into executive-friendly summaries and technical explanations.
- **Threat Classification** — Classify alerts by type and severity.
- **Risk Scoring** — Explainable 0–100 risk scores for alerts, assets, and incidents.
- **Threat Intelligence Enrichment** — Enrich IPs, domains, URLs, and hashes using free community feeds.
- **MITRE ATT&CK Mapping** — Map alerts to tactics and techniques using a seeded knowledge base.
- **Investigation & Response Recommendations** — Provide prioritized immediate, short-term, and long-term actions.
- **Incident Report Generation** — Generate structured Markdown and PDF reports.
- **Natural Language Assistant** — Ask Sentinel AI security questions or request investigation guidance.

## Architecture

```
Security Alert
      |
      v
Alert Parser / Context Builder
      |
      +--> Asset Info
      +--> Previous Incidents
      +--> Threat Intelligence
      +--> MITRE Knowledge Base
      +--> Vulnerability Data
      |
      v
AI Analysis Engine (Ollama LLM + fallback)
      |
      v
Risk Scorer
      |
      v
SOC Recommendations
      |
      v
Dashboard / API / Report
```

## Backend Components

| Module | Path | Purpose |
|--------|------|---------|
| Model Manager | `app/services/ai_engine/model_manager.py` | Ollama client with deterministic JSON fallback |
| Context Builder | `app/services/ai_engine/context_builder.py` | Gathers related alert/asset/incident context |
| Prompts | `app/services/ai_engine/prompts.py` | Structured prompt templates |
| Knowledge Base | `app/services/ai_engine/knowledge_base.py` | MITRE techniques, playbooks, seeding |
| Threat Intel | `app/services/ai_engine/threat_intel.py` | Enrichment and IOC caching |
| Risk Scorer | `app/services/ai_engine/risk_scorer.py` | Explainable risk calculation |
| Anomaly Detector | `app/services/ai_engine/anomaly_detector.py` | Isolation Forest ML module |
| Report Generator | `app/services/ai_engine/report_generator.py` | Markdown + PDF reports |
| Analysis Pipeline | `app/services/ai_engine/analysis.py` | Main orchestration service |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/analyze-alert` | Analyze an alert by ID |
| POST | `/api/ai/chat` | Ask Sentinel AI a question |
| GET | `/api/ai/health` | Check AI engine status |
| GET | `/api/threat-intelligence/{indicator}` | Lookup an IOC |
| GET | `/api/threat-intelligence/` | List cached IOCs |
| GET | `/api/risk/asset/{asset_id}` | Asset risk score |
| GET | `/api/risk/alert/{alert_id}` | Alert risk score |
| GET | `/api/risk/incident/{incident_id}` | Incident risk score |
| GET | `/api/risk/top-assets` | Top risky assets |
| POST | `/api/incidents/{incident_id}/generate-report` | Generate incident report |

## Database Schema Additions

- `ai_analysis` — analysis results per alert
- `threat_intelligence` — enriched IOC records
- `ioc_database` — IOC library
- `risk_scores` — calculated risk scores
- `anomaly_records` — ML anomaly output
- `knowledge_base_items` — MITRE/playbook data

## Configuration

Set these environment variables (see `backend/.env.example`):

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Optional threat intelligence keys (free tiers)
ABUSEIPDB_API_KEY=
VIRUSTOTAL_API_KEY=
ALIENVAULT_OTX_API_KEY=
```

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend
cd backend
pytest -q

# Frontend
cd frontend
npm run build
npm run lint
```

## Demonstration Scenarios

1. **Brute Force Detection** — Analyze a failed logon alert; receive MITRE T1110 mapping, risk score, and response steps.
2. **IP Reputation Check** — Enrich `8.8.8.8` through the Threat Intelligence page.
3. **Incident Report** — Generate a Markdown/PDF report for incident #1 from the Reports page.
4. **Risk Center** — Recalculate risk for a critical asset and view top risky assets.
5. **SOC Copilot Chat** — Ask Sentinel AI “How do I investigate a FortiGate deny to RDP alert?”

## Notes

- Sentinel AI only **recommends** actions; it never performs destructive operations.
- When Ollama is unavailable, the engine falls back to deterministic, structured output so the UI remains functional.
