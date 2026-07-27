# Golden Dome SOC — RC1 Release Audit

**Release candidate:** `0.3.0-rc1`  
**Audit date:** 2026-07-27  
**Decision:** **Accepted for portfolio, evaluator, and controlled demonstration use.**

## Acceptance evidence

| Gate | Evidence | Status |
|---|---|---|
| Backend regression | `39 passed` via `pytest backend/tests -q` | Pass |
| Frontend quality | ESLint and TypeScript/Vite production build | Pass |
| Container build | Frontend, backend, and migration images built successfully | Pass |
| Deployment | Compose schema validated; migration, seed, and dependencies started | Pass |
| Runtime health | PostgreSQL, Redis, Ollama, backend, frontend, and gateway verified | Pass |
| Authentication | Login and live refresh-token exchange verified | Pass |
| Authorization | Viewer read-only / privileged mutation denial regression test | Pass |
| SOAR | approval, evidence/timeline, lifecycle, and alert-trigger tests | Pass |
| Security review | Findings and remediations in `SECURITY_ASSESSMENT_RC1.md` | Pass with residual risks |

## RC1 quality improvements

- Closed bootstrap account escalation by disabling public registration after the first account.
- Added a refresh-token endpoint and unique JWT IDs.
- Hardened malformed-token and invalid-role failure paths to return controlled authorization responses.
- Fixed PostgreSQL startup seeding and Alembic async URL migration behavior.
- Added repeatable Docker health validation, operational scripts, CI, documentation, governance files, architecture diagrams, and demonstration workflows.

## Release constraints

- This is not a general-availability security product. Production internet exposure requires TLS at the edge, managed secrets, Wazuh certificate setup, external penetration testing, distributed auth rate limiting, and operational monitoring.
- AI answers are advisory and must never be treated as autonomous authorization for destructive operations.
- The frontend production bundle is functional but should be route-split before low-bandwidth user deployment.

## Release checklist

- [x] Core services start successfully.
- [x] Backend/database/cache communication verified.
- [x] Auth and role enforcement covered by tests.
- [x] AI input guard exists and is tested through API behavior.
- [x] SOAR workflows and alert triggering covered.
- [x] Deployment/recovery/security/architecture/user documentation added.
- [x] Release changelog, license, contributor policy, code of conduct, and security policy included.
- [ ] Wazuh profile certificate bootstrap validated in a dedicated resource-sized staging host.
- [ ] Independent DAST/penetration test completed before public production deployment.
