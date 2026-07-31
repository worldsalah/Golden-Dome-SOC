import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AnalystUser
from app.services.wazuh_service import WazuhService, WazuhServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wazuh", tags=["Wazuh Integration"])


def _get_service() -> WazuhService:
    return WazuhService()


WazuhDep = Annotated[WazuhService, Depends(_get_service)]


def _wazuh_error(exc: Exception) -> dict[str, Any]:
    logger.exception("Wazuh API call failed")
    detail = str(exc)
    if isinstance(exc, WazuhServiceError):
        detail = "Wazuh API unreachable or authentication failed"
    return {"wazuh_available": False, "error": detail}


@router.get("/agents")
async def list_agents(
    current_user: AnalystUser,
    service: WazuhDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List Wazuh agents."""
    try:
        return await service.get_agents(limit=limit, offset=offset)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/agents/stats")
async def agents_stats(
    current_user: AnalystUser,
    service: WazuhDep,
    agent_id: str | None = Query(None),
):
    try:
        return await service.get_agents_stats(agent_id=agent_id)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: AnalystUser,
    service: WazuhDep,
):
    """Get details for a specific Wazuh agent."""
    try:
        return await service.get_agent_details(agent_id)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/vulnerabilities")
async def list_vulnerabilities(
    current_user: AnalystUser,
    service: WazuhDep,
    agent_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List Wazuh vulnerabilities, optionally filtered by agent."""
    try:
        return await service.get_vulnerabilities(agent_id=agent_id, limit=limit, offset=offset)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/alerts")
async def list_alerts(
    current_user: AnalystUser,
    service: WazuhDep,
    size: int = Query(100, ge=1, le=1000),
    severity: int | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
):
    """Retrieve Wazuh alerts from the Wazuh Indexer."""
    try:
        return await service.get_alerts(
            size=size,
            severity=severity,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/security-events")
async def list_security_events(
    current_user: AnalystUser,
    service: WazuhDep,
    size: int = Query(100, ge=1, le=1000),
    rule_id: str | None = Query(None),
):
    """Retrieve Wazuh security events."""
    try:
        return await service.get_security_events(size=size, rule_id=rule_id)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/manager/info")
async def manager_info(current_user: AnalystUser, service: WazuhDep):
    try:
        return await service.get_manager_info()
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/cluster/status")
async def cluster_status(current_user: AnalystUser, service: WazuhDep):
    try:
        return await service.get_cluster_status()
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/mitre")
async def mitre(
    current_user: AnalystUser,
    service: WazuhDep,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        return await service.get_mitre(limit=limit, offset=offset)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/tasks")
async def tasks(
    current_user: AnalystUser,
    service: WazuhDep,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        return await service.get_tasks(limit=limit, offset=offset)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/dashboard")
async def dashboard(
    current_user: AnalystUser,
    service: WazuhDep,
    hours: int = Query(168, ge=1, le=2160),
):
    """Live Wazuh dashboard aggregation."""
    try:
        return await service.get_dashboard(hours=hours)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/attack-map")
async def attack_map(
    current_user: AnalystUser,
    service: WazuhDep,
    hours: int = Query(720, ge=1, le=2160),
    size: int = Query(200, ge=1, le=1000),
):
    """Extract attacker source IPs from Wazuh alerts with GeoIP if available."""
    try:
        return await service.get_attack_map(hours=hours, size=size)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/correlate-incidents")
async def correlate_incidents(
    current_user: AnalystUser,
    service: WazuhDep,
    hours: int = Query(168, ge=1, le=2160),
    min_cluster_size: int = Query(2, ge=1, le=100),
):
    """Auto-correlate Wazuh alerts into incidents by source IP, rule, agent, MITRE, and time-proximity."""
    try:
        incidents = await service.correlate_incidents(hours=hours, min_cluster_size=min_cluster_size)
        return {"incidents": incidents, "total": len(incidents)}
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/search")
async def global_search(
    current_user: AnalystUser,
    service: WazuhDep,
    q: str = Query(..., min_length=2),
    limit: int = Query(50, ge=1, le=200),
):
    """Global search across alerts, agents, vulnerabilities, and MITRE techniques."""
    try:
        return await service.global_search(query=q, limit=limit)
    except Exception as exc:
        return _wazuh_error(exc)


@router.get("/latest-alerts")
async def latest_alerts(
    current_user: AnalystUser,
    service: WazuhDep,
    size: int = Query(10, ge=1, le=100),
):
    """Get latest Wazuh alerts for live notifications."""
    try:
        alerts = await service.get_latest_alerts(size=size)
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as exc:
        return _wazuh_error(exc)
