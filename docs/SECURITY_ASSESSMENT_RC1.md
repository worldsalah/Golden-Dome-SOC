# Security Assessment — RC1

**Assessment date:** 2026-07-27  
**Scope:** FastAPI API, JWT/RBAC, frontend delivery, AI prompt boundary, Docker deployment, and Compose network.

## Executive summary

No known critical release blocker remains in the tested core stack. The assessment corrected public post-bootstrap account creation and added token refresh handling, malformed-claim handling, RBAC regression tests, and container/network controls. This is an engineering assessment, not a substitute for an independent penetration test before internet exposure.

## Findings and remediations

| ID | Severity | Finding | RC1 remediation |
|---|---|---|---|
| SEC-001 | High | Public registration accepted privileged role values after initialization. | Public registration now works only when no user exists. Subsequent accounts must be created by an administrator through `/api/users`. |
| SEC-002 | Medium | Refresh tokens were issued but no exchange endpoint existed. | Added `POST /api/auth/refresh`, validates token type, active user, and rotates issued token IDs. |
| SEC-003 | Medium | Malformed JWT `sub` claims could cause a server exception. | JWT subject parsing now returns controlled `401` responses. |
| SEC-004 | Medium | Unknown persisted role values could trigger unhandled enum conversion. | RBAC dependencies now fail closed with `403`. |
| SEC-005 | Medium | Initial PostgreSQL seed failed because UTC-aware defaults were inserted into naive schema columns. | UTC helper now emits naive UTC compatible with existing schema; full Compose startup verified. |
| SEC-006 | Low | Prompt injection risk from user-supplied AI questions. | AI question, hunt, and generated playbook inputs use bounded injection-marker validation; system prompt prohibits autonomous destructive action. |
| SEC-007 | Low | Internal service exposure could widen attack surface. | Only gateway publishes an application port; database, Redis, backend, frontend, and Ollama remain Compose-network internal. |

## Verified controls

- Bcrypt password hashing with an explicit 72-byte boundary.
- JWT signature, expiry, access/refresh type separation, unique token IDs, active-user lookup.
- Role-based authorization on privileged API routes.
- Pydantic request validation and bounded query pagination on audited resource routes.
- Read-only unprivileged Nginx containers, app non-root user, Docker logging rotation, Compose health checks.
- Security headers, trusted hosts, CORS configuration, and gateway API rate limiting.

## Residual risks and recommendations

- Add a distributed Redis-backed login limiter and refresh-token revocation list before multi-node internet exposure.
- Terminate TLS at a managed edge/load balancer and store secrets in a secret manager rather than `.env`.
- Add SAST/DAST and dependency remediation for all reported third-party package advisories in CI.
- Conduct an authenticated external penetration test and threat model integrations before GA.
- Configure Wazuh certificates and network policy separately; the official Wazuh profile is intentionally opt-in.
