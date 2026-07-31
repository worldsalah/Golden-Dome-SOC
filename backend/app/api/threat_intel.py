import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnalystUser, DBDependency
from app.security.permissions import Role, require_min_role
from app.security.tenant import tenant_filter
from app.database.models import IocDatabase, ThreatIntelligence
from app.schemas.threat_intel import ThreatIntelRequest, ThreatIntelResponse
from app.services.ai_engine.threat_intel import ThreatIntelEnricher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threat-intelligence", tags=["Threat Intelligence"])


def get_enricher(db: DBDependency) -> ThreatIntelEnricher:
    return ThreatIntelEnricher(db)


EnricherDependency = Annotated[ThreatIntelEnricher, Depends(get_enricher)]


@router.get("/{indicator}", response_model=ThreatIntelResponse)
async def lookup_indicator(
    indicator: str,
    current_user: AnalystUser,
    type: str | None = Query(None, description="Optional IOC type: ip, domain, hash, url"),
    enricher: ThreatIntelEnricher = Depends(get_enricher),
):
    try:
        result = await enricher.enrich(indicator, type_hint=type)
        await enricher.close()
        return ThreatIntelResponse(**result)
    except Exception as exc:
        logger.exception("Threat intelligence enrichment failed for %s", indicator)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {exc}",
        )


@router.post("/enrich", response_model=ThreatIntelResponse)
async def enrich_indicator(
    payload: ThreatIntelRequest,
    current_user: AnalystUser,
    enricher: EnricherDependency,
):
    try:
        result = await enricher.enrich(payload.indicator, type_hint=payload.type)
        await enricher.close()
        return ThreatIntelResponse(**result)
    except Exception as exc:
        logger.exception("Threat intelligence enrichment failed for %s", payload.indicator)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {exc}",
        )


from app.database.database import get_db


@router.get("/", response_model=dict)
async def list_indicators(
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 20,
):
    query = select(IocDatabase)
    filt = tenant_filter(IocDatabase, current_user.organization_id)
    if filt is not None:
        query = query.where(filt)
    total = len((await db.execute(query)).scalars().all())
    result = await db.execute(
        query
        .order_by(desc(IocDatabase.last_seen))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "data": [
            {
                "id": r.id,
                "value": r.value,
                "type": r.type,
                "category": r.category,
                "confidence": r.confidence,
                "first_seen": r.first_seen.isoformat() if r.first_seen else None,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                "sources": r.sources,
            }
            for r in rows
        ],
        "meta": {"page": page, "limit": limit, "total": total},
    }
