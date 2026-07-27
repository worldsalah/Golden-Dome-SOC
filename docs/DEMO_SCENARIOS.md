# RC1 Demonstration Scenarios

## Hotel Wi-Fi attack

1. Ingest a high-severity alert for repeated authentication failures from an untrusted guest-network source.
2. Open the alert and enrich the source IP.
3. Ask AI Analyst for a brute-force investigation plan.
4. Create an incident, assign it, and record evidence in the timeline.
5. Run the Brute Force SOAR playbook; approve containment only after analyst review.
6. Generate an executive report.

## Compromised employee account

1. Create or ingest impossible-travel and suspicious-login alerts for an employee asset.
2. Correlate alerts into an incident and review identity-related evidence.
3. Use AI Analyst to summarize impact and recommend session revocation/password reset.
4. Require approval before disabling an account or external response action.

## Ransomware detection

1. Ingest a critical malware/ransomware alert from an endpoint.
2. Enrich file hashes and asset vulnerabilities.
3. Create a critical incident and run the ransomware response playbook.
4. Demonstrate approval-gated host isolation, evidence capture, and notification.
5. Export the incident report for leadership.

## Malicious PowerShell execution

1. Ingest a PowerShell alert with MITRE ATT&CK technique mapping.
2. Use the AI analysis to identify the suspicious command behavior.
3. Collect endpoint evidence, create an incident timeline, and document hunt queries.
4. Demonstrate a report that contains the MITRE technique and remediation steps.

## External firewall scan

1. Ingest port-scan telemetry from a firewall asset.
2. Enrich source IP intelligence and evaluate asset criticality.
3. Run the Port Scan response playbook to create a ticket and notify analysts.
4. Demonstrate that block actions are simulated or approval-gated until an authorized decision is recorded.
