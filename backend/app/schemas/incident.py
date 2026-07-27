from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    severity: str = Field(default="medium")
    status: str = Field(default="open")
    description: str | None = None


class IncidentCreate(IncidentBase):
    assigned_user_id: int | None = None
    alert_ids: list[int] = []


class IncidentUpdate(BaseModel):
    name: str | None = None
    severity: str | None = None
    status: str | None = None
    description: str | None = None
    assigned_user_id: int | None = None
    resolved_at: datetime | None = None


class AlertSummary(BaseModel):
    id: int
    title: str
    severity: int
    status: str
    mitre_technique: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentTimelineRead(BaseModel):
    id: int
    action: str
    note: str | None = None
    actor_id: int | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentRead(IncidentBase):
    id: int
    assigned_user_id: int | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    timeline: list[IncidentTimelineRead] = []
    alerts: list[AlertSummary] = []

    model_config = ConfigDict(from_attributes=True)


class TimelineNoteCreate(BaseModel):
    note: str = Field(..., min_length=1)
