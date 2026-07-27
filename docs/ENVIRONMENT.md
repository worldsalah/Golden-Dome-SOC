# Environment Variable Reference

Copy `.env.example` to `.env`; `.env.production` is a restrictive production starting point and `.env.development` is for local development only.

| Variable | Required | Purpose |
|---|---:|---|
| `HTTP_PORT` | No | Public gateway port; defaults to `8080`. |
| `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL` | No | Runtime mode and logging verbosity. Keep `DEBUG=false` in production. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Yes | PostgreSQL initialization and backend connection credentials. |
| `REDIS_PASSWORD` | Yes | Redis authentication credential. |
| `SECRET_KEY` | Yes | 64+ character JWT signing secret; rotate securely. |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Yes | Initial administrator created during first demo seed. |
| `ALLOWED_ORIGINS` | Yes | Comma-separated browser origins permitted for API access. |
| `TRUSTED_HOSTS` | Yes | Comma-separated HTTP hostnames accepted by FastAPI. |
| `SEED_DEMO_DATA` | No | Seeds example SOC data and built-in playbooks. Set false for clean deployments. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` | No | Local AI service location, model, and request limit. |
| `WAZUH_*`, `OPENSEARCH_*` | No | Wazuh and Indexer integration endpoints and credentials. |
| `ABUSEIPDB_API_KEY`, `VIRUSTOTAL_API_KEY`, `ALIENVAULT_OTX_API_KEY` | No | Threat intelligence provider credentials. |
| `SMTP_*` | No | Outbound notification transport; leave blank to use simulated delivery. |
| `SOAR_AUTO_TRIGGER_ENABLED` | No | Enables automatic alert-triggered SOAR playbooks. |

Use a secret manager rather than a plaintext `.env` file in managed cloud environments. Never use any `CHANGE_ME` value in a publicly reachable deployment.
