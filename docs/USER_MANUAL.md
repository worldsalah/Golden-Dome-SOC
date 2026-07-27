# Golden Dome SOC User Manual

## 1. Sign in

Open the platform URL supplied by your administrator. Use the seeded administrator credentials only for first access; create named analyst accounts from **Profile / User Management** and rotate the bootstrap password.

## 2. Dashboard

The dashboard summarizes alert volume, open incidents, asset risk, and detection health. Use it as the operational landing page; drill into an alert or incident rather than taking containment action directly from aggregate metrics.

## 3. Alert investigation

Open **Alerts**, filter by severity, status, source, or date, then open an alert. Review source/destination, MITRE mapping, related asset context, threat intelligence, and investigation history. Assign or acknowledge alerts according to your team workflow.

## 4. AI Analyst

Use **AI Analyst** to request an evidence-based explanation, suggested investigation steps, or a threat hunt. Input is bounded and checked for prompt-injection markers. Treat the result as analyst assistance, verify cited telemetry, and obtain human approval before destructive action.

## 5. Incidents

Create or update incidents from correlated alerts. Use the timeline to record assignments, investigation observations, containment decisions, and closure reasoning. The timeline is the primary audit trail.

## 6. Assets and vulnerabilities

Use **Assets** for asset ownership, criticality, exposure, associated alerts, and vulnerability context. Asset changes require analyst privileges. Use **Vulnerabilities** to prioritize remediation from exploitability and business criticality.

## 7. Threat Intelligence

Use **Threat Intelligence** to enrich IPs, domains, hashes, and campaign indicators. Provider results may be unavailable or rate-limited; a failed provider does not itself imply an IOC is benign.

## 8. SOAR

Use **SOAR Automation** to select a playbook, inspect its graph, run approved simulations, and review execution logs, evidence, approvals, and timeline events. High-risk responders must use an approval node. Alert-triggered playbooks may run automatically only when enabled by administrators.

## 9. Reports

Generate operational or executive reports after confirming incident data. Review generated AI content for accuracy before distribution.

## 10. Roles

- **Viewer**: read operational data.
- **SOC analyst**: investigate and mutate operational records.
- **Administrator**: manage users, system-level resources, and privileged controls.

If a control is unavailable, contact an administrator rather than bypassing workflow safeguards.
