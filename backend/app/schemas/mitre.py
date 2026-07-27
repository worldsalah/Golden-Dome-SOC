from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MitreCoverage(BaseModel):
    total_techniques: int
    detected_techniques: int
    coverage_percentage: float
    tactics: list[str]


class MITRETechniqueBase(BaseModel):
    technique_id: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=255)
    tactic: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    associated_rules: str | None = None
    detection_status: str = Field(default="planned", pattern=r"^(planned|partial|detected|not_applicable)$")
    alert_count: int = Field(default=0)


class MITRETechniqueCreate(MITRETechniqueBase):
    pass


class MitreTechniqueRead(MITRETechniqueBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
