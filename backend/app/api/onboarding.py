"""Customer onboarding wizard API — guided deployment flow for new organizations."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, FirstBootOrSuperAdmin, SuperAdminUser
from app.config.security import hash_password
from app.database.models import Asset, AssetType, Connector, Organization, User
from app.services.connectors import ConnectorRegistry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status")
async def onboarding_status(db: DBDependency):
    """Return whether the platform needs first-boot setup."""
    from sqlalchemy import func, select
    count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    orgs = (await db.execute(select(func.count(Organization.id)))).scalar() or 0
    return {
        "needs_setup": count == 0 and orgs == 0,
        "users_count": count,
        "organizations_count": orgs,
    }


class OnboardingStep1(BaseModel):
    """Create organization."""
    org_name: str = Field(..., min_length=2, max_length=255)
    org_slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9-]+$")
    industry: str | None = None
    contact_email: str | None = None
    plan: str = "professional"


class OnboardingStep2(BaseModel):
    """Create admin user for the org."""
    admin_username: str = Field(..., min_length=3, max_length=64)
    admin_email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")
    admin_password: str = Field(..., min_length=8)


class OnboardingStep3(BaseModel):
    """Configure infrastructure connectors."""
    connectors: list[dict[str, Any]] = Field(default_factory=list)


class OnboardingStep4(BaseModel):
    """Add initial assets."""
    assets: list[dict[str, Any]] = Field(default_factory=list)


class OnboardingResult(BaseModel):
    organization_id: int
    admin_user_id: int
    connectors_created: int
    assets_created: int
    next_steps: list[str]


@router.post("/wizard", response_model=OnboardingResult, status_code=status.HTTP_201_CREATED)
async def run_onboarding_wizard(
    payload: dict[str, Any],
    current_user: FirstBootOrSuperAdmin,
    db: DBDependency,
):
    """Run the full onboarding wizard in one call.

    Expected payload:
    {
        "org": {"name": "...", "slug": "...", "industry": "...", ...},
        "admin": {"username": "...", "email": "...", "password": "..."},
        "connectors": [{"name": "...", "connector_type": "...", "config": {...}}, ...],
        "assets": [{"hostname": "...", "ip_address": "...", "type": "..."}, ...]
    }
    """
    # Step 1: Create organization
    org_data = payload.get("org", {})
    if not org_data.get("name") or not org_data.get("slug"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="org.name and org.slug are required")

    existing = await db.execute(select(Organization).where(Organization.slug == org_data["slug"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already exists")

    org = Organization(
        name=org_data["name"],
        slug=org_data["slug"],
        industry=org_data.get("industry"),
        contact_email=org_data.get("contact_email"),
        plan=org_data.get("plan", "professional"),
    )
    db.add(org)
    await db.flush()

    # Step 2: Create admin user
    admin_data = payload.get("admin", {})
    if not admin_data.get("username") or not admin_data.get("email") or not admin_data.get("password"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="admin.username, admin.email, and admin.password are required")

    admin_user = User(
        username=admin_data["username"],
        email=admin_data["email"],
        hashed_password=hash_password(admin_data["password"]),
        role="super_admin",

        organization_id=org.id,
    )
    db.add(admin_user)

    # Step 3: Create connectors
    connectors_created = 0
    for conn_data in payload.get("connectors", []):
        connector_type = conn_data.get("connector_type")
        manifest_cls = ConnectorRegistry.get(connector_type)
        if not manifest_cls:
            continue
        connector = Connector(
            tenant_id=org.id,
            name=conn_data.get("name", connector_type),
            connector_type=connector_type,
            category=manifest_cls.manifest.category,
            config=json.dumps(conn_data.get("config", {})),
            credentials=json.dumps(conn_data.get("credentials", {})) if conn_data.get("credentials") else None,
            status="configured",
        )
        db.add(connector)
        connectors_created += 1

    # Step 4: Create assets
    assets_created = 0
    for asset_data in payload.get("assets", []):
        asset = Asset(
            tenant_id=org.id,
            hostname=asset_data.get("hostname", "unknown"),
            ip_address=asset_data.get("ip_address"),
            type=asset_data.get("type", AssetType.UNKNOWN.value),
            operating_system=asset_data.get("operating_system"),
            criticality=asset_data.get("criticality", 50),
        )
        db.add(asset)
        assets_created += 1

    await db.commit()

    next_steps = [
        "Verify admin user can login",
        "Test connector connections",
        "Run asset discovery scan",
        "Configure detection rules",
        "Set up alert notifications",
    ]

    logger.info("Onboarding complete for org %s (id=%d)", org.name, org.id)

    return OnboardingResult(
        organization_id=org.id,
        admin_user_id=admin_user.id,
        connectors_created=connectors_created,
        assets_created=assets_created,
        next_steps=next_steps,
    )


@router.get("/wizard/steps")
async def get_onboarding_steps(current_user: SuperAdminUser):
    """Return the onboarding wizard steps and available options."""
    return {
        "steps": [
            {
                "id": 1,
                "title": "Create Organization",
                "description": "Set up the customer organization with name, industry, and plan",
                "fields": ["org_name", "org_slug", "industry", "contact_email", "plan"],
            },
            {
                "id": 2,
                "title": "Create Admin User",
                "description": "Create the first admin user for this organization",
                "fields": ["admin_username", "admin_email", "admin_password"],
            },
            {
                "id": 3,
                "title": "Connect Infrastructure",
                "description": "Configure security, cloud, and ticketing connectors",
                "fields": ["connectors"],
                "available_connectors": ConnectorRegistry.list_all(),
            },
            {
                "id": 4,
                "title": "Add Assets",
                "description": "Register initial infrastructure assets for monitoring",
                "fields": ["assets"],
            },
            {
                "id": 5,
                "title": "Run Discovery",
                "description": "Start monitoring and verify everything is working",
                "fields": [],
            },
        ]
    }
