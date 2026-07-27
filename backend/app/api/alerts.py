import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.api.deps import CurrentUser
from app.schemas.alert import AlertCreate, AlertListParams, AlertRead, AlertStatusUpdate
from app.security.jwt import get_current_user
from app.security.permissions import Role, require_min_role
from app.services.alert_enrichment import AlertEnrichmentService
from app.services.alert_service import AlertService
from app.services.wazuh_service import WazuhService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=dict)
async def list_alerts(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: int | None = Query(None, ge=1, le=15),
    status: str | None = Query(None),
    search: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    assigned_to_me: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    params = AlertListParams(
        page=page,
        limit=limit,
        severity=severity,
        status=status,
        search=search,
        start_date=start_date,
        end_date=end_date,
        assigned_to_me=assigned_to_me,
    )
    service = AlertService(db)
    alerts, total = await service.get_alerts(params)
    return {
        "data": [AlertRead.model_validate(a) for a in alerts],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(
    alert_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    current_user: Annotated[dict, Depends(require_min_role(Role.SOC_ANALYST))],
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.create_alert(alert_in)
    return alert


@router.patch("/{alert_id}/status", response_model=AlertRead)
async def update_alert_status(
    alert_id: int,
    update: AlertStatusUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.update_status(alert_id, update)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.post("/sync", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def sync_alerts_from_wazuh(
    current_user: Annotated[dict, Depends(require_min_role(Role.SOC_ANALYST))],
    size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Pull recent alerts from Wazuh/OpenSearch and persist metadata locally."""
    wazuh = WazuhService()
    raw_alerts = await wazuh.get_alerts(size=size)
    normalized = [await wazuh.normalize_alert(a) for a in raw_alerts]

    service = AlertService(db)
    created, skipped = await service.sync_alerts_from_wazuh(normalized)
    logger.info("Alert sync requested by %s: %d created, %d skipped", current_user.username, created)
    return {"created": created, "skipped": skipped, "total_processed": len(normalized)}


@router.post("/{alert_id}/enrich", response_model=dict)
async def enrich_alert(
    alert_id: int,
    current_user: CurrentUser,
    create_incident: bool = Query(False, description="Create incident if alert severity is critical"),
    db: AsyncSession = Depends(get_db),
):
    """Run the alert enrichment pipeline: MITRE, threat intelligence, AI analysis, and optional incident creation."""
    _ = current_user
    service = AlertEnrichmentService(db)
    try:
        result = await service.enrich(alert_id, create_incident=create_incident)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result
