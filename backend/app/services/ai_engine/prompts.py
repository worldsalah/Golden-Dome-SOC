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

ATTACK_CHAIN_PROMPT = Template("""You are a senior SOC analyst performing attack chain analysis. Given a set of related alerts from an incident, reconstruct the likely attack chain using the MITRE ATT&CK framework. Return ONLY valid JSON.

Incident: $incident
Alerts (chronological): $alerts
Threat intelligence: $threat_intel
Asset context: $assets

JSON structure:
{
  "attack_chain_summary": "Narrative description of the attack progression",
  "kill_chain_phases": [
    {"phase": "Reconnaissance", "description": "...", "evidence": ["alert_id", "alert_id"]},
    {"phase": "Initial Access", "description": "...", "evidence": ["alert_id"]},
    {"phase": "Execution", "description": "...", "evidence": ["alert_id"]},
    {"phase": "Persistence", "description": "...", "evidence": []},
    {"phase": "Privilege Escalation", "description": "...", "evidence": []},
    {"phase": "Defense Evasion", "description": "...", "evidence": []},
    {"phase": "Credential Access", "description": "...", "evidence": []},
    {"phase": "Discovery", "description": "...", "evidence": []},
    {"phase": "Lateral Movement", "description": "...", "evidence": []},
    {"phase": "Collection", "description": "...", "evidence": []},
    {"phase": "Command and Control", "description": "...", "evidence": []},
    {"phase": "Exfiltration", "description": "...", "evidence": []},
    {"phase": "Impact", "description": "...", "evidence": []}
  ],
  "attacker_profile": {
    "sophistication": "low|medium|high|APT-level",
    "likely_threat_actor": "Named group or 'Unknown'",
    "motivation": "Financial|Espionage|Disruption|Unknown",
    "ttps_observed": ["T####", "T####"]
  },
  "evidence_summary": {
    "key_findings": ["Finding 1", "Finding 2"],
    "confidence_level": "low|medium|high",
    "gaps_in_evidence": ["What we don't know yet"]
  },
  "remediation_priority": [
    {"priority": "critical", "action": "...", "reason": "..."},
    {"priority": "high", "action": "...", "reason": "..."}
  ]
}

Only include phases where evidence exists. Respond ONLY with valid JSON.
""")

DETECTION_ENGINEER_PROMPT = Template("""You are an AI Detection Engineer. Analyze the following alert data and detection rule to identify false positives, suggest rule improvements, and identify MITRE coverage gaps. Return ONLY valid JSON.

Alert data:
$alert_data

Detection rule (if available):
$rule_data

Historical alert stats for this rule:
$stats

JSON structure:
{
  "false_positive_analysis": {
    "is_likely_fp": true|false,
    "confidence": 0-100,
    "reasoning": "Explanation of why this is or isn't a false positive",
    "fp_indicators": ["Indicator 1", "Indicator 2"],
    "legitimate_indicators": ["Indicator 1", "Indicator 2"]
  },
  "rule_improvement_suggestions": [
    {
      "suggestion": "Description of the improvement",
      "current_issue": "What's wrong with the current rule",
      "proposed_change": "Specific change to make",
      "expected_impact": "What this will improve"
    }
  ],
  "mitre_coverage": {
    "technique_covered": "T#### or null",
    "related_techniques": ["T####", "T####"],
    "missing_detection_gaps": ["Technique that should be detected but isn't"],
    "recommended_new_rules": [
      {
        "name": "Rule name",
        "technique_id": "T####",
        "description": "What this rule should detect",
        "suggested_logic": "Pseudo-code or description of detection logic"
      }
    ]
  },
  "tuning_recommendations": {
    "severity_adjustment": "increase|decrease|maintain",
    "reasoning": "Why severity should change",
    "filter_suggestions": ["Filter 1", "Filter 2"],
    "whitelist_suggestions": ["Entry 1"]
  },
  "overall_assessment": "Summary of the detection engineering review"
}

Respond ONLY with valid JSON. Do not wrap in markdown code fences.
""")
