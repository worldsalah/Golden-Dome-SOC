# QA Report — RC1

**Status:** Candidate accepted for portfolio/demo release after final automated verification.

## Automated coverage

| Area | Coverage evidence | Status |
|---|---|---|
| Authentication | Password verification, login failures, bootstrap registration, refresh type validation, malformed JWT claims | Pass |
| Authorization | Viewer read access and mutation/admin denial | Pass |
| Alerts / detection | Alert APIs, Wazuh normalization, detection-rule tests | Pass |
| AI | API and engine tests, fallback behavior, injection input validation | Pass |
| SOAR | approval gates, timeline/evidence, clone/delete, alert auto-trigger | Pass |
| Infrastructure | Compose config, image builds, migrations, health verification | Pass |
| Frontend | ESLint and production TypeScript/Vite build | Pass |

## End-to-end verification

The deployed Compose stack passed health checks for PostgreSQL, Redis, Ollama, FastAPI, frontend Nginx, and gateway Nginx. Migration and demo seed ran before backend readiness.

## Manual RC1 UX checklist

- Verify login, sidebar navigation, table pagination, empty states, form validation, charts, and SOAR graph editing at desktop/tablet widths before external demonstration.
- Confirm exact production hostname, TLS certificate, CORS, trusted-host setting, and administrator password before publishing any deployment.
- Use demo scenarios in `docs/DEMO_SCENARIOS.md` for evaluator walkthroughs.

## Known non-blocking items

- Wazuh needs its certificate bootstrap and is intentionally opt-in.
- Full visual regression/browser automation and Lighthouse capture are recommended follow-up gates.
- AI outputs remain advisory; human validation is required for security decisions.
