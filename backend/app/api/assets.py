import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, AnalystUser, CurrentUser
from app.database.database import get_db
from app.database.models import Asset
from app.schemas.asset import AssetCreate, AssetDetailsRead, AssetRead, AssetUpdate
from app.security.tenant import ensure_tenant_access, tenant_filter
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=dict)
async def list_assets(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(Asset)
    filt = tenant_filter(Asset, current_user.organization_id)
    if filt is not None:
        query = query.where(filt)

    total_result = await db.execute(select(Asset))
    # Count only tenant-scoped assets for the response total
    total = len([a for a in total_result.scalars().all() if filt is None or a.tenant_id == current_user.organization_id])

    result = await db.execute(
        query
        .offset((page - 1) * limit)
        .limit(limit)
    )
    assets = result.scalars().all()
    return {
        "data": [AssetRead.model_validate(a) for a in assets],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(
    asset_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await ensure_tenant_access(asset.tenant_id, current_user.organization_id)
    return asset


@router.get("/{asset_id}/details", response_model=AssetDetailsRead)
async def get_asset_details(
    asset_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await ensure_tenant_access(asset.tenant_id, current_user.organization_id)
    await db.refresh(asset, ["vulnerabilities", "alerts"])
    return {
        "asset": asset,
        "vulnerabilities": asset.vulnerabilities,
        "alerts": asset.alerts,
    }


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    asset = Asset(**payload.model_dump())
    asset.tenant_id = current_user.organization_id
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    logger.info("Asset created: %s (tenant=%s) by user %s", asset.hostname, asset.tenant_id, current_user.username)
    return asset


@router.patch("/{asset_id}", response_model=AssetRead)
async def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await ensure_tenant_access(asset.tenant_id, current_user.organization_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    logger.info("Asset updated: %s by user %s", asset.hostname, current_user.username)
    return asset


@router.post("/{asset_id}/calculate-risk", response_model=dict)
async def calculate_asset_risk(
    asset_id: int,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await ensure_tenant_access(asset.tenant_id, current_user.organization_id)
    service = RiskService(db)
    try:
        score = await service.calculate_asset_risk(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"asset_id": asset_id, "risk_score": score}


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await ensure_tenant_access(asset.tenant_id, current_user.organization_id)
    await db.delete(asset)
    await db.commit()
    logger.info("Asset deleted: %s by user %s", asset.hostname, current_user.username)
    return None
