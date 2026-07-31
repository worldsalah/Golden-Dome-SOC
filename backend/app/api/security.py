"""Commercial security API — rate limiting, API keys, security headers, and security testing."""

import hashlib
import json
import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, SuperAdminUser, SecurityManagerUser
from app.database.models import ApiKey, AuditLog
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["Commercial Security"])


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=128)
    scopes: list[str] = Field(default_factory=list)


@router.get("/headers")
async def get_security_headers(current_user: SecurityManagerUser):
    """Report current security header configuration."""
    return {
        "headers": {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        },
        "cors": {
            "allow_credentials": True,
            "allowed_methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        },
        "rate_limiting": {
            "ai_endpoints": "60 requests per minute per user",
            "login_attempts": "5 attempts per 15 minutes",
            "api_keys": "Configurable per key",
        },
    }


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    """Create a new API key for programmatic access (persisted to database)."""
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    api_key = ApiKey(
        tenant_id=current_user.organization_id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=json.dumps(payload.scopes),
        is_active=True,
        created_by=current_user.id,
    )
    db.add(api_key)

    audit = AuditLog(
        tenant_id=current_user.organization_id,
        user_id=current_user.id,
        username=current_user.username,
        action="api_key_created",
        resource_type="api_key",
        resource_id=key_prefix,
        status="success",
    )
    db.add(audit)
    await db.commit()

    return {
        "key": raw_key,
        "key_prefix": key_prefix,
        "name": payload.name,
        "scopes": payload.scopes,
        "message": "Store this key securely — it will not be shown again",
    }


@router.get("/api-keys")
async def list_api_keys(
    current_user: SuperAdminUser,
    db: DBDependency,
):
    """List all API keys (masked)."""
    query = select(ApiKey).order_by(desc(ApiKey.created_at))
    if current_user.organization_id is not None:
        query = query.where(ApiKey.tenant_id == current_user.organization_id)
    result = await db.execute(query)
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "key_prefix": k.key_prefix,
            "name": k.name,
            "scopes": json.loads(k.scopes) if k.scopes else [],
            "is_active": k.is_active,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_prefix}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_prefix: str,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    """Revoke an API key."""
    query = select(ApiKey).where(ApiKey.key_prefix == key_prefix)
    if current_user.organization_id is not None:
        query = query.where(ApiKey.tenant_id == current_user.organization_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    api_key.revoked_at = utc_now()
    audit = AuditLog(
        tenant_id=current_user.organization_id,
        user_id=current_user.id,
        username=current_user.username,
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=key_prefix,
        status="success",
    )
    db.add(audit)
    await db.commit()


@router.get("/audit-summary")
async def get_security_audit_summary(
    current_user: SecurityManagerUser,
    db: DBDependency,
):
    """Get a summary of security-relevant audit events."""
    query = select(
        AuditLog.action,
        func.count(AuditLog.id).label("count"),
    ).group_by(AuditLog.action)

    if current_user.organization_id is not None:
        query = query.where(AuditLog.tenant_id == current_user.organization_id)

    result = await db.execute(query)
    summary = {row.action: row.count for row in result}

    failed_logins = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == "login_failed",
            AuditLog.status == "failed",
        )
    )

    active_keys_query = select(func.count(ApiKey.id)).where(ApiKey.is_active == True)
    if current_user.organization_id is not None:
        active_keys_query = active_keys_query.where(ApiKey.tenant_id == current_user.organization_id)
    active_keys = await db.scalar(active_keys_query)

    return {
        "event_counts": summary,
        "failed_logins": failed_logins or 0,
        "active_api_keys": active_keys or 0,
    }
