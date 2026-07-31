# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately to the maintainers at `security@goldendome.local`. Do not open a public issue.

We aim to acknowledge reports within 48 hours and provide an initial assessment within 7 days.

## Security Features

- PBKDF2 password hashing
- JWT access/refresh tokens with revocation
- Multi-factor authentication (TOTP)
- Role-based access control with legacy role migration
- Tenant isolation across all scoped models
- API key management and audit logging
- HTTPS/TLS 1.2+ with secure headers and rate limiting

## Hardening Recommendations

- Replace self-signed certificates with CA-issued or enterprise certificates before production use.
- Rotate `SECRET_KEY`, `POSTGRES_PASSWORD`, and `REDIS_PASSWORD` after first boot.
- Enable MFA for all administrator accounts.
- Restrict network access to management ports (22, 443) using host firewalls.
- Keep the platform, base images, and Wazuh/AI containers updated.
