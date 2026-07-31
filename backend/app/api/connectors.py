"""Connector management API — list, configure, test, and manage integrations."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, AnalystUser, ITAdminUser
from app.database.models import Connector, ConnectorLog
from app.security.tenant import tenant_filter
from app.services.connectors import ConnectorRegistry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connectors", tags=["Connectors"])


@router.get("/catalog")
async def list_connector_catalog(current_user: AnalystUser):
    """List all available connector types that can be installed."""
    return ConnectorRegistry.list_all()


@router.get("/catalog/{category}")
async def list_connectors_by_category(category: str, current_user: AnalystUser):
    """List connectors by category (security, cloud, ticketing)."""
    return ConnectorRegistry.list_by_category(category)


@router.get("")
async def list_connectors(
    current_user: AnalystUser,
    db: DBDependency,
):
    """List configured connectors for the current tenant."""
    query = select(Connector)
    filt = tenant_filter(Connector, current_user.organization_id)
    if filt is not None:
        query = query.where(filt)
    query = query.order_by(desc(Connector.created_at))
    result = await db.execute(query)
    connectors = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "connector_type": c.connector_type,
            "category": c.category,
            "status": c.status,
            "health_status": c.health_status,
            "last_connected": c.last_connected.isoformat() if c.last_connected else None,
            "last_sync": c.last_sync.isoformat() if c.last_sync else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in connectors
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connector(
    payload: dict[str, Any],
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Create and configure a new connector."""
    connector_type = payload.get("connector_type")
    name = payload.get("name")
    if not connector_type or not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and connector_type are required")

    manifest = ConnectorRegistry.get(connector_type)
    if not manifest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown connector type: {connector_type}")

    config = payload.get("config", {})
    credentials = payload.get("credentials", {})

    connector = Connector(
        tenant_id=current_user.organization_id,
        name=name,
        connector_type=connector_type,
        category=manifest.manifest.category,
        config=json.dumps(config),
        credentials=json.dumps(credentials) if credentials else None,
        status="configured",
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    logger.info("Created connector %s (%s) for tenant %s", name, connector_type, current_user.organization_id)
    return {"id": connector.id, "name": connector.name, "connector_type": connector.connector_type, "status": connector.status}


@router.post("/{connector_id}/test")
async def test_connector(
    connector_id: int,
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Test a connector's connection."""
    connector = await db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    from app.security.tenant import ensure_tenant_access
    await ensure_tenant_access(connector.tenant_id, current_user.organization_id)

    connector_class = ConnectorRegistry.get(connector.connector_type)
    if not connector_class:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connector type not available")

    config = json.loads(connector.config) if connector.config else {}
    creds = json.loads(connector.credentials) if connector.credentials else {}
    config.update(creds)

    instance = connector_class(config=config)
    result = await instance.test_connection()

    connector.health_status = "healthy" if result.get("healthy") else "unhealthy"
    connector.last_connected = __import__("app.utils.datetime_helper", fromlist=["utc_now"]).utc_now() if result.get("healthy") else connector.last_connected

    log = ConnectorLog(
        connector_id=connector.id,
        level="info" if result.get("healthy") else "warning",
        message=f"Connection test: {result.get('status', 'unknown')}",
        details=json.dumps(result),
    )
    db.add(log)
    await db.commit()

    return result


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: int,
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Delete a connector."""
    connector = await db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    from app.security.tenant import ensure_tenant_access
    await ensure_tenant_access(connector.tenant_id, current_user.organization_id)

    await db.delete(connector)
    await db.commit()


@router.get("/{connector_id}/logs")
async def list_connector_logs(
    connector_id: int,
    current_user: AnalystUser,
    db: DBDependency,
    limit: int = 50,
):
    """List logs for a connector."""
    connector = await db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    from app.security.tenant import ensure_tenant_access
    await ensure_tenant_access(connector.tenant_id, current_user.organization_id)

    result = await db.execute(
        select(ConnectorLog)
        .where(ConnectorLog.connector_id == connector_id)
        .order_by(desc(ConnectorLog.created_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "level": l.level,
            "message": l.message,
            "details": l.details,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
