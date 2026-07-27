from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlertAnalysisRequest(BaseModel):
    alert_id: int = Field(..., description="ID of the alert to analyze")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000, description="Analyst question")
    alert_id: int | None = Field(None, description="Optional alert context")


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    answer: str
    source: str = "ollama"


class AlertAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_id: int | None = None
    executive_summary: str
    technical_explanation: dict[str, Any]
    mitre_mapping: dict[str, Any]
    risk_assessment: dict[str, Any]
    risk_score: int
    risk_classification: str
    investigation_steps: list[str]
    recommended_response: dict[str, Any]
    analyst_notes: str
    llm_source: str


class IncidentInvestigationRequest(BaseModel):
    incident_id: int


class IncidentInvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    incident_id: int | None = None
    title: str = ""
    severity: str = ""
    summary: str = ""
    timeline: list[Any] = []
    affected_assets: list[str] = []
    indicators_of_compromise: list[str] = []
    mitre_mapping: list[Any] | dict[str, Any] = []
    investigation_performed: list[str] = []
    recommended_remediation: dict[str, Any] = {}
    lessons_learned: list[str] = []
    risk_score: int = 0
    risk_reason: str = ""
    llm_source: str = "unknown"


class PlaybookGenerationRequest(BaseModel):
    alert_description: str = Field(..., min_length=5)
    mitre_technique: str | None = None
    severity: int = Field(default=5, ge=1, le=15)


class PlaybookGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    description: str = ""
    trigger: str = ""
    actions: list[dict[str, Any]]
    expected_outcome: str = ""
    automation_notes: str = ""
    llm_source: str = "unknown"


class ThreatHuntRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=4000)


class ThreatHuntResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str
    hypotheses: list[str] = []
    recommended_queries: list[str] = []
    indicators_to_hunt: list[str] = []
    mitre_techniques: list[str] = []
    priority: str = "P4"
    confidence: int = 0
    rag_sources: list[str] = []
    llm_source: str = "unknown"


class FeedbackRequest(BaseModel):
    analysis_id: int
    helpful: bool = False
    incorrect: bool = False
    comment: str | None = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    feedback_id: int
    status: str


class FeedbackListResponse(BaseModel):
    data: list[dict[str, Any]]


class AnomalyRecordItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    feature_type: str
    record_id: str
    anomaly_score: int
    features: dict[str, Any] | str | None = None
    created_at: str | None = None


class AnomalyDetectionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    auth: list[AnomalyRecordItem] = []
    traffic: list[AnomalyRecordItem] = []


class DailyReportResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = "Daily SOC Report"
    date: str = ""
    executive_summary: str = ""
    key_metrics: dict[str, Any] = {}
    top_threats: list[Any] = []
    recommendations: list[str] = []
    llm_source: str = "unknown"


class HistoryResponse(BaseModel):
    data: list[dict[str, Any]]


class QueryLogResponse(BaseModel):
    data: list[dict[str, Any]]
