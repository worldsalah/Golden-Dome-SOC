from datetime import datetime
from typing import Any

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


class FalsePositiveRuleAnalysis(BaseModel):
    rule_id: str
    detection_name: str
    alert_count: int
    real_incidents: int
    false_positive_count: int
    false_positive_rate: float | None
    repeated_alerts: int
    confidence: float
    suggestions: list[str]


class RuleOptimizerEntry(BaseModel):
    rule_id: str
    detection_name: str
    alert_count: int
    suggestion: str


class DuplicateRuleGroup(BaseModel):
    key: str
    type: str
    rule_ids: list[str]
    suggestion: str


class RuleOptimizerResponse(BaseModel):
    never_triggered: list[RuleOptimizerEntry]
    rarely_triggered: list[RuleOptimizerEntry]
    frequently_triggered: list[RuleOptimizerEntry]
    inefficient: list[RuleOptimizerEntry]
    duplicate_groups: list[DuplicateRuleGroup]
    total_rules: int
    data_source: str
    generated_at: datetime


class ReplayAlertResponse(BaseModel):
    alert_id: int
    original_event: dict[str, Any]
    current_rule: dict[str, Any] | None = None
    verdict: str
    match_count_24h: int
    last_trigger: datetime | None = None
    suggestions: list[str]
    data_source: str
    generated_at: datetime


class EvidenceEntry(BaseModel):
    id: int
    source: str
    type: str
    title: str
    timestamp: datetime | None = None
    snippet: str
    rule_id: str | None = None
    severity: int | None = None
    file_path: str | None = None
    raw: str | None = None


class EvidenceSearchResponse(BaseModel):
    evidence: list[EvidenceEntry]
    query: str | None = None
    source: str | None = None
    total: int
    data_source: str
    generated_at: datetime


class SocHealthComponents(BaseModel):
    detection_validation: float
    attack_coverage: float
    false_positive_control: float
    backlog: float
    platform_performance: float


class SocHealthScoreResponse(BaseModel):
    grade: str
    overall_score: float
    components: SocHealthComponents
    open_alerts: int
    open_incidents: int
    data_source: str
    generated_at: datetime


class DaemonHealth(BaseModel):
    name: str
    status: str


class DetectionPerformanceResponse(BaseModel):
    api_latency_ms: float
    indexer_latency_ms: float
    events_per_second: float | None = None
    events_dropped_per_hour: int | None = None
    drop_percentage: float | None = None
    alerts_per_hour: float | None = None
    alerts_written_24h: int | None = None
    indexer_alert_volume_24h: int | None = None
    daemon_health: list[DaemonHealth] = []
    manager_stats_raw: dict[str, Any] = {}
    data_source: str
    generated_at: datetime


class FalsePositiveAnalysisResponse(BaseModel):
    rules: list[FalsePositiveRuleAnalysis]
    total_rules_analyzed: int
    rules_with_disposition_data: int
    avg_false_positive_rate: float | None
    data_source: str
    generated_at: datetime
