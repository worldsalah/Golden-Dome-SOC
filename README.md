# 🛡️ Golden Dome SOC Platform

[![RC1](https://img.shields.io/badge/release-RC1-0ea5e9)](CHANGELOG.md)
[![Docker Compose](https://img.shields.io/badge/deployment-Docker%20Compose-2496ed)](docs/DEPLOYMENT.md)
[![License](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

## Overview

Golden Dome is a containerized Security Operations Center (SOC) platform for security monitoring, threat detection, incident response, threat intelligence, AI-assisted analysis, and SOAR automation.

## Quick Start

```bash
cp .env.example .env
./scripts/install.sh
```

Open `http://localhost:8080` and sign in using `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`. The command builds and starts the frontend, FastAPI backend, PostgreSQL, Redis, Ollama, reverse proxy, schema migration, demo seed, and health verification.

- **[Installation](docs/INSTALLATION.md)**
- **[Production deployment and recovery](docs/DEPLOYMENT.md)**
- **[Architecture](docs/ARCHITECTURE.md)**
- **[Environment variables](docs/ENVIRONMENT.md)**
- **[Developer guide](docs/DEVELOPMENT.md)**

## Product Capabilities

- **Security operations**: alerts, assets, incidents, detection rules, MITRE mapping, risk scoring, reports, and timeline evidence.
- **AI-assisted analysis**: local Ollama integration, guarded analyst chat, RAG-backed investigation context, fallback analysis, and structured recommendations.
- **Threat intelligence**: IOC enrichment and vulnerability context from configured providers.
- **SOAR**: visual node workflow builder, approval gates, retry-aware actions, alert triggers, evidence collection, playbook import/export, and notifications.
- **Enterprise operations**: production Compose stack, migrations, health checks, CI, backup/recovery, security assessment, and RC1 quality artifacts.

See the [architecture diagrams](docs/ARCHITECTURE_DIAGRAMS.md), [user manual](docs/USER_MANUAL.md), [demo scenarios](docs/DEMO_SCENARIOS.md), [security assessment](docs/SECURITY_ASSESSMENT_RC1.md), [QA report](docs/QA_REPORT_RC1.md), and [RC1 release audit](docs/RELEASE_AUDIT_RC1.md).

The platform integrates:

- Wazuh SIEM
- FortiGate Firewall Logs
- Windows Security Monitoring
- Threat Detection
- Security Analytics


## Project Objectives

The objective is to build a complete SOC environment capable of:

- Collecting security events
- Detecting suspicious activity
- Monitoring infrastructure
- Investigating incidents
- Supporting security operations workflows


## Current Architecture


FortiGate Firewall
|
| Syslog
|
v

Kali Linux SOC Server

Wazuh Manager
Wazuh Indexer

Wazuh Dashboard

  |
  |
  v

Windows Server 2019
Wazuh Agent



## Technology Stack

| Component | Technology |
|-|-|
| Operating System | Kali Linux |
| SIEM | Wazuh |
| Firewall | FortiGate |
| Endpoint Monitoring | Wazuh Agent |
| Containerization | Docker |
| Documentation | Markdown |


## Sprint Progress

### Sprint 1 — SOC Foundation

Status:

✅ Completed


Completed tasks:

- Kali Linux prepared
- Network connectivity verified
- SOC workspace created
- Docker installed
- Docker Compose configured
- Wazuh deployment repository downloaded


Next Sprint:

- Deploy Wazuh stack
- Install Windows Agent
- Integrate FortiGate Syslog
- Create detection rules


## Author

Salah ANEZ

Cybersecurity Engineering Student
