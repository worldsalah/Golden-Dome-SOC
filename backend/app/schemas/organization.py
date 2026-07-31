from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    industry: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    plan: str = Field(default="professional")
    max_users: int = Field(default=50, ge=1)
    max_assets: int = Field(default=500, ge=1)


class OrganizationCreate(OrganizationBase):
    slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    plan: str | None = None
    max_users: int | None = None
    max_assets: int | None = None
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


class OrganizationRead(OrganizationBase):
    id: int
    slug: str
    is_active: bool
    settings: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationWithStats(OrganizationRead):
    user_count: int = 0
    asset_count: int = 0
    alert_count: int = 0
    incident_count: int = 0
