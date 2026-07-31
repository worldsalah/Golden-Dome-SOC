# Changelog

## Golden Dome SOC v1.0.0 — 2026-07-31

### Added
- Enterprise multi-tenant architecture with organization, tenant isolation, role-based access control, MFA, audit logging, and user sessions.
- Professional landing page with animated 3D globe, Framer Motion sections, commercial cybersecurity presentation, and first-boot setup wizard.
- AI Security Analyst Copilot (chat, alert analysis, incident investigation, threat hunt, playbook generator, daily SOC report, audit/history).
- SOAR automation with visual workflow builder, approval gates, retries, evidence collection, and built-in playbooks.
- Asset discovery engine (nmap-based), asset management, vulnerability management, and risk scoring.
- Threat intelligence module (IOC database, campaigns, actors, malware, vulnerability intelligence, attack graph).
- Connector framework for Wazuh, FortiGate, AWS, Azure, ServiceNow, Jira, Microsoft Defender.
- Security posture, hotel/PCI/GDPR module, MITRE ATT&CK mapping, commercial security, and deployment APIs.
- Production deployment stack (`docker-compose.production.yml`), HTTPS reverse proxy, `install.sh`, backup, and upgrade support.

### Security
- Tenant-scoped models and query filters across all 13 data entities.
- PBKDF2 password hashing, JWT access/refresh tokens with revocation, MFA TOTP, and API key management.
- TLS 1.2/1.3, secure headers, HSTS, rate limiting, and self-signed/admin-supplied certificate support.

### Fixed
- React render errors from non-string/object fields in Vulnerability Management and Rule Optimizer.
- Backend first-boot onboarding to allow unauthenticated setup on a fresh installation.
- 502/gateway stale upstream issues after container rebuilds.

### Testing
- 69 backend API/integration tests passing.
- Frontend TypeScript build and lint passing.
- Full Docker stack verified with health checks.

### Known Limitations
- Wazuh and AI/LLM profiles are optional and require additional resources.
- Landing page bundles >500 kB; code-splitting is recommended for v1.1.
- Windows installer uses WSL2 path; native PowerShell installer is on the roadmap.
