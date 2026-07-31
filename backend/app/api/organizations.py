"""Organization management API — multi-tenant CRUD and user management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, SuperAdminUser, SecurityManagerUser
from app.database.models import (
    Alert,
    Asset,
    Incident,
    Organization,
    User,
    UserRole,
)
from app.config.security import hash_password
from app.security.permissions import Role
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    OrganizationWithStats,
)
from app.schemas.user import UserCreate, UserRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(
    current_user: SuperAdminUser,
    db: DBDependency,
):
    result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    existing = await db.execute(select(Organization).where(Organization.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already exists")

    org = Organization(**payload.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    logger.info("Created organization: %s (slug=%s)", org.name, org.slug)
    return org


@router.get("/{org_id}", response_model=OrganizationWithStats)
async def get_organization(
    org_id: int,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    user_count = await db.scalar(select(func.count(User.id)).where(User.organization_id == org_id))
    asset_count = await db.scalar(select(func.count(Asset.id)).where(Asset.tenant_id == org_id))
    alert_count = await db.scalar(select(func.count(Alert.id)).where(Alert.tenant_id == org_id))
    incident_count = await db.scalar(select(func.count(Incident.id)).where(Incident.tenant_id == org_id))

    return OrganizationWithStats(
        **{c.name: getattr(org, c.name) for c in org.__table__.columns},
        user_count=user_count or 0,
        asset_count=asset_count or 0,
        alert_count=alert_count or 0,
        incident_count=incident_count or 0,
    )


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(
    org_id: int,
    payload: OrganizationUpdate,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Soft-delete: deactivate instead of hard delete
    org.is_active = False
    await db.commit()


@router.get("/{org_id}/users", response_model=list[UserRead])
async def list_org_users(
    org_id: int,
    current_user: SecurityManagerUser,
    db: DBDependency,
):
    if current_user.role != Role.SUPER_ADMIN.value and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to list users for this organization",
        )
    result = await db.execute(
        select(User).where(User.organization_id == org_id).order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{org_id}/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_org_user(
    org_id: int,
    payload: UserCreate,
    current_user: SuperAdminUser,
    db: DBDependency,
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    existing = await db.execute(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    user_count = await db.scalar(select(func.count(User.id)).where(User.organization_id == org_id))
    if user_count and user_count >= org.max_users:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User limit reached for this organization")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        organization_id=org_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Created user %s for org %s", user.username, org.name)
    return user
