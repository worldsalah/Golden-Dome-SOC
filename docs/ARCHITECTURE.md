# Platform Architecture

```text
Browser -> Gateway Nginx -> Frontend Nginx
                       -> FastAPI -> PostgreSQL
                                   -> Redis
                                   -> Ollama
                                   -> Wazuh Manager / Indexer (optional profile)
```

## Service boundaries

| Service | Responsibility | Published port |
|---|---|---|
| `gateway` | API routing, SPA routing, rate limiting, HTTP security headers | `HTTP_PORT` (8080 default) |
| `frontend` | Immutable React build served by unprivileged Nginx | Internal only |
| `backend` | FastAPI API, automation, integrations, health/readiness | Internal only |
| `migrate` | One-shot Alembic schema migration before backend startup | Internal only |
| `db` | PostgreSQL durable application data | Internal only |
| `redis` | cache and asynchronous coordination | Internal only |
| `ollama` | local LLM inference and model cache | Internal only |
| Wazuh profile | manager, indexer, dashboard for SIEM ingestion | Internal by default |

## Networking and persistence

All services join the `goldendome` bridge network. Database, cache, AI models, application data, and logs use named volumes, retaining data between container rebuilds. Internal service names (`db`, `redis`, `ollama`, `backend`) are DNS names used in deployment configuration.

## Health model

- `/health` reports backend process liveness.
- `/ready` checks PostgreSQL and Redis connectivity and returns 503 if unavailable.
- `/health` on frontend and gateway reports static serving/proxy liveness.
- Compose health checks gate startup where dependencies matter.
- `scripts/verify.sh` provides an operator-facing summary.

## Security model

Containers run without root where images support it; frontend and gateway are read-only with temporary runtime files mounted in memory. The gateway applies headers, compression, and API rate limiting. Secrets are supplied through environment variables, never copied into images. Production deployments must add TLS at the edge and exact CORS/host allowlists.
