"""Asset discovery API — network scanning and topology mapping."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, ITAdminUser, AnalystUser
from app.database.models import Asset
from app.services.discovery import AssetDiscoveryEngine
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery", tags=["Asset Discovery"])


class DiscoveryRequest(BaseModel):
    cidr: str = Field(..., description="Network range in CIDR notation, e.g. 192.168.1.0/24")
    scan_type: str = Field(default="quick", pattern="^(quick|deep)$")


@router.post("/scan")
async def run_discovery(
    payload: DiscoveryRequest,
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Run a network discovery scan."""
    engine = AssetDiscoveryEngine(db, tenant_id=current_user.organization_id)
    result = await engine.discover_network(payload.cidr, payload.scan_type)
    if result.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result["error"])
    return result


@router.get("/topology")
async def get_topology(
    current_user: AnalystUser,
    db: DBDependency,
):
    """Get the network topology map."""
    engine = AssetDiscoveryEngine(db, tenant_id=current_user.organization_id)
    return await engine.get_topology()


@router.get("/assets")
async def list_discovered_assets(
    current_user: AnalystUser,
    db: DBDependency,
):
    """List all discovered assets for the current tenant."""
    query = select(Asset)
    if current_user.organization_id is not None:
        query = query.where(Asset.tenant_id == current_user.organization_id)
    result = await db.execute(query)
    assets = result.scalars().all()
    return [
        {
            "id": a.id,
            "hostname": a.hostname,
            "ip_address": a.ip_address,
            "type": a.type,
            "operating_system": a.operating_system,
            "criticality": a.criticality,
            "risk_score": a.risk_score,
            "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            "wazuh_agent_id": a.wazuh_agent_id,
        }
        for a in assets
    ]
