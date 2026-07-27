import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import KnowledgeBaseItem, MITRETechnique

logger = logging.getLogger(__name__)


MITRE_TECHNIQUES: dict[str, dict[str, str]] = {
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "T1133": {"name": "External Remote Services", "tactic": "Initial Access"},
    "T1078": {"name": "Valid Accounts", "tactic": "Defense Evasion, Persistence, Privilege Escalation, Initial Access"},
    "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
    "T1110.001": {"name": "Brute Force: Password Guessing", "tactic": "Credential Access"},
    "T1110.003": {"name": "Brute Force: Password Spraying", "tactic": "Credential Access"},
    "T1548": {"name": "Abuse Elevation Control Mechanism", "tactic": "Privilege Escalation"},
    "T1068": {"name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1059.001": {"name": "PowerShell", "tactic": "Execution"},
    "T1059.003": {"name": "Windows Command Shell", "tactic": "Execution"},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "Persistence"},
    "T1053.005": {"name": "Scheduled Task", "tactic": "Persistence"},
    "T1547": {"name": "Boot or Logon Autostart Execution", "tactic": "Persistence"},
    "T1547.001": {"name": "Registry Run Keys", "tactic": "Persistence"},
    "T1046": {"name": "Network Service Scanning", "tactic": "Discovery"},
    "T1016": {"name": "System Network Configuration Discovery", "tactic": "Discovery"},
    "T1083": {"name": "File and Directory Discovery", "tactic": "Discovery"},
    "T1018": {"name": "Remote System Discovery", "tactic": "Discovery"},
    "T1021": {"name": "Remote Services", "tactic": "Lateral Movement"},
    "T1021.001": {"name": "Remote Desktop Protocol", "tactic": "Lateral Movement"},
    "T1021.002": {"name": "SMB/Windows Admin Shares", "tactic": "Lateral Movement"},
    "T1550": {"name": "Use Alternate Authentication Material", "tactic": "Lateral Movement"},
    "T1204": {"name": "User Execution", "tactic": "Execution"},
    "T1105": {"name": "Ingress Tool Transfer", "tactic": "Command and Control"},
    "T1071.004": {"name": "DNS", "tactic": "Command and Control"},
    "T1505.003": {"name": "Web Shell", "tactic": "Persistence"},
    "T1136": {"name": "Create Account", "tactic": "Persistence"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic": "Impact"},
}

DEFAULT_RESPONSE_PLAYBOOKS: dict[str, dict[str, Any]] = {
    "brute_force": {
        "description": "Response playbook for brute force attacks.",
        "immediate": [
            "Identify the targeted account(s).",
            "Block or contain the source IP if IOC is confirmed.",
            "Check for any successful authentications from the same source.",
        ],
        "short_term": [
            "Reset affected credentials.",
            "Enable or enforce MFA.",
            "Review authentication logging for additional suspicious IPs.",
        ],
        "long_term": [
            "Implement account lockout policies.",
            "Deploy geo-impossible travel detection.",
            "Conduct purple-team exercise for credential-based attacks.",
        ],
    },
    "port_scan": {
        "description": "Response playbook for network scanning activity.",
        "immediate": [
            "Identify the source and targeted hosts.",
            "Determine if the scan originated from an authorized asset.",
            "Capture relevant firewall and IDS logs.",
        ],
        "short_term": [
            "Review exposed services and patch/remove unnecessary ones.",
            "Tighten ingress/egress firewall rules.",
        ],
        "long_term": [
            "Segment critical networks.",
            "Deploy network detection for scanning behavior.",
        ],
    },
    "malware": {
        "description": "Response playbook for suspected malware execution.",
        "immediate": [
            "Isolate the affected host from the network.",
            "Preserve memory and disk artifacts.",
            "Block known malicious hashes at the endpoint and proxy layers.",
        ],
        "short_term": [
            "Run endpoint malware scan.",
            "Reset credentials used on the affected host.",
            "Hunt for similar indicators across the estate.",
        ],
        "long_term": [
            "Update EDR signatures and behavioral rules.",
            "Review application control policies.",
        ],
    },
    "generic": {
        "description": "Generic incident response workflow.",
        "immediate": [
            "Triage and scope the alert.",
            "Identify affected assets and accounts.",
            "Contain confirmed malicious activity.",
        ],
        "short_term": [
            "Perform root-cause analysis.",
            "Eradicate persistence mechanisms.",
        ],
        "long_term": [
            "Document lessons learned.",
            "Tune detection logic and controls.",
        ],
    },
}


class KnowledgeBase:
    """In-memory and persistent security knowledge base."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    @staticmethod
    def lookup_mitre(technique_id: str | None) -> dict[str, str]:
        if not technique_id:
            return {"name": "Unknown", "tactic": "Unknown"}
        tid = technique_id.strip().upper()
        return MITRE_TECHNIQUES.get(tid, {"name": "Unknown", "tactic": "Unknown"})

    @staticmethod
    def playbook_for(technique_id: str | None, title: str = "") -> dict[str, Any]:
        lower = f"{title} {technique_id or ''}".lower()
        if "brute" in lower or "logon" in lower or technique_id == "T1110":
            return DEFAULT_RESPONSE_PLAYBOOKS["brute_force"]
        if "scan" in lower or technique_id == "T1046":
            return DEFAULT_RESPONSE_PLAYBOOKS["port_scan"]
        if "malware" in lower or "ransom" in lower:
            return DEFAULT_RESPONSE_PLAYBOOKS["malware"]
        return DEFAULT_RESPONSE_PLAYBOOKS["generic"]

    async def seed_defaults(self) -> None:
        if not self.db:
            return
        for tid, info in MITRE_TECHNIQUES.items():
            result = await self.db.execute(
                select(KnowledgeBaseItem).where(KnowledgeBaseItem.technique_id == tid)
            )
            if not result.scalar_one_or_none():
                item = KnowledgeBaseItem(
                    technique_id=tid,
                    tactic=info["tactic"],
                    name=info["name"],
                    description=f"MITRE ATT&CK technique {tid}: {info['name']}.",
                    source="mitre-attack",
                )
                self.db.add(item)

            result_tech = await self.db.execute(
                select(MITRETechnique).where(MITRETechnique.technique_id == tid)
            )
            if not result_tech.scalar_one_or_none():
                mitre = MITRETechnique(
                    technique_id=tid,
                    tactic=info["tactic"],
                    name=info["name"],
                    description=f"MITRE ATT&CK technique {tid}: {info['name']}.",
                    detection_status="planned",
                )
                self.db.add(mitre)
        await self.db.commit()

    async def find_by_technique(self, technique_id: str) -> KnowledgeBaseItem | None:
        if not self.db:
            return None
        result = await self.db.execute(
            select(KnowledgeBaseItem).where(KnowledgeBaseItem.technique_id == technique_id)
        )
        return result.scalar_one_or_none()
