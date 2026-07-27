from pydantic import BaseModel, ConfigDict, Field


class ThreatIntelRequest(BaseModel):
    indicator: str = Field(..., min_length=1, max_length=512, description="IOC to enrich")
    type: str | None = Field(None, description="Optional IOC type (ip, domain, hash, url, cve, email, mitre_technique)")


class ThreatIntelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    indicator: str
    type: str
    sources: list[dict]
    reputation_score: int = Field(..., ge=0, le=100)
    confidence: int = Field(..., ge=0, le=100)
    country: str | None = None
    asn: str | None = None
    threat_category: str | None = None
    malware: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None


class ThreatIOCEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    type: str
    value: str
    severity: str
    reputation_score: int
    threat_score: int
    confidence: int
    malicious: bool
    source_count: int
    country: str | None = None
    asn: str | None = None
    isp: str | None = None
    threat_category: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None


class ThreatIOCDetail(ThreatIOCEntry):
    sources: list[dict] = []
    scoring: dict | None = None
    related_alerts: list[dict] = []
    related_incidents: list[dict] = []
    related_campaigns: list[dict] = []
    related_malware: list[dict] = []
    related_actors: list[dict] = []


class MalwareEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    family: str
    aliases: str | None = None
    category: str | None = None
    description: str | None = None
    infection_vectors: str | None = None
    persistence_methods: str | None = None
    privilege_escalation: str | None = None
    c2_behavior: str | None = None
    mitre_techniques: str | None = None
    known_iocs: str | None = None
    affected_os: str | None = None
    remediation_guidance: str | None = None


class ThreatActorEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    aliases: str | None = None
    country: str | None = None
    motivation: str | None = None
    description: str | None = None
    targeted_sectors: str | None = None
    targeted_regions: str | None = None
    techniques: str | None = None


class CampaignEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    campaign_name: str
    status: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    targeted_sectors: str | None = None
    targeted_regions: str | None = None


class CampaignDetail(CampaignEntry):
    iocs: list[ThreatIOCEntry] = []
    malware: list[MalwareEntry] = []
    actors: list[ThreatActorEntry] = []


class VulnerabilityEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    cve: str
    cvss_score: int | None = None
    severity: str | None = None
    exploit_available: bool = False
    affected_software: str | None = None
    description: str | None = None
    cisa_kev: bool = False
    remediation_priority: str
    patch_recommendations: str | None = None


class ThreatDashboard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_iocs: int
    malicious_iocs: int
    new_iocs_24h: int
    top_malicious_ips: list[dict]
    top_malware_families: list[dict]
    active_campaigns: list[dict]
    high_risk_vulnerabilities: list[dict]
    top_targeted_assets: list[dict]
    ioc_trend: list[dict]
    score_distribution: list[dict]
    feed_health: list[dict]


class ThreatGraph(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nodes: list[dict]
    edges: list[dict]


class ThreatMapPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    lat: float
    lon: float
    label: str
    type: str
    score: int


class ThreatSearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    iocs: list[ThreatIOCEntry]
    malware: list[MalwareEntry]
    actors: list[ThreatActorEntry]
    campaigns: list[CampaignEntry]
    vulnerabilities: list[VulnerabilityEntry]
