# Contributing

1. Create a focused branch and explain the operational/security impact in the pull request.
2. Keep credentials, tokens, and raw sensitive telemetry out of commits and screenshots.
3. Add or update tests for every behavior change.
4. Run `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, and `npm --prefix frontend run build` before requesting review.
5. Review generated Alembic migrations and update docs for user-visible behavior.
6. Follow least privilege, explicit validation, and approval-gated response automation principles.
