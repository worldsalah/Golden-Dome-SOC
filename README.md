# Golden Dome SOC v1.0.0

A commercial-grade, multi-tenant Security Operations Center (SOC) platform for threat detection, incident response, AI-assisted analysis, and security orchestration.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-69%20passing-brightgreen)

---

## Features

- **SIEM Integration** — Wazuh, OpenSearch, FortiGate, AWS, Azure, ServiceNow, Jira, Microsoft Defender connectors.
- **AI SOC Analyst** — Chat, alert analysis, incident investigation, threat hunting, playbook generation, daily reports.
- **SOAR** — Visual workflow builder with conditions, approval gates, retries, and built-in response playbooks.
- **Threat Intelligence** — IOC database, campaigns, actors, malware, vulnerability intelligence, attack graph.
- **Asset & Risk** — Asset discovery, vulnerability management, risk scoring, security posture, MITRE ATT&CK mapping.
- **Multi-Tenant** — Organization isolation, RBAC, MFA, API keys, audit logs.
- **Commercial Deployment** — Docker production stack, HTTPS reverse proxy, `install.sh`, auto-start, backups.

---

## Technology Stack

- **Backend** — Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, Redis, Alembic, Pydantic.
- **Frontend** — React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Query, Framer Motion, Recharts, React Flow.
- **3D/Maps** — `@react-three/fiber`, Three.js, Leaflet.
- **AI/LLM** — Ollama (local), OpenAI-compatible API support.
- **Infrastructure** — Docker, Docker Compose, Nginx, Wazuh, OpenSearch.

---

## Quick Start (Linux)

On a fresh Ubuntu/Debian server:

```bash
sudo apt-get update && sudo apt-get install -y curl git

curl -fsSL https://raw.githubusercontent.com/worldsalah/Golden-Dome-SOC/main/install.sh | sudo bash
```

Then open `https://<SERVER_IP>` and complete the setup wizard.

---

## Windows Server

Use WSL2:

```powershell
wsl --install -d Ubuntu-24.04
```

After reboot, run in PowerShell:

```powershell
wsl -d Ubuntu-24.04 -u root -e bash -c "apt-get update && apt-get install -y curl git && curl -fsSL https://raw.githubusercontent.com/worldsalah/Golden-Dome-SOC/main/install.sh | bash"
```

---

## Repository Structure

```
Golden-Dome-SOC/
├── backend/          FastAPI application
├── frontend/         React + TypeScript SPA
├── docker/           Backend Dockerfile
├── nginx/            Dev + production Nginx configs
├── scripts/          Backup, restore, verify
├── docs/             Architecture and guides
├── docker-compose.yml            Development stack
├── docker-compose.production.yml Production appliance stack
├── install.sh        One-command Linux installer
├── production.env    Production environment template
├── CHANGELOG.md
├── LICENSE
└── SECURITY.md
```

---

## Testing

### Backend

```bash
docker compose exec -T backend pytest -q
```

Result: **69 passed**.

### Frontend

```bash
cd frontend && npm run build
```

Result: build succeeds.

---

## Documentation

- `CHANGELOG.md` — release history
- `SECURITY.md` — security policy and hardening
- `FINAL_RELEASE_REPORT.md` — v1.0.0 release summary
- `docs/` — architecture, deployment, user guides

---

## License

This project is released under the MIT License. See `LICENSE`.
