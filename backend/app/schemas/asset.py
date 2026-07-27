from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=128)
    ip_address: str | None = None
    type: str = Field(default="unknown")
    operating_system: str | None = None
    criticality: int = Field(default=50, ge=0, le=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    last_seen: datetime | None = None
    wazuh_agent_id: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    type: str | None = None
    operating_system: str | None = None
    criticality: int | None = Field(default=None, ge=0, le=100)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    last_seen: datetime | None = None
    wazuh_agent_id: str | None = None


class AssetRead(AssetBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetVulnerabilityRead(BaseModel):
    id: int
    cve: str
    severity: str
    cvss_score: int | None
    description: str | None
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetAlertSummary(BaseModel):
    id: int
    title: str
    severity: int
    status: str
    mitre_technique: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetDetailsRead(BaseModel):
    asset: AssetRead
    vulnerabilities: list[AssetVulnerabilityRead]
    alerts: list[AssetAlertSummary]
