"""Tenant isolation utilities for multi-tenant access control."""

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.models import User
from app.security.jwt import get_current_user


async def get_tenant_id(
    current_user: User = Depends(get_current_user),
) -> int | None:
    """Extract tenant_id from the authenticated user.

    Super admins (platform owners) have tenant_id=None and can access all tenants.
    Regular users are scoped to their organization.
    """
    return current_user.organization_id


def get_tenant_from_request(request: Request) -> int | None:
    """Extract tenant_id from request state (set by TenantIsolationMiddleware).

    Returns None for super admins or unauthenticated requests.
    """
    return getattr(request.state, "tenant_id", None)


def tenant_filter(model: type, tenant_id: int | None):
    """Return a SQLAlchemy filter condition for tenant isolation.

    If tenant_id is None (super admin), no filter is applied.
    Otherwise, filter by tenant_id column.
    """
    if tenant_id is None:
        return None
    if hasattr(model, "tenant_id"):
        return model.tenant_id == tenant_id
    return None


async def ensure_tenant_access(
    resource_tenant_id: int | None,
    user_tenant_id: int | None,
) -> None:
    """Ensure the user has access to the given tenant resource.

    Raises 403 if the user's tenant_id doesn't match the resource's tenant_id
    (unless the user is a super admin with tenant_id=None).
    """
    if user_tenant_id is None:
        return  # Super admin, full access
    if resource_tenant_id is not None and resource_tenant_id != user_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to another organization",
        )
