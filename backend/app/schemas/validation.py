from datetime import datetime

from pydantic import BaseModel, Field


class DetectionValidationEntry(BaseModel):
    rule_id: str
    detection_name: str
    mitre_technique: str | None = None
    severity: int
    alert_count: int
    last_trigger: datetime | None = None
    status: str  # enabled | disabled (from Wazuh rule status)
    validation_status: str  # validated | pending | stale | no_data
    coverage_percentage: float
    false_positive_rate: float | None = None  # None = insufficient local disposition data
    false_positive_sample_size: int = 0
    detection_confidence: float
    groups: list[str] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    total_detections: int
    validated: int
    pending: int
    no_data: int
    avg_false_positive_rate: float | None
    avg_confidence: float
    total_alerts_observed: int
    data_source: str
    generated_at: datetime


class ValidationCenterResponse(BaseModel):
    summary: ValidationSummary
    detections: list[DetectionValidationEntry]


class AttackCoverageTechnique(BaseModel):
    technique_id: str
    name: str
    tactic: str
    state: str  # validated | implemented | failed | missing_detection
    mapped_rule_count: int
    mapped_rule_ids: list[str]
    last_tested: datetime | None = None
    coverage_percentage: float


class AttackCoverageResponse(BaseModel):
    techniques: list[AttackCoverageTechnique]
    tactic_summary: dict[str, dict[str, int]]
    total_techniques: int
    validated_techniques: int
    overall_coverage_percentage: float
    data_source: str
    generated_at: datetime
