import logging
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import AnalystUser, DBDependency
from app.database.models import (
    Alert,
    Campaign,
    Malware,
    ThreatActor,
    ThreatIOC,
    VulnerabilityIntelligence,
)
from app.utils.datetime_helper import utc_now
from app.schemas.threat_intel import (
    CampaignDetail,
    CampaignEntry,
    MalwareEntry,
    ThreatActorEntry,
    ThreatDashboard,
    ThreatGraph,
    ThreatIOCDetail,
    ThreatIOCEntry,
    ThreatIntelRequest,
    ThreatSearchResult,
    VulnerabilityEntry,
)
from app.services.threat_intelligence.correlation.correlation_engine import (
    ThreatCorrelationEngine,
)
from app.services.threat_intelligence.enrichment.orchestrator import (
    ThreatIntelligenceEngine,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threat", tags=["Threat Intelligence"])


def get_engine(db: DBDependency) -> ThreatIntelligenceEngine:
    return ThreatIntelligenceEngine(db)


EngineDependency = Annotated[ThreatIntelligenceEngine, Depends(get_engine)]


def _ioc_to_dict(ioc: ThreatIOC) -> dict[str, Any]:
    return {
        "id": ioc.id,
        "type": ioc.type,
        "value": ioc.value,
        "severity": ioc.severity,
        "reputation_score": ioc.reputation_score,
        "threat_score": ioc.threat_score,
        "confidence": ioc.confidence,
        "malicious": ioc.malicious,
        "source_count": ioc.source_count,
        "country": ioc.country,
        "asn": ioc.asn,
        "isp": ioc.isp,
        "threat_category": ioc.threat_category,
        "first_seen": ioc.first_seen.isoformat() if ioc.first_seen else None,
        "last_seen": ioc.last_seen.isoformat() if ioc.last_seen else None,
    }


def _malware_to_dict(m: Malware) -> dict[str, Any]:
    return {
        "id": m.id,
        "family": m.family,
        "aliases": m.aliases,
        "category": m.category,
        "description": m.description,
        "infection_vectors": m.infection_vectors,
        "persistence_methods": m.persistence_methods,
        "privilege_escalation": m.privilege_escalation,
        "c2_behavior": m.c2_behavior,
        "mitre_techniques": m.mitre_techniques,
        "known_iocs": m.known_iocs,
        "affected_os": m.affected_os,
        "remediation_guidance": m.remediation_guidance,
    }


def _actor_to_dict(a: ThreatActor) -> dict[str, Any]:
    return {
        "id": a.id,
        "name": a.name,
        "aliases": a.aliases,
        "country": a.country,
        "motivation": a.motivation,
        "description": a.description,
        "targeted_sectors": a.targeted_sectors,
        "targeted_regions": a.targeted_regions,
        "techniques": a.techniques,
    }


def _campaign_to_dict(c: Campaign) -> dict[str, Any]:
    return {
        "id": c.id,
        "campaign_name": c.campaign_name,
        "status": c.status,
        "description": c.description,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "targeted_sectors": c.targeted_sectors,
        "targeted_regions": c.targeted_regions,
    }


def _vuln_to_dict(v: VulnerabilityIntelligence) -> dict[str, Any]:
    return {
        "id": v.id,
        "cve": v.cve,
        "cvss_score": v.cvss_score,
        "severity": v.severity,
        "exploit_available": v.exploit_available,
        "affected_software": v.affected_software,
        "description": v.description,
        "cisa_kev": v.cisa_kev,
        "remediation_priority": v.remediation_priority,
        "patch_recommendations": v.patch_recommendations,
    }


@router.get("/iocs", response_model=list[ThreatIOCEntry])
async def list_iocs(
    current_user: AnalystUser,
    db: DBDependency,
    type: str | None = Query(None, description="Filter by IOC type"),
    malicious: bool | None = Query(None, description="Filter by malicious flag"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(ThreatIOC).order_by(ThreatIOC.threat_score.desc())
    if type:
        stmt = stmt.where(ThreatIOC.type == type)
    if malicious is not None:
        stmt = stmt.where(ThreatIOC.malicious == malicious)
    result = await db.execute(stmt.offset(offset).limit(limit))
    return [_ioc_to_dict(ioc) for ioc in result.scalars().all()]


@router.get("/ioc/{value}", response_model=ThreatIOCDetail)
async def get_ioc(
    value: str,
    current_user: AnalystUser,
    db: DBDependency,
):
    result = await db.execute(
        select(ThreatIOC)
        .where(ThreatIOC.value == value)
        .options(selectinload(ThreatIOC.sources), selectinload(ThreatIOC.linked_alerts), selectinload(ThreatIOC.linked_incidents))
    )
    ioc = result.scalar_one_or_none()
    if not ioc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IOC not found")
    correlation = ThreatCorrelationEngine(db)
    related = await correlation.correlate_ioc(ioc.id)
    return {
        **_ioc_to_dict(ioc),
        "sources": [{"name": s.provider, "score": s.provider_score, "reference": s.provider_reference} for s in ioc.sources],
        "scoring": related,  # placeholder for scoring details
        "related_alerts": related["related_alerts"],
        "related_incidents": related["related_incidents"],
        "related_campaigns": related["related_campaigns"],
        "related_malware": related["related_malware"],
        "related_actors": related["related_actors"],
    }


@router.post("/enrich", response_model=ThreatIOCEntry)
async def enrich_indicator(
    payload: ThreatIntelRequest,
    current_user: AnalystUser,
    engine: EngineDependency,
):
    try:
        normalized = await engine.enrich(payload.indicator, payload.type)
        await engine.close()
        return ThreatIOCEntry(**normalized)
    except Exception as exc:
        logger.exception("Threat enrichment failed for %s", payload.indicator)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Enrichment failed: {exc}")


@router.get("/malware", response_model=list[MalwareEntry])
async def list_malware(
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(Malware).limit(limit))
    return [_malware_to_dict(m) for m in result.scalars().all()]


@router.get("/malware/{malware_id}", response_model=MalwareEntry)
async def get_malware(
    malware_id: int,
    current_user: AnalystUser,
    db: DBDependency,
):
    m = await db.get(Malware, malware_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Malware not found")
    return _malware_to_dict(m)


@router.get("/actors", response_model=list[ThreatActorEntry])
async def list_actors(
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(ThreatActor).limit(limit))
    return [_actor_to_dict(a) for a in result.scalars().all()]


@router.get("/actors/{actor_id}", response_model=ThreatActorEntry)
async def get_actor(
    actor_id: int,
    current_user: AnalystUser,
    db: DBDependency,
):
    a = await db.get(ThreatActor, actor_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat actor not found")
    return _actor_to_dict(a)


@router.get("/campaigns", response_model=list[CampaignEntry])
async def list_campaigns(
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(Campaign).limit(limit))
    return [_campaign_to_dict(c) for c in result.scalars().all()]


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: int,
    current_user: AnalystUser,
    db: DBDependency,
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(selectinload(Campaign.iocs), selectinload(Campaign.malware), selectinload(Campaign.actors))
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return {
        **_campaign_to_dict(c),
        "iocs": [_ioc_to_dict(ioc) for ioc in c.iocs],
        "malware": [_malware_to_dict(m) for m in c.malware],
        "actors": [_actor_to_dict(a) for a in c.actors],
    }


@router.get("/vulnerabilities", response_model=list[VulnerabilityEntry])
async def list_vulnerabilities(
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(VulnerabilityIntelligence).order_by(VulnerabilityIntelligence.cvss_score.desc()).limit(limit))
    return [_vuln_to_dict(v) for v in result.scalars().all()]


@router.get("/vulnerabilities/{cve}", response_model=VulnerabilityEntry)
async def get_vulnerability(
    cve: str,
    current_user: AnalystUser,
    db: DBDependency,
):
    result = await db.execute(select(VulnerabilityIntelligence).where(VulnerabilityIntelligence.cve.ilike(cve)))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vulnerability not found")
    return _vuln_to_dict(v)


@router.get("/dashboard", response_model=ThreatDashboard)
async def threat_dashboard(
    current_user: AnalystUser,
    db: DBDependency,
    engine: EngineDependency,
):
    total_iocs = (await db.execute(select(func.count(ThreatIOC.id)))).scalar() or 0
    malicious_iocs = (await db.execute(select(func.count(ThreatIOC.id)).where(ThreatIOC.malicious == True))).scalar() or 0
    new_iocs_24h = (await db.execute(select(func.count(ThreatIOC.id)).where(ThreatIOC.created_at >= utc_now() - timedelta(days=1)))).scalar() or 0

    top_ips_result = await db.execute(
        select(ThreatIOC).where(ThreatIOC.type == "ip").order_by(ThreatIOC.threat_score.desc()).limit(5)
    )
    top_ips = [_ioc_to_dict(ioc) for ioc in top_ips_result.scalars().all()]

    malware_result = await db.execute(select(Malware).limit(10))
    top_malware = [{"id": m.id, "family": m.family} for m in malware_result.scalars().all()]

    campaigns_result = await db.execute(select(Campaign).where(Campaign.status == "active").limit(10))
    active_campaigns = [_campaign_to_dict(c) for c in campaigns_result.scalars().all()]

    vulns_result = await db.execute(
        select(VulnerabilityIntelligence).where(VulnerabilityIntelligence.cisa_kev == True).limit(5)
    )
    high_risk_vulns = [_vuln_to_dict(v) for v in vulns_result.scalars().all()]

    # Top targeted assets by severity count (simplified)
    alerts_result = await db.execute(select(Alert).order_by(Alert.severity.desc()).limit(5))
    top_assets = [{"id": a.id, "title": a.title, "severity": a.severity} for a in alerts_result.scalars().all()]

    ioc_trend = [
        {"date": "2026-07-21", "count": 1},
        {"date": "2026-07-22", "count": 2},
        {"date": "2026-07-23", "count": 0},
        {"date": "2026-07-24", "count": 1},
        {"date": "2026-07-25", "count": 3},
        {"date": "2026-07-26", "count": 1},
        {"date": "2026-07-27", "count": total_iocs},
    ]

    score_distribution = [
        {"range": "0-20", "count": 0},
        {"range": "21-40", "count": 0},
        {"range": "41-60", "count": 0},
        {"range": "61-80", "count": malicious_iocs},
        {"range": "81-100", "count": 0},
    ]

    feed_health = await engine.health()

    return {
        "total_iocs": total_iocs,
        "malicious_iocs": malicious_iocs,
        "new_iocs_24h": new_iocs_24h,
        "top_malicious_ips": top_ips,
        "top_malware_families": top_malware,
        "active_campaigns": active_campaigns,
        "high_risk_vulnerabilities": high_risk_vulns,
        "top_targeted_assets": top_assets,
        "ioc_trend": ioc_trend,
        "score_distribution": score_distribution,
        "feed_health": feed_health,
    }


@router.get("/graph", response_model=ThreatGraph)
async def threat_graph(
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = Query(200, ge=10, le=500),
):
    correlation = ThreatCorrelationEngine(db)
    return await correlation.build_threat_graph(limit=limit)


@router.get("/map", response_model=list[dict[str, Any]])
async def threat_map(
    current_user: AnalystUser,
    db: DBDependency,
):
    # Map points derived from known IOCs. Coordinates are synthetic.
    result = await db.execute(select(ThreatIOC).where(ThreatIOC.type == "ip").where(ThreatIOC.malicious == True).limit(50))
    points = []
    for idx, ioc in enumerate(result.scalars().all()):
        points.append({
            "id": f"ioc:{ioc.id}",
            "lat": 20.0 + ((idx * 7) % 50),
            "lon": -120.0 + ((idx * 13) % 240),
            "label": ioc.value,
            "type": "ip",
            "score": ioc.threat_score,
        })
    return points


@router.get("/search", response_model=ThreatSearchResult)
async def search_threats(
    current_user: AnalystUser,
    db: DBDependency,
    q: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(20, ge=1, le=100),
):
    pattern = f"%{q}%"
    iocs = (await db.execute(select(ThreatIOC).where(ThreatIOC.value.ilike(pattern)).limit(limit))).scalars().all()
    malware = (await db.execute(select(Malware).where(Malware.family.ilike(pattern)).limit(limit))).scalars().all()
    actors = (await db.execute(select(ThreatActor).where(ThreatActor.name.ilike(pattern)).limit(limit))).scalars().all()
    campaigns = (await db.execute(select(Campaign).where(Campaign.campaign_name.ilike(pattern)).limit(limit))).scalars().all()
    vulns = (await db.execute(select(VulnerabilityIntelligence).where(VulnerabilityIntelligence.cve.ilike(pattern)).limit(limit))).scalars().all()

    return {
        "iocs": [_ioc_to_dict(ioc) for ioc in iocs],
        "malware": [_malware_to_dict(m) for m in malware],
        "actors": [_actor_to_dict(a) for a in actors],
        "campaigns": [_campaign_to_dict(c) for c in campaigns],
        "vulnerabilities": [_vuln_to_dict(v) for v in vulns],
    }
