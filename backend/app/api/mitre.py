import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.database.database import get_db
from app.database.models import MITRETechnique
from app.schemas.mitre import MitreCoverage
from app.services.wazuh_service import WazuhService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mitre", tags=["MITRE ATT&CK"])


@router.get("/techniques", response_model=dict)
async def list_techniques(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return MITRE techniques from live Wazuh alerts (via OpenSearch) and any DB-registered techniques."""
    # Get live technique counts from Wazuh alerts
    try:
        service = WazuhService()
        matrix = await service.get_mitre_matrix(hours=720)
        live_techniques = {t["technique_id"]: t for t in matrix.get("matrix", {}).get("", [])}
        for tactic, techs in matrix.get("matrix", {}).items():
            for t in techs:
                live_techniques[t["technique_id"]] = t
    except Exception:
        logger.exception("Failed to fetch live MITRE techniques from Wazuh")
        live_techniques = {}

    # Get DB-registered techniques
    db_result = await db.execute(select(MITRETechnique))
    db_techniques = {t.technique_id: t for t in db_result.scalars().all()}

    techniques = []
    seen = set()

    for tid, live in live_techniques.items():
        techniques.append(
            {
                "technique_id": tid,
                "name": live.get("name", tid),
                "tactic": live.get("tactic", "Unknown"),
                "alert_count": live.get("alert_count", 0),
                "source": "wazuh",
            }
        )
        seen.add(tid)

    for tid, tech in db_techniques.items():
        if tid not in seen:
            techniques.append(
                {
                    "technique_id": tech.technique_id,
                    "name": tech.name,
                    "tactic": tech.tactic,
                    "alert_count": 0,
                    "source": "database",
                }
            )

    return {"data": techniques}


@router.get("/matrix", response_model=dict)
async def get_matrix(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return a live MITRE ATT&CK matrix generated from Wazuh alerts."""
    try:
        service = WazuhService()
        return await service.get_mitre_matrix()
    except Exception as exc:
        logger.exception("Live MITRE matrix failed")
        return {"wazuh_available": False, "error": str(exc)}


@router.get("/coverage", response_model=MitreCoverage)
async def get_coverage(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MITRETechnique))
    techniques = result.scalars().all()
    detected = [t for t in techniques if t.detection_status in ("detected", "partial")]
    tactics = {t.strip() for tech in techniques for t in tech.tactic.split(",")}
    coverage = (len(detected) / total * 100) if total else 0.0
    return MitreCoverage(
        total_techniques=total,
        detected_techniques=len(detected),
        coverage_percentage=round(coverage, 2),
        tactics=sorted(tactics),
    )
