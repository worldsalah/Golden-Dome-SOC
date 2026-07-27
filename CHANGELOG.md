# Changelog

## 0.3.0-rc1 — 2026-07-27

### Added

- SOAR visual playbook builder, approval gates, evidence, workflow timeline, import/export, retries, alert triggers, and notification channels.
- Containerized production stack with Nginx, FastAPI, PostgreSQL, Redis, Ollama, Alembic, health checks, install/verify/backup/restore tooling, and GitHub Actions CI.
- RC1 security assessment, architecture diagrams, user manual, and demonstration scenarios.
- JWT refresh endpoint and security/RBAC regression tests.

### Changed

- Public account registration is now bootstrap-only; administrators create later accounts through the user-management API.
- Token creation includes unique JWT IDs; malformed token claims and invalid roles fail closed.
- PostgreSQL schema initialization is handled by Alembic before backend startup.

### Known limitations

- Wazuh is an opt-in, certificate-based profile.
- AI results remain analyst-assistive and must be reviewed before operational action.
