# SOAR Automation Module

## Overview
The Security Orchestration, Automation and Response (SOAR) module turns the platform from a monitoring tool into an intelligent cyber-defense system. It provides a workflow engine, playbook builder, approval gates, evidence collection, and automation analytics.

## Architecture

```
Security Event
    ↓
Detection Engine
    ↓
Threat Intelligence / AI Analyst
    ↓
SOAR Engine
    ↓
Playbook Execution (nodes + actions)
    ↓
Response Actions / Approval Gate
    ↓
Incident Updates + Evidence + Timeline
    ↓
Dashboard & Reporting
```

## Backend Packages

- `app.services.soar.soar_service` – playbook CRUD, execution orchestration, statistics.
- `app.services.soar.workflow_engine.engine` – node-graph executor with conditions, retries, approval gates, and resume support.
- `app.services.soar.workflow_engine.actions` – registered action handlers (enrich IOC, enrich alert, create/update/close incident, block IP, quarantine/isolate host, disable user, notify, email, webhook, generate report, collect evidence).
- `app.services.soar.notifications.notification_service` – real SMTP email plus simulated Slack/Teams/Discord webhooks.
- `app.services.soar.workflow_engine.actions` also logs every action and piece of evidence.
- `app.api.soar` – FastAPI endpoints for playbooks, executions, approvals, timeline, evidence, logs, statistics, import/export.

## Workflow Engine

A playbook can define either:
1. `nodes` – a directed graph for visual workflows (trigger → condition → actions → approval → end).
2. `actions` – a legacy sequential action list used as fallback.

Node types:
- `trigger` / `start` / `end`
- `condition` – evaluated against workflow variables.
- `approval` – pauses execution and creates a `WorkflowApproval` request.
- `ai_decision` – deterministic AI recommendation based on enrichment results.
- `enrich_ioc`, `enrich_alert`, `query_threat_intel`, `collect_evidence`
- Response actions: `block_ip`, `quarantine_host`, `isolate_endpoint`, `disable_user`
- Notification/reporting: `notify`, `send_email`, `create_ticket`, `webhook`, `generate_report`
- Incident management: `create_incident`, `update_incident`, `close_incident`

Template syntax: strings in node configs can use `{{input.<key>}}` and `{{variables.<key>}}`.

## Approval Workflow

- High-risk actions (e.g. blocking IPs, isolating endpoints) pause the workflow.
- `GET /api/soar/approvals?status=pending` lists pending requests.
- `POST /api/soar/approvals/{id}/decision` approves or denies. Approved requests resume the execution automatically.

## Evidence & Timeline

Every execution produces:
- `WorkflowTimelineEvent` – timestamped node start/end, approvals, errors.
- `WorkflowEvidence` – IOC enrichment, alert enrichment, collected context, generated reports.
- `WorkflowActionLog` – each action invocation, status, duration, input/output.

## Built-in Playbooks

Seeded on startup:
- Brute Force Response
- Malware Detection
- Ransomware Response
- Suspicious PowerShell
- Port Scan Response

## Frontend

`SOARAutomationPage.tsx` provides:
- **Dashboard** – KPI cards, execution-status bar chart, most-executed playbooks, automation health.
- **Playbooks** – list built-in and custom playbooks, run, edit, clone, delete, and a node/action editor.
- **Executions** – recent runs, status, current node, output, timeline, evidence, action logs.
- **Approvals** – approve/deny pending workflow gates.

## Security

- RBAC: playbook create/update/run require `soc_analyst`; delete requires `admin`.
- Every automated action is logged in `WorkflowActionLog`.
- Approval gates enforce human review for high-impact response actions.
