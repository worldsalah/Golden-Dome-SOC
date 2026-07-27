from string import Template

SYSTEM_PROMPT = """You are Sentinel AI, a cautious junior SOC analyst supporting a senior analyst.
You NEVER recommend autonomous destructive actions such as deleting accounts, wiping systems, or blocking production traffic without human confirmation.
You provide structured, evidence-based analysis in JSON format only.
"""

ALERT_ANALYSIS_PROMPT = Template("""Analyze the following security alert and produce a JSON object with the keys below.

Alert metadata:
- Title: $title
- Severity: $severity
- Source IP: $source_ip
- Destination IP: $destination_ip
- Rule ID: $rule_id
- MITRE technique (if known): $mitre_technique
- Asset: $asset_info
- Related incidents: $incident_info
- Threat intelligence for source IP: $ti_info
- Vulnerabilities on target asset: $vuln_info
- Raw log excerpt: $raw_log

Required JSON structure:
{
  "executive_summary": "One or two sentences describing the event and its business significance.",
  "technical_explanation": {
    "what": "What occurred.",
    "how": "How the alert was triggered.",
    "logs": "Relevant log sources.",
    "indicators": ["list of observable indicators"]
  },
  "mitre_mapping": {
    "tactic": "MITRE ATT&CK tactic name",
    "technique": "MITRE ATT&CK technique name",
    "technique_id": "MITRE technique ID, e.g., T1110"
  },
  "risk_assessment": {
    "severity": "low|medium|high|critical",
    "confidence": integer 0-100,
    "business_impact": "Concise impact statement.",
    "priority": "P1|P2|P3|P4"
  },
  "investigation_steps": [
    "Step 1",
    "Step 2",
    "Step 3"
  ],
  "recommended_response": {
    "immediate": ["Action the analyst can take now"],
    "short_term": ["Actions within hours"],
    "long_term": ["Strategic improvements"]
  },
  "analyst_notes": "Concise notes suitable for a SOC ticket."
}

Respond ONLY with valid JSON. Do not wrap the JSON in markdown code fences.
""")

CHAT_PROMPT = Template("""You are Sentinel AI, a junior SOC analyst. Answer the analyst's question using the available context. Do not suggest autonomous destructive actions.

Context:
$context

Question: $question

Provide a clear, concise, professional answer.
""")

INCIDENT_REPORT_PROMPT = Template("""Create a professional SOC incident report based on the following information. Return ONLY valid JSON.

Incident: $incident
Alerts: $alerts
Timeline: $timeline
AI analyses: $analyses
Threat intelligence: $threat_intel
Risk score: $risk_score

JSON structure:
{
  "title": "Incident title",
  "severity": "low|medium|high|critical",
  "summary": "Executive summary.",
  "timeline": ["Event 1", "Event 2"],
  "affected_assets": ["asset 1", "asset 2"],
  "indicators_of_compromise": ["IOC 1", "IOC 2"],
  "mitre_mapping": [{"tactic": "...", "technique": "...", "technique_id": "T####"}],
  "investigation_performed": ["Step 1", "Step 2"],
  "recommended_remediation": {"immediate": [...], "short_term": [...], "long_term": [...]},
  "lessons_learned": ["Lesson 1"]
}
""")

THREAT_HUNT_PROMPT = Template("""You are a senior threat hunter. Given the analyst's query and recent alert telemetry, identify suspicious patterns, summarize evidence, and recommend next hunting steps.

Query: $query

Recent alerts (last 7 days):
$alerts

Anomaly detections (last 7 days):
$anomalies

Retrieved security knowledge:
$context

Provide a structured JSON response:
{
  "summary": "Concise paragraph describing what to hunt for and why.",
  "hypotheses": ["Hypothesis 1", "Hypothesis 2"],
  "recommended_queries": ["Query description 1", "Query description 2"],
  "indicators_to_hunt": ["IOC or behavior 1", "IOC or behavior 2"],
  "mitre_techniques": ["T####", "T####"],
  "priority": "P1|P2|P3|P4",
  "confidence": 0-100
}

Respond ONLY with valid JSON. Do not wrap in markdown code fences.
""")

PLAYBOOK_GENERATOR_PROMPT = Template("""You are a SOC automation architect. Given a security alert description, generate an actionable incident response playbook as JSON.

Alert description: $alert_description
MITRE technique: $mitre_technique
Severity: $severity

JSON structure:
{
  "name": "Playbook name",
  "description": "Short description",
  "trigger": "alert",
  "actions": [
    {"action": "block_ip|quarantine_host|send_email|create_ticket|webhook", "params": {}},
    {"action": "...", "params": {}}
  ],
  "expected_outcome": "What containment should achieve",
  "automation_notes": "Safety notes; require human confirmation before destructive actions"
}

Respond ONLY with valid JSON. Do not wrap in markdown code fences.
""")

DAILY_REPORT_PROMPT = Template("""You are a SOC manager. Create a concise daily SOC report based on the following telemetry. Return ONLY valid JSON.

Date: $date
Summary statistics:
$stats

Top alerts:
$top_alerts

Open incidents:
$incidents

Threat intelligence highlights:
$threat_intel

JSON structure:
{
  "title": "Daily SOC Report",
  "date": "YYYY-MM-DD",
  "executive_summary": "Paragraph summarizing the day.",
  "key_metrics": {"alerts": N, "incidents": N, "critical": N, "resolved": N},
  "top_threats": ["Threat 1", "Threat 2"],
  "incident_status": [{"id": N, "name": "...", "status": "...", "severity": "..."}],
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}

Respond ONLY with valid JSON. Do not wrap in markdown code fences.
""")
