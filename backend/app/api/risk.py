import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnalystUser, DBDependency
from app.database.database import get_db
from app.database.models import Alert, Asset, Incident, RiskScore
from app.schemas.risk import RiskScoreResponse
from app.services.ai_engine.risk_scorer import RiskScorer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["Risk Center"])


def get_risk_service(db: DBDependency) -> RiskScorer:
    return RiskScorer(db)


RiskService = Annotated[RiskScorer, Depends(get_risk_service)]


@router.get("/asset/{asset_id}", response_model=RiskScoreResponse)
async def get_asset_risk(
    asset_id: int,
    current_user: AnalystUser,
    service: RiskService,
):
    asset = await service.db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    score, reason = await service.calculate_asset_risk(asset)
    await service.store_risk_score("asset", asset.id, score, reason)
    return RiskScoreResponse(
        target_type="asset",
        target_id=asset.id,
        score=score,
        classification=service.classification(score),
        reason=reason,
    )


@router.post("/asset/{asset_id}/recalculate", response_model=RiskScoreResponse)
async def recalculate_asset_risk(
    asset_id: int,
    current_user: AnalystUser,
    service: RiskService,
):
    asset = await service.db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    score, reason = await service.calculate_asset_risk(asset)
    asset.risk_score = score
    await service.db.commit()
    await service.store_risk_score("asset", asset.id, score, reason)
    return RiskScoreResponse(
        target_type="asset",
        target_id=asset.id,
        score=score,
        classification=service.classification(score),
        reason=reason,
    )


@router.get("/alert/{alert_id}", response_model=RiskScoreResponse)
async def get_alert_risk(
    alert_id: int,
    current_user: AnalystUser,
    service: RiskService,
):
    alert = await service.db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    score, reason = await service.calculate_alert_risk(alert)
    await service.store_risk_score("alert", alert.id, score, reason)
    return RiskScoreResponse(
        target_type="alert",
        target_id=alert.id,
        score=score,
        classification=service.classification(score),
        reason=reason,
    )


@router.get("/incident/{incident_id}", response_model=RiskScoreResponse)
async def get_incident_risk(
    incident_id: int,
    current_user: AnalystUser,
    service: RiskService,
):
    incident = await service.db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    score, reason = await service.calculate_incident_risk(incident)
    await service.store_risk_score("incident", incident.id, score, reason)
    return RiskScoreResponse(
        target_type="incident",
        target_id=incident.id,
        score=score,
        classification=service.classification(score),
        reason=reason,
    )


@router.get("/top-assets")
async def top_risky_assets(
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    service = RiskScorer(db)
    assets = await service.get_top_risky_assets(limit)
    return {
        "data": [
            {"id": a.id, "hostname": a.hostname, "risk_score": a.risk_score, "criticality": a.criticality}
            for a in assets
        ]
    }
