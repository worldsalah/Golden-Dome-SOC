# Detection Engineering Guide

## Overview

Golden Dome SOC includes a full detection engineering pipeline: collect logs, normalize events, apply detection rules, map to MITRE ATT&CK, score risk, generate alerts, and drive AI-assisted response.

## Detection Pipeline

```
Security Event
      |
      v
Log Collection (Wazuh, FortiGate, Windows, Linux)
      |
      v
Log Normalization
      |
      v
Detection Rules
      |
      v
MITRE ATT&CK Mapping
      |
      v
Risk Scoring
      |
      v
Alert Generation
      |
      v
AI Investigation
      |
      v
Incident Creation / SOAR Response
```

## Supported Log Sources

| Source | Collection | Examples |
|--------|-----------|----------|
| Wazuh SIEM | Wazuh Agent + Manager | Sysmon, auth logs, file integrity |
| FortiGate | Syslog / Wazuh integration | Firewall denies, VPN, DNS |
| Windows | Event Logs / Sysmon | Logon events, PowerShell, scheduled tasks |
| Linux | Auditd / auth logs | SSH, sudo, file changes |
| Applications | File / API | Web server logs, database logs |

## Wazuh Integration

Backend module: `app/services/wazuh/`

- `client.py` — Wazuh Manager API authentication and requests.
- `alerts.py` — OpenSearch queries for Wazuh alerts and security events.
- `agents.py` — Wazuh agent listing/details.
- `vulnerabilities.py` — Wazuh vulnerability scanner results.

API endpoints (require authentication):

| Endpoint | Description |
|----------|-------------|
| `GET /api/wazuh/agents` | List agents |
| `GET /api/wazuh/agents/{id}` | Agent details |
| `GET /api/wazuh/vulnerabilities` | Vulnerability findings |
| `GET /api/wazuh/alerts` | Wazuh alerts from indexer |
| `GET /api/wazuh/security-events` | Raw security events |
| `POST /api/alerts/sync` | Pull and normalize Wazuh alerts into platform |

## Detection Rules

Detection rules are stored in the `detection_rules` table with fields:

- `name`, `description`
- `severity` (1–15)
- `category` (Authentication, Network, Malware, etc.)
- `source` (Wazuh, FortiGate, ...)
- `logic` — Python expression evaluated against an event
- `mitre_attack_id`
- `status` — active, disabled, draft, archived

### Rule Logic

Logic is a Python expression evaluated with `event` bound to the incoming log object.

Example:

```python
event.get('rule', {}).get('id') == '200001' and event.get('rule', {}).get('level', 0) >= 10
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/detection-rules` | List rules |
| `POST /api/detection-rules` | Create rule |
| `GET /api/detection-rules/{id}` | Get rule |
| `PATCH /api/detection-rules/{id}` | Update rule |
| `DELETE /api/detection-rules/{id}` | Delete rule |
| `POST /api/detection-rules/{id}/test` | Test rule against sample event |
| `PATCH /api/detection-rules/{id}/toggle` | Enable/disable toggle |
| `GET /api/detection-rules/coverage/summary` | MITRE coverage metrics |

## Wazuh Custom Rules

Production-ready Wazuh rules are provided in `wazuh/custom_rules.xml`. Categories include:

- Authentication: SSH brute force, Windows failed logins, password spraying
- Privilege Escalation: sudo abuse, new admin accounts
- Execution: PowerShell, command shell
- Persistence: scheduled tasks, registry run keys
- Network: port scanning, DNS tunneling, outbound denies
- Lateral Movement: RDP, SMB
- Malware: known hashes, suspicious binaries
- Web Security: SQL injection, directory traversal, web shells

Install by copying the file to the Wazuh manager rules directory (e.g., `/var/ossec/etc/rules/`) and restarting Wazuh.

## Alert Enrichment Pipeline

When an alert is created or enriched, the platform automatically:

1. Looks up MITRE technique details from the knowledge base.
2. Queries threat intelligence for source/destination IPs.
3. Runs Sentinel AI analysis.
4. Optionally creates a critical incident (severity >= 10).

Endpoint: `POST /api/alerts/{id}/enrich?create_incident=true`

## MITRE ATT&CK Coverage

The `mitre_techniques` table tracks detection status:

- `planned` — Not yet implemented
- `partial` — Some detection capability
- `detected` — Active detection rule mapped
- `not_applicable` — Not relevant

Coverage summary is available via `/api/detection-rules/coverage/summary` and visualized in the Detection Center UI.

## Detection Rule Lifecycle

```
Create Rule
     |
Test Rule
     |
Deploy Rule (set status = active)
     |
Monitor Performance
     |
Tune Rule
     |
Archive Rule
```

Use the Detection Center frontend page to manage this lifecycle.

## Testing Rules

Use the rule test dialog in Detection Center or the API:

```bash
curl -X POST "http://localhost:8000/api/detection-rules/1/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event": {"rule": {"id": "200001", "level": 10}}}'
```

Expected response:

```json
{
  "matched": true,
  "reason": "Rule matched",
  "extracted_fields": {"result": true}
}
```

## Standards

- Sigma rule concepts for detection logic.
- MITRE ATT&CK framework for threat mapping.
- Detection-as-Code principles.
- SOC best practices for tuning and false-positive management.

## Troubleshooting

- **Wazuh API unreachable**: Verify `WAZUH_API_URL`, credentials, and certificate settings in `.env`.
- **OpenSearch query fails**: Check `OPENSEARCH_URL` and that Wazuh indexer is running.
- **No detection rules in UI**: Ensure `seed_database` runs on startup or insert rules manually.
- **Rule test fails with syntax error**: Validate Python expression syntax in `logic`.
