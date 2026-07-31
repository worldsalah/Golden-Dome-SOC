from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Table, JSON
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.utils.datetime_helper import utc_now


class UserRole(str, PyEnum):
    SUPER_ADMIN = "super_admin"
    SECURITY_MANAGER = "security_manager"
    ANALYST = "analyst"
    IT_ADMINISTRATOR = "it_administrator"
    EXECUTIVE = "executive"
    # Legacy aliases (mapped at runtime)
    ADMIN = "admin"
    SOC_ANALYST = "soc_analyst"
    VIEWER = "viewer"


ROLE_MIGRATION_MAP = {
    "admin": "super_admin",
    "soc_analyst": "analyst",
    "viewer": "executive",
}


class AlertStatus(str, PyEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IncidentSeverity(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AssetType(str, PyEnum):
    FIREWALL = "firewall"
    WINDOWS_SERVER = "windows_server"
    LINUX_SERVER = "linux_server"
    DATABASE = "database"
    WORKSTATION = "workstation"
    APPLICATION = "application"
    UNKNOWN = "unknown"


incident_alert_association = Table(
    "incident_alerts",
    Base.metadata,
    Column("incident_id", ForeignKey("incidents.id"), primary_key=True),
    Column("alert_id", ForeignKey("alerts.id"), primary_key=True),
)

ioc_alert_association = Table(
    "ioc_alert_links",
    Base.metadata,
    Column("ioc_id", Integer, ForeignKey("threat_iocs.id"), primary_key=True),
    Column("alert_id", Integer, ForeignKey("alerts.id"), primary_key=True),
)

ioc_incident_association = Table(
    "ioc_incident_links",
    Base.metadata,
    Column("ioc_id", Integer, ForeignKey("threat_iocs.id"), primary_key=True),
    Column("incident_id", Integer, ForeignKey("incidents.id"), primary_key=True),
)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(128), unique=True, index=True, nullable=False)
    industry = Column(String(128), nullable=True)
    contact_email = Column(String(128), nullable=True)
    contact_phone = Column(String(64), nullable=True)
    address = Column(Text, nullable=True)
    plan = Column(String(64), default="professional", nullable=False)
    max_users = Column(Integer, default=50, nullable=False)
    max_assets = Column(Integer, default=500, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    users = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default=UserRole.ANALYST.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # MFA
    mfa_secret = Column(String(255), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_backup_codes = Column(Text, nullable=True)

    # Session & audit
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(64), nullable=True)
    failed_login_count = Column(Integer, default=0, nullable=False)
    password_changed_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="users")
    assigned_alerts = relationship("Alert", back_populates="assigned_user")
    assigned_incidents = relationship("Incident", back_populates="assigned_user")
    created_reports = relationship("Report", back_populates="created_by")
    timeline_events = relationship("IncidentTimeline", back_populates="actor")
    detection_rules = relationship("DetectionRule", back_populates="author")
    ai_feedback = relationship("AiFeedback", back_populates="user")
    ai_query_logs = relationship("AiQueryLog", back_populates="user")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    hostname = Column(String(128), nullable=False)
    ip_address = Column(String(64), index=True, nullable=True)
    type = Column(String(64), default=AssetType.UNKNOWN.value, nullable=False)
    operating_system = Column(String(128), nullable=True)
    criticality = Column(Integer, default=50, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    last_seen = Column(DateTime, nullable=True)
    wazuh_agent_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    alerts = relationship("Alert", back_populates="asset")
    vulnerabilities = relationship("AssetVulnerability", back_populates="asset")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    wazuh_alert_id = Column(String(64), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Integer, default=1, nullable=False)
    source_ip = Column(String(64), nullable=True)
    destination_ip = Column(String(64), nullable=True)
    rule_id = Column(String(64), nullable=True)
    mitre_technique = Column(String(64), nullable=True)
    status = Column(String(32), default=AlertStatus.NEW.value, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    raw_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    assigned_user = relationship("User", back_populates="assigned_alerts")
    asset = relationship("Asset", back_populates="alerts")
    ai_analyses = relationship("AiAnalysis", back_populates="alert")
    threat_iocs = relationship("ThreatIOC", secondary=ioc_alert_association, back_populates="linked_alerts")
    incidents = relationship(
        "Incident",
        secondary=incident_alert_association,
        back_populates="alerts",
    )


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    severity = Column(String(32), default=IncidentSeverity.MEDIUM.value, nullable=False)
    status = Column(String(32), default=IncidentStatus.OPEN.value, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    assigned_user = relationship("User", back_populates="assigned_incidents")
    ai_analyses = relationship("AiAnalysis", back_populates="incident")
    threat_iocs = relationship("ThreatIOC", secondary=ioc_incident_association, back_populates="linked_incidents")
    alerts = relationship(
        "Alert",
        secondary=incident_alert_association,
        back_populates="incidents",
    )
    timeline = relationship(
        "IncidentTimeline",
        back_populates="incident",
        order_by="IncidentTimeline.timestamp",
    )


class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("Incident", back_populates="timeline")
    actor = relationship("User", back_populates="timeline_events")


class AssetVulnerability(Base):
    __tablename__ = "asset_vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    cve = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False)
    cvss_score = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)

    asset = relationship("Asset", back_populates="vulnerabilities")


class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    indicator = Column(String(255), nullable=False, index=True)
    type = Column(String(64), nullable=False)
    source = Column(String(128), nullable=True)
    threat_category = Column(String(128), nullable=True)
    reputation_score = Column(Integer, default=0, nullable=False)
    confidence = Column(Integer, default=0, nullable=False)
    country = Column(String(128), nullable=True)
    asn = Column(String(128), nullable=True)
    malware = Column(String(255), nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, default=utc_now, nullable=False)
    last_checked = Column(DateTime, default=utc_now, nullable=False)


class IocDatabase(Base):
    __tablename__ = "ioc_database"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    value = Column(String(255), nullable=False, index=True)
    type = Column(String(64), nullable=False)
    category = Column(String(128), nullable=True)
    confidence = Column(Integer, default=0, nullable=False)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, default=utc_now, nullable=False)
    sources = Column(Text, nullable=True)


class AiAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    summary = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    confidence = Column(Integer, default=0, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    severity = Column(String(32), nullable=True)
    priority = Column(String(32), nullable=True)
    mitre_tactic = Column(String(128), nullable=True)
    mitre_technique = Column(String(255), nullable=True)
    mitre_technique_id = Column(String(64), nullable=True)
    investigation_steps = Column(Text, nullable=True)
    response_steps = Column(Text, nullable=True)
    analyst_notes = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    alert = relationship("Alert", back_populates="ai_analyses")
    incident = relationship("Incident", back_populates="ai_analyses")
    feedback = relationship("AiFeedback", back_populates="analysis", uselist=False)


class AiFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("ai_analysis.id"), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    helpful = Column(Boolean, default=False, nullable=False)
    incorrect = Column(Boolean, default=False, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    analysis = relationship("AiAnalysis", back_populates="feedback")
    user = relationship("User", back_populates="ai_feedback")


class AiQueryLog(Base):
    __tablename__ = "ai_query_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String(128), nullable=False)
    request_payload = Column(Text, nullable=True)
    response_summary = Column(Text, nullable=True)
    source = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="ai_query_logs")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    target_type = Column(String(64), nullable=False)
    target_id = Column(Integer, nullable=False, index=True)
    score = Column(Integer, default=0, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    id = Column(Integer, primary_key=True, index=True)
    feature_type = Column(String(64), nullable=False)
    record_id = Column(String(255), nullable=False, index=True)
    anomaly_score = Column(Integer, default=0, nullable=False)
    features = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class KnowledgeBaseItem(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(64), nullable=True, index=True)
    tactic = Column(String(128), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    source = Column(String(128), default="internal", nullable=False)


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Integer, default=5, nullable=False)
    category = Column(String(64), nullable=False)
    source = Column(String(64), nullable=False)
    logic = Column(Text, nullable=False)
    mitre_attack_id = Column(String(64), nullable=True)
    status = Column(String(32), default="active", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    author = relationship("User", back_populates="detection_rules")


class MITRETechnique(Base):
    __tablename__ = "mitre_techniques"

    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    tactic = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    associated_rules = Column(Text, nullable=True)
    detection_status = Column(String(32), default="planned", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    report_type = Column(String(64), default="security", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    created_by = relationship("User", back_populates="created_reports")


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trigger = Column(String(64), default="manual", nullable=False)
    trigger_config = Column(Text, nullable=True, default="{}")
    status = Column(String(32), default="active", nullable=False)
    category = Column(String(64), default="response", nullable=False)
    version = Column(String(32), default="1.0.0", nullable=False)
    tags = Column(Text, nullable=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    actions = Column(Text, nullable=False, default="[]")
    nodes = Column(Text, nullable=False, default="[]")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    executions = relationship("PlaybookExecution", back_populates="playbook", cascade="all, delete-orphan")


class PlaybookExecution(Base):
    __tablename__ = "playbook_executions"

    id = Column(Integer, primary_key=True, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False)
    status = Column(String(32), default="running", nullable=False)
    triggered_by = Column(String(64), nullable=True)
    trigger_event = Column(String(128), nullable=True)
    input_data = Column(Text, nullable=True)
    output_log = Column(Text, nullable=True)
    context = Column(Text, nullable=True, default="{}")
    current_node_id = Column(String(64), nullable=True)
    node_states = Column(Text, nullable=True, default="{}")
    results = Column(Text, nullable=True, default="{}")
    logs = Column(Text, nullable=True, default="[]")
    approval_status = Column(String(32), default="na", nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    playbook = relationship("Playbook", back_populates="executions")


class WorkflowApproval(Base):
    __tablename__ = "workflow_approvals"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("playbook_executions.id"), nullable=False, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=True)
    node_id = Column(String(64), nullable=True)
    action_summary = Column(Text, nullable=True)
    risk_level = Column(String(32), default="medium", nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    requested_by = Column(String(128), nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    details = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class WorkflowTimelineEvent(Base):
    __tablename__ = "workflow_timeline"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("playbook_executions.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=True)
    event_type = Column(String(64), nullable=False)
    message = Column(Text, nullable=True)
    actor = Column(String(128), nullable=True)
    details = Column(Text, nullable=True, default="{}")
    timestamp = Column(DateTime, default=utc_now, nullable=False)


class WorkflowEvidence(Base):
    __tablename__ = "workflow_evidence"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("playbook_executions.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=True)
    evidence_type = Column(String(64), nullable=False)
    source = Column(String(255), nullable=True)
    content = Column(Text, nullable=True, default="{}")
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class WorkflowActionLog(Base):
    __tablename__ = "workflow_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("playbook_executions.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=True)
    action_type = Column(String(64), nullable=False)
    status = Column(String(32), default="ok", nullable=False)
    input_data = Column(Text, nullable=True, default="{}")
    output_data = Column(Text, nullable=True, default="{}")
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


campaign_ioc_association = Table(
    "campaign_ioc_links",
    Base.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),
    Column("ioc_id", Integer, ForeignKey("threat_iocs.id"), primary_key=True),
)

campaign_malware_association = Table(
    "campaign_malware_links",
    Base.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),
    Column("malware_id", Integer, ForeignKey("malware.id"), primary_key=True),
)

campaign_actor_association = Table(
    "campaign_actor_links",
    Base.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),
    Column("actor_id", Integer, ForeignKey("threat_actors.id"), primary_key=True),
)

class ThreatIOC(Base):
    __tablename__ = "threat_iocs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    type = Column(String(64), nullable=False, index=True)
    value = Column(String(512), nullable=False, index=True)
    first_seen = Column(DateTime, default=utc_now, nullable=False)
    last_seen = Column(DateTime, default=utc_now, nullable=False)
    confidence = Column(Integer, default=0, nullable=False)
    reputation_score = Column(Integer, default=0, nullable=False)
    threat_score = Column(Integer, default=0, nullable=False)
    severity = Column(String(32), default="low", nullable=False)
    malicious = Column(Boolean, default=False, nullable=False)
    source_count = Column(Integer, default=0, nullable=False)
    country = Column(String(128), nullable=True)
    asn = Column(String(128), nullable=True)
    isp = Column(String(255), nullable=True)
    threat_category = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    sources = relationship("ThreatSource", back_populates="ioc", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", secondary=campaign_ioc_association, back_populates="iocs")
    linked_alerts = relationship("Alert", secondary=ioc_alert_association, back_populates="threat_iocs")
    linked_incidents = relationship("Incident", secondary=ioc_incident_association, back_populates="threat_iocs")


class ThreatSource(Base):
    __tablename__ = "threat_sources"

    id = Column(Integer, primary_key=True, index=True)
    ioc_id = Column(Integer, ForeignKey("threat_iocs.id"), nullable=False, index=True)
    provider = Column(String(128), nullable=False)
    provider_score = Column(Integer, nullable=True)
    provider_reference = Column(String(512), nullable=True)
    raw_data = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=utc_now, nullable=False)

    ioc = relationship("ThreatIOC", back_populates="sources")


class Malware(Base):
    __tablename__ = "malware"

    id = Column(Integer, primary_key=True, index=True)
    family = Column(String(255), nullable=False, index=True)
    aliases = Column(Text, nullable=True)
    category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    infection_vectors = Column(Text, nullable=True)
    persistence_methods = Column(Text, nullable=True)
    privilege_escalation = Column(Text, nullable=True)
    c2_behavior = Column(Text, nullable=True)
    mitre_techniques = Column(Text, nullable=True)
    known_iocs = Column(Text, nullable=True)
    affected_os = Column(Text, nullable=True)
    remediation_guidance = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    campaigns = relationship("Campaign", secondary=campaign_malware_association, back_populates="malware")


class ThreatActor(Base):
    __tablename__ = "threat_actors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    aliases = Column(Text, nullable=True)
    country = Column(String(128), nullable=True)
    motivation = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    targeted_sectors = Column(Text, nullable=True)
    targeted_regions = Column(Text, nullable=True)
    techniques = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    campaigns = relationship("Campaign", secondary=campaign_actor_association, back_populates="actors")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String(255), nullable=False, index=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(32), default="active", nullable=False)
    description = Column(Text, nullable=True)
    targeted_sectors = Column(Text, nullable=True)
    targeted_regions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    iocs = relationship("ThreatIOC", secondary=campaign_ioc_association, back_populates="campaigns")
    malware = relationship("Malware", secondary=campaign_malware_association, back_populates="campaigns")
    actors = relationship("ThreatActor", secondary=campaign_actor_association, back_populates="campaigns")


class VulnerabilityIntelligence(Base):
    __tablename__ = "vulnerability_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    cve = Column(String(64), nullable=False, index=True)
    cvss_score = Column(Integer, nullable=True)
    severity = Column(String(32), nullable=True)
    exploit_available = Column(Boolean, default=False, nullable=False)
    affected_software = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    cisa_kev = Column(Boolean, default=False, nullable=False)
    remediation_priority = Column(String(32), default="low", nullable=False)
    patch_recommendations = Column(Text, nullable=True)
    affected_assets = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(64), nullable=True)
    action = Column(String(128), nullable=False)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    status = Column(String(32), default="success", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    token_jti = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


class Connector(Base):
    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    connector_type = Column(String(64), nullable=False, index=True)
    category = Column(String(64), nullable=False)
    status = Column(String(32), default="disconnected", nullable=False)
    config = Column(Text, nullable=True, default="{}")
    credentials = Column(Text, nullable=True)
    last_connected = Column(DateTime, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    health_status = Column(String(32), default="unknown", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ConnectorLog(Base):
    __tablename__ = "connector_logs"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(Integer, ForeignKey("connectors.id"), nullable=False, index=True)
    level = Column(String(32), default="info", nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    scopes = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
