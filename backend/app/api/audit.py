"""Audit log API — query user actions, login history, and security events."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, SecurityManagerUser
from app.database.models import AuditLog, UserSession
from app.security.tenant import tenant_filter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get("/logs")
async def list_audit_logs(
    current_user: SecurityManagerUser,
    db: DBDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    action: str | None = None,
    user_id: int | None = None,
):
    """List audit logs scoped to the current user's tenant."""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    # Tenant isolation
    if current_user.organization_id is not None:
        query = query.where(AuditLog.tenant_id == current_user.organization_id)
        count_query = count_query.where(AuditLog.tenant_id == current_user.organization_id)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    total = await db.scalar(count_query) or 0
    query = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "meta": {"total": total, "page": page, "limit": limit},
    }


@router.get("/sessions")
async def list_sessions(
    current_user: SecurityManagerUser,
    db: DBDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    """List active user sessions scoped to the current user's tenant."""
    query = select(UserSession).where(UserSession.is_active == True)
    count_query = select(func.count(UserSession.id)).where(UserSession.is_active == True)

    if current_user.organization_id is not None:
        query = query.where(UserSession.tenant_id == current_user.organization_id)
        count_query = count_query.where(UserSession.tenant_id == current_user.organization_id)

    total = await db.scalar(count_query) or 0
    query = query.order_by(desc(UserSession.created_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "data": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
            }
            for s in sessions
        ],
        "meta": {"total": total, "page": page, "limit": limit},
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: int,
    current_user: SecurityManagerUser,
    db: DBDependency,
):
    """Revoke a user session (force logout)."""
    session = await db.get(UserSession, session_id)
    if not session:
        raise status.HTTP_404_NOT_FOUND

    if current_user.organization_id is not None and session.tenant_id != current_user.organization_id:
        raise status.HTTP_403_FORBIDDEN

    session.is_active = False
    session.revoked_at = __import__("app.utils.datetime_helper", fromlist=["utc_now"]).utc_now()
    await db.commit()
