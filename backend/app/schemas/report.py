from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content: str | None = None
    report_type: str = Field(default="security")


class ReportCreate(ReportBase):
    pass


class ReportRead(ReportBase):
    id: int
    created_by_id: int | None = None
    file_path: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentReportRequest(BaseModel):
    incident_id: int = Field(..., description="Incident ID to generate the report for")
