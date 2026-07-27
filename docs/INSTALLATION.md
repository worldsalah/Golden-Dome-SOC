# Installation Guide

## Prerequisites

- Docker Engine 25+ or Docker Desktop 4+
- Docker Compose v2
- 8 GB RAM for the core stack; 16 GB+ when running Ollama and Wazuh
- 20 GB free disk space for images, database, and model data

## Quick start

```bash
cp .env.example .env
./scripts/install.sh
```

The installer verifies Docker, creates local folders, generates local secrets if `.env` is new, builds images, starts the platform, and runs health checks.

Open `http://localhost:8080`. Log in using `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`.

## Manual start

```bash
cp .env.example .env
# Edit all CHANGE_ME and password values before production use.
docker compose up -d
./scripts/verify.sh
```

## Development

```bash
cp .env.development .env
docker compose -f docker-compose.dev.yml up
```

Frontend hot reload is served on `http://localhost:5173`; backend OpenAPI is on `http://localhost:8000/docs`.

## Troubleshooting

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 db
./scripts/verify.sh
```

If the database migration fails, inspect the `migrate` service logs. Do not remove `postgres_data` in a production environment; use `scripts/backup.sh` before any recovery action.

## Wazuh

The core platform starts by default. Wazuh is an opt-in profile because the official stack requires certificates and substantially more host resources. Use the maintained Wazuh single-node bundle under `wazuh/wazuh-docker/single-node` for certificate bootstrap, then launch the root profile:

```bash
docker compose --profile wazuh up -d
```

Keep Wazuh manager, indexer, and dashboard ports private or protected by a VPN/reverse proxy in production.
