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


def _wazuh_error(exc: Exception):
    logger.exception("Wazuh API call failed")
    detail = str(exc)
    if isinstance(exc, WazuhServiceError):
        detail = "Wazuh API unreachable or authentication failed"
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


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
        _wazuh_error(exc)


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
        _wazuh_error(exc)


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
        _wazuh_error(exc)


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
        _wazuh_error(exc)


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
        _wazuh_error(exc)
