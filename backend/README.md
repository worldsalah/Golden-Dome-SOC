# Golden Dome SOC — Backend API

FastAPI backend for the Golden Dome SOC Platform.

## Stack

- **Python 3.12+**
- **FastAPI** — REST API framework
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — primary database
- **Alembic** — database migrations
- **Pydantic v2** — validation and settings
- **JWT** — authentication
- **Redis** — caching and Celery broker (prepared for Sprint 4)
- **Docker & Docker Compose**

## Project Structure

```
backend/
├── app/
│   ├── api/            # FastAPI routers
│   ├── config/         # Settings and security helpers
│   ├── database/       # SQLAlchemy models and session
│   ├── schemas/        # Pydantic request/response models
│   ├── security/       # JWT and RBAC
│   ├── services/       # Wazuh client, alert, risk, threat services
│   ├── utils/          # Logging and seed helpers
│   └── main.py         # Application factory
├── tests/              # Pytest suite
├── alembic/            # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Environment Variables

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing key (change in production) |
| `DATABASE_URL` | PostgreSQL async connection string |
| `WAZUH_API_URL` | Wazuh Manager REST API URL |
| `WAZUH_API_USERNAME` / `WAZUH_API_PASSWORD` | Wazuh API credentials |
| `OPENSEARCH_URL` | Wazuh Indexer / OpenSearch URL |
| `ALLOWED_ORIGINS` | CORS origins for the React frontend |

## Development Setup

### Option 1 — Docker Compose (recommended)

```bash
cd backend
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000`.
Swagger UI: `http://localhost:8000/docs`

### Option 2 — Local Python

Requirements: Python 3.12, PostgreSQL 15, Redis 7.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Update .env to point to local PostgreSQL
uvicorn app.main:app --reload
```

## Database Migrations

The application auto-creates tables in development. For production and Alembic-managed migrations:

```bash
cd backend
# Generate a migration from current models
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Default Users

On first startup, a default admin is seeded:

- Username: `admin`
- Password: `admin`

Change this password immediately in production.

## Running Tests

```bash
cd backend
pytest -v
```

## API Endpoints

| Group | Base Path |
|-------|-----------|
| Auth | `/api/auth` |
| Users | `/api/users` |
| Alerts | `/api/alerts` |
| Assets | `/api/assets` |
| Incidents | `/api/incidents` |
| MITRE | `/api/mitre` |
| Reports | `/api/reports` |

## Wazuh Integration

The backend connects to:

1. **Wazuh Manager REST API** for agents, agent details, and vulnerabilities.
2. **Wazuh Indexer (OpenSearch)** for alerts and security events.

Configure both endpoints in `.env`.

## Security Notes

- All passwords are hashed with bcrypt.
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`.
- CORS origins are restricted by `ALLOWED_ORIGINS`.
- Security headers are added by middleware.
- No secrets are hardcoded in source code.
