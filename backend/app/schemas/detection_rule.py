from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DetectionRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    severity: int = Field(default=5, ge=1, le=15)
    category: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    logic: str = Field(..., min_length=1)
    mitre_attack_id: str | None = None
    status: str = Field(default="active", pattern=r"^(active|disabled|draft|archived)$")


class DetectionRuleCreate(DetectionRuleBase):
    pass


class DetectionRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: int | None = Field(default=None, ge=1, le=15)
    category: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, min_length=1)
    logic: str | None = Field(default=None, min_length=1)
    mitre_attack_id: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|disabled|draft|archived)$")


class DetectionRuleRead(DetectionRuleBase):
    id: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionRuleTestRequest(BaseModel):
    event: dict = Field(default_factory=dict, description="Sample log event object to test the rule against")


class DetectionRuleTestResult(BaseModel):
    matched: bool
    reason: str | None = None
    extracted_fields: dict = Field(default_factory=dict)


class DetectionRuleScenario(BaseModel):
    name: str
    event: dict = Field(default_factory=dict)
    expected_match: bool = False


class DetectionRuleScenarioRequest(BaseModel):
    scenarios: list[DetectionRuleScenario]


class DetectionRuleScenarioEvaluation(BaseModel):
    total_scenarios: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    recommendation: str
    results: list[dict] = Field(default_factory=list)
