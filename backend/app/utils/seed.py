import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import hash_password
from app.database.models import (
    Asset,
    Campaign,
    DetectionRule,
    KnowledgeBaseItem,
    Malware,
    ThreatActor,
    User,
    UserRole,
    VulnerabilityIntelligence,
)
from app.services.ai_engine.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

DEFAULT_ASSETS = [
    {
        "hostname": "FortiGate-60F",
        "ip_address": "192.168.1.1",
        "type": "firewall",
        "operating_system": "FortiOS",
        "criticality": 95,
    },
    {
        "hostname": "Windows-Server-2019",
        "ip_address": "192.168.1.10",
        "type": "windows_server",
        "operating_system": "Windows Server 2019",
        "criticality": 85,
    },
    {
        "hostname": "Linux-Database-Server",
        "ip_address": "192.168.1.20",
        "type": "database",
        "operating_system": "Ubuntu 22.04 LTS",
        "criticality": 90,
    },
    {
        "hostname": "Linux-Web-Server",
        "ip_address": "192.168.1.30",
        "type": "linux_server",
        "operating_system": "Debian 12",
        "criticality": 70,
    },
]

DEFAULT_DETECTION_RULES = [
    {
        "name": "SSH Brute Force",
        "description": "Detect multiple failed SSH authentication attempts from the same source IP.",
        "severity": 10,
        "category": "Authentication",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200001' and event.get('rule', {}).get('level', 0) >= 10",
        "mitre_attack_id": "T1110",
        "status": "active",
    },
    {
        "name": "Windows Failed Login Brute Force",
        "description": "Detect repeated Windows failed logins indicating brute force or password spraying.",
        "severity": 13,
        "category": "Authentication",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200002'",
        "mitre_attack_id": "T1110",
        "status": "active",
    },
    {
        "name": "Suspicious PowerShell Execution",
        "description": "Detect execution of suspicious PowerShell commands.",
        "severity": 10,
        "category": "Execution",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200020'",
        "mitre_attack_id": "T1059.001",
        "status": "active",
    },
    {
        "name": "Port Scanning",
        "description": "Detect network reconnaissance through multiple denied connections from a single source.",
        "severity": 12,
        "category": "Network",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200040'",
        "mitre_attack_id": "T1046",
        "status": "active",
    },
    {
        "name": "SQL Injection Attempt",
        "description": "Detect potential SQL injection patterns in web server logs.",
        "severity": 10,
        "category": "Web Security",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200070'",
        "mitre_attack_id": "T1190",
        "status": "active",
    },
    {
        "name": "Known Malicious Hash Detected",
        "description": "Detect execution or presence of a known malicious file hash.",
        "severity": 12,
        "category": "Malware",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200060'",
        "mitre_attack_id": "T1204",
        "status": "active",
    },
    {
        "name": "RDP Lateral Movement",
        "description": "Detect suspicious RDP connection attempts to sensitive segments.",
        "severity": 12,
        "category": "Lateral Movement",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200050'",
        "mitre_attack_id": "T1021.001",
        "status": "active",
    },
    {
        "name": "Suspicious Scheduled Task Creation",
        "description": "Detect creation of a new scheduled task that may indicate persistence.",
        "severity": 10,
        "category": "Persistence",
        "source": "Wazuh",
        "logic": "event.get('rule', {}).get('id') == '200030'",
        "mitre_attack_id": "T1053.005",
        "status": "active",
    },
]

DEFAULT_MALWARE = [
    {
        "family": "Emotet",
        "aliases": "Heodo, Geodo",
        "category": "Trojan",
        "description": "A modular banking trojan often used as a downloader for other malware.",
        "infection_vectors": "Spear-phishing emails with malicious attachments or links.",
        "persistence_methods": "Scheduled tasks, Windows services, registry run keys.",
        "privilege_escalation": "Process injection, token theft.",
        "c2_behavior": "HTTP/HTTPS C2 over dynamic DGA domains.",
        "mitre_techniques": "T1566.001,T1059.001,T1053.005,T1071.001",
        "known_iocs": "185.220.101.32,emotet-c2.example",
        "affected_os": "Windows",
        "remediation_guidance": "Isolate infected hosts, reset credentials, block IOCs at perimeter.",
    },
    {
        "family": "Cobalt Strike",
        "aliases": "CobaltStrike",
        "category": "Penetration Testing Tool / RAT",
        "description": "Commercial post-exploitation framework frequently abused by threat actors.",
        "infection_vectors": "Phishing, exploitation, payload injection.",
        "persistence_methods": "Service installation, scheduled tasks.",
        "privilege_escalation": "Exploitation for privilege escalation.",
        "c2_behavior": "Encrypted BEACON C2 over HTTP/HTTPS/DNS.",
        "mitre_techniques": "T1071.001,T1059.003,T1021.002,T1543.003",
        "known_iocs": "192.0.2.100,cobalt-c2.example",
        "affected_os": "Windows, Linux",
        "remediation_guidance": "Hunt for BEACON payloads, review egress traffic, rebuild compromised hosts.",
    },
]

DEFAULT_ACTORS = [
    {
        "name": "APT28",
        "aliases": "Fancy Bear, Sofacy, Strontium",
        "country": "Russia",
        "motivation": "Espionage, geopolitical influence",
        "description": "A Russian state-sponsored cyber espionage group targeting governments and militaries.",
        "targeted_sectors": "Government, Defense, Energy, Media",
        "targeted_regions": "Europe, North America, Middle East",
        "techniques": "T1598,T1566.001,T1053,T1003",
    },
    {
        "name": "Lazarus Group",
        "aliases": "HIDDEN COBRA, Zinc, Nickel Academy",
        "country": "North Korea",
        "motivation": "Financial gain, espionage, sabotage",
        "description": "A North Korean state-sponsored group involved in destructive attacks and heists.",
        "targeted_sectors": "Finance, Media, Critical Infrastructure",
        "targeted_regions": "Global",
        "techniques": "T1566.001,T1204.002,T1059,T1485",
    },
]

DEFAULT_CAMPAIGNS = [
    {
        "campaign_name": "Operation BruteForce",
        "status": "active",
        "description": "Ongoing brute force campaign targeting exposed RDP and SSH services.",
        "targeted_sectors": "Healthcare, Education",
        "targeted_regions": "North America",
    },
]

DEFAULT_VULNERABILITIES = [
    {
        "cve": "CVE-2023-23397",
        "cvss_score": 95,
        "severity": "critical",
        "exploit_available": True,
        "affected_software": "Microsoft Outlook",
        "description": "Microsoft Outlook privilege escalation vulnerability exploited in the wild.",
        "cisa_kev": True,
        "remediation_priority": "critical",
        "patch_recommendations": "Apply Microsoft security update KB5023307.",
    },
]

async def seed_database(db: AsyncSession) -> None:
    """Seed the database with an initial admin user and default assets."""
    from app.config.settings import get_settings

    settings = get_settings()
    result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
    if not result.scalar_one_or_none():
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(admin)
        logger.info("Created default admin user")

    for asset_data in DEFAULT_ASSETS:
        result = await db.execute(
            select(Asset).where(Asset.hostname == asset_data["hostname"])
        )
        if not result.scalar_one_or_none():
            asset = Asset(**asset_data)
            db.add(asset)
            logger.info("Created default asset: %s", asset_data["hostname"])

    kb = KnowledgeBase(db)
    await kb.seed_defaults()
    logger.info("Seeded security knowledge base")

    for rule_data in DEFAULT_DETECTION_RULES:
        result = await db.execute(
            select(DetectionRule).where(DetectionRule.name == rule_data["name"])
        )
        if not result.scalar_one_or_none():
            rule = DetectionRule(**rule_data)
            db.add(rule)
            logger.info("Created default detection rule: %s", rule_data["name"])

    for malware_data in DEFAULT_MALWARE:
        result = await db.execute(select(Malware).where(Malware.family == malware_data["family"]))
        if not result.scalar_one_or_none():
            db.add(Malware(**malware_data))
            logger.info("Created default malware profile: %s", malware_data["family"])

    created_actors = {}
    for actor_data in DEFAULT_ACTORS:
        result = await db.execute(select(ThreatActor).where(ThreatActor.name == actor_data["name"]))
        if not result.scalar_one_or_none():
            actor = ThreatActor(**actor_data)
            db.add(actor)
            await db.flush()
            created_actors[actor.name] = actor
            logger.info("Created default threat actor: %s", actor_data["name"])

    created_malware_map = {}
    for family in ("Emotet", "Cobalt Strike"):
        result = await db.execute(select(Malware).where(Malware.family == family))
        mal = result.scalar_one_or_none()
        if mal:
            created_malware_map[family] = mal

    for campaign_data in DEFAULT_CAMPAIGNS:
        result = await db.execute(select(Campaign).where(Campaign.campaign_name == campaign_data["campaign_name"]))
        if not result.scalar_one_or_none():
            campaign = Campaign(**campaign_data)
            campaign.malware = list(created_malware_map.values())
            if created_actors.get("APT28"):
                campaign.actors = [created_actors["APT28"]]
            db.add(campaign)
            logger.info("Created default campaign: %s", campaign_data["campaign_name"])

    for vuln_data in DEFAULT_VULNERABILITIES:
        result = await db.execute(select(VulnerabilityIntelligence).where(VulnerabilityIntelligence.cve == vuln_data["cve"]))
        if not result.scalar_one_or_none():
            db.add(VulnerabilityIntelligence(**vuln_data))
            logger.info("Created default vulnerability: %s", vuln_data["cve"])

    await db.commit()
