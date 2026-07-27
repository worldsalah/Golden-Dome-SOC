from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    wazuh_alert_id: str
    title: str
    description: str | None = None
    severity: int = Field(default=1, ge=1, le=15)
    source_ip: str | None = None
    destination_ip: str | None = None
    rule_id: str | None = None
    mitre_technique: str | None = None
    status: str = "new"
    raw_log: str | None = None


class AlertCreate(AlertBase):
    asset_id: int | None = None
    assigned_user_id: int | None = None


class AlertStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(new|acknowledged|investigating|resolved|false_positive)$")
    assigned_user_id: int | None = None


class AlertRead(AlertBase):
    id: int
    asset_id: int | None = None
    assigned_user_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    severity: int | None = None
    status: str | None = None
    search: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    assigned_to_me: bool = False
