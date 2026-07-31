# Golden Dome SOC — Production Status Report

## Infrastructure Overview

| Component | Status | Details |
|-----------|--------|---------|
| Wazuh Manager | ✅ Active | v4.14.1, 2 agents connected |
| Wazuh Indexer (OpenSearch) | ✅ Active | 320,135+ alerts indexed |
| Wazuh Dashboard | ✅ Active | Kibana UI accessible |
| Backend API | ✅ Healthy | v0.3.0, all endpoints operational |
| Frontend | ✅ Healthy | React app served via gateway |
| PostgreSQL DB | ✅ Healthy | 200 alerts, 24 incidents, 6 assets |
| Redis | ✅ Healthy | Cache + session store |
| Ollama LLM | ✅ Healthy | AI analysis engine |

## Agents

| ID | Name | Status | OS | IP |
|----|------|--------|----|----|
| 000 | wazuh.manager | Active | Linux | 127.0.0.1 |
| 002 | RoyalKarthago | Active | Windows Server 2019 | 192.168.1.2 |

## Telemetry Sources (RoyalKarthago)

- **Windows Security Events** — Logon success/failure, account management, service creation, scheduled tasks
- **PowerShell Script Block Logging** — Full script block capture with suspicious command detection
- **Sysmon (SwiftOnSecurity config)** — Process creation, network connections, file creation, registry modifications
- **Windows Defender** — Malware detection, remediation status, real-time protection monitoring
- **FIM (File Integrity Monitoring)** — Critical system file monitoring
- **Vulnerability Detection** — 31 CVEs detected (Notepad++, Windows packages)

## Detection Engineering

### Custom Rules (local_rules.xml)

| Rule ID | Level | Description | MITRE |
|---------|-------|-------------|-------|
| 100100-100105 | 7-14 | FortiGate firewall detection (deny, recon, SSH, DNS, compromised host) | T1046, T1190, T1071.004 |
| 100200-100204 | 8-13 | Sysmon: suspicious process, encoded PowerShell, credential dumping, file creation | T1059, T1059.001, T1003, T1105 |
| 100210-100213 | 10-13 | PowerShell: download/execute, encoded commands, credential access, lateral movement | T1059.001, T1027, T1003, T1021.006 |
| 100220-100222 | 12-14 | Windows Defender: malware detection, remediation failure, protection disabled | T1204, T1562.001 |
| 100230-100235 | 8-10 | Windows auth: brute force, service creation, user creation/deletion, scheduled tasks | T1110, T1543.003, T1136, T1531, T1053.005 |

## GeoIP Enrichment

- **OpenSearch Ingest Pipeline**: `filebeat-7.10.2-wazuh-alerts-pipeline` with GeoIP processor
- **GeoLite2 Databases**: City, Country (MaxMind)
- **Enriched Fields**: `GeoLocation.country_name`, `GeoLocation.city_name`, `GeoLocation.region_name`, `GeoLocation.location`
- **Attack Map**: 103 unique source IPs, 31 with GeoLocation data (Germany, Bulgaria, Russia, etc.)

## Vulnerability Detection

- **31 CVEs** detected for RoyalKarthago
- **Packages scanned**: Notepad++, Windows system packages
- **Severity breakdown**: High (7.8 CVSS), Medium (5.0-6.3 CVSS)
- **Index**: `wazuh-states-vulnerabilities-wazuh.manager`

## Alert Synchronization (Background Worker)

- **Sync interval**: 60 seconds
- **Assets synced**: 6 (FortiGate, Windows Server, Linux servers, Wazuh manager, RoyalKarthago)
- **Alerts synced**: 200 from OpenSearch → PostgreSQL
- **Incidents auto-created**: 24 (from 16 correlated clusters)
- **Dedup**: By `wazuh_alert_id` (unique constraint)

## Incident Correlation

Multi-dimensional clustering using:
- **Source IP + Rule ID** correlation
- **Agent + MITRE technique** correlation
- **Source IP + Destination IP** correlation
- **Rule + Agent** correlation
- **Time-proximity** clustering (5-minute window)
- **Severity escalation** detection (max > avg + 3)

## Threat Intelligence

| Feed | Status | API Key Required |
|------|--------|-------------------|
| AlienVault OTX | ✅ Working (free) | No (optional) |
| AbuseIPDB | ⚠️ Configured (needs key) | Yes |
| VirusTotal | ⚠️ Configured (needs key) | Yes |
| URLHaus | ⚠️ Configured | No |
| MalwareBazaar | ⚠️ Configured | No |
| CISA KEV | ⚠️ Configured | No |
| MITRE ATT&CK | ✅ Working | No |

**OTX enrichment verified**: IP `87.251.64.13` → reputation 100, 10 pulses, malicious_ip

## API Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `/api/wazuh/agents` | ✅ | Agent list and status |
| `/api/wazuh/alerts` | ✅ | OpenSearch alert search |
| `/api/wazuh/attack-map` | ✅ | GeoIP-enriched attack map |
| `/api/wazuh/vulnerabilities` | ✅ | CVE detection results |
| `/api/wazuh/dashboard` | ✅ | Alert aggregation dashboard |
| `/api/wazuh/correlate-incidents` | ✅ | Multi-dimensional incident correlation |
| `/api/alerts` | ✅ | Platform DB alerts (synced) |
| `/api/incidents` | ✅ | Auto-correlated incidents |
| `/api/assets` | ✅ | Asset inventory |
| `/api/mitre/coverage` | ✅ | MITRE ATT&CK coverage |
| `/api/threat-intelligence/enrich` | ✅ | IOC enrichment (OTX) |
| `/api/threat/dashboard` | ✅ | Threat intelligence dashboard |
| `/api/soar/playbooks` | ✅ | SOAR automation |
| `/api/ai/analyze-alert` | ✅ | AI security analysis |

## Key Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/sync_worker.py` | New: Background sync worker (assets, alerts, incidents) |
| `backend/app/main.py` | Added sync worker startup/shutdown in lifespan |
| `backend/app/services/wazuh_service.py` | Enhanced incident correlation (multi-dimensional, time-proximity, escalation) |
| `backend/app/api/wazuh.py` | Expanded hours limits for dashboard, attack-map, correlate-incidents |
| `backend/app/api/incidents.py` | Fixed lazy-loading with selectinload, func.count |
| `backend/app/services/ai_engine/threat_intel.py` | OTX enrichment without API key |
| `backend/app/services/threat_intelligence/connectors/alienvault_otx.py` | OTX connector works without key |
| Wazuh `local_rules.xml` | 20+ custom detection rules (Sysmon, PowerShell, Defender, Windows auth) |

## Notes

- Attack simulation was **skipped** — production hotel environment with live clients
- The platform is receiving **real telemetry** from FortiGate firewall, Windows agent, and Wazuh manager
- All detection rules are active and will trigger on real security events
- Background sync worker runs every 60 seconds to keep platform DB current
