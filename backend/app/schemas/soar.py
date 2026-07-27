import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlaybookAction(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class PlaybookNode(BaseModel):
    id: str
    type: str
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    next_nodes: list[str] = Field(default_factory=list)
    condition: str | None = None


class PlaybookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger: str = Field(default="manual")
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active")
    category: str = Field(default="response")
    version: str = Field(default="1.0.0")
    tags: str | None = None
    is_builtin: bool = Field(default=False)
    actions: list[PlaybookAction] = Field(default_factory=list)
    nodes: list[PlaybookNode] = Field(default_factory=list)

    @field_validator("actions", mode="before")
    @classmethod
    def parse_actions(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value or "[]")
        return value

    @field_validator("nodes", mode="before")
    @classmethod
    def parse_nodes(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value or "[]")
        return value

    @field_validator("trigger_config", mode="before")
    @classmethod
    def parse_trigger_config(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value or "{}")
        return value


class PlaybookCreate(PlaybookBase):
    pass


class PlaybookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    trigger: str | None = None
    trigger_config: dict[str, Any] | None = None
    status: str | None = None
    category: str | None = None
    version: str | None = None
    tags: str | None = None
    actions: list[PlaybookAction] | None = None
    nodes: list[PlaybookNode] | None = None


class PlaybookRead(PlaybookBase):
    id: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlaybookRunRequest(BaseModel):
    input_data: dict[str, Any] = Field(default_factory=dict)
    trigger_event: str | None = None


class PlaybookExecutionRead(BaseModel):
    id: int
    playbook_id: int
    status: str
    triggered_by: str | None
    trigger_event: str | None
    input_data: str | None
    output_log: str | None
    context: str | None
    current_node_id: str | None
    node_states: str | None
    results: str | None
    logs: str | None
    approval_status: str | None
    requires_approval: bool
    started_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowApprovalCreate(BaseModel):
    execution_id: int
    node_id: str | None = None
    action_summary: str
    risk_level: str = "medium"
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowApprovalRead(BaseModel):
    id: int
    execution_id: int
    playbook_id: int | None
    node_id: str | None
    action_summary: str | None
    risk_level: str
    status: str
    requested_by: str | None
    approved_by: str | None
    approved_at: datetime | None
    details: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowApprovalDecision(BaseModel):
    decision: str  # approved or denied
    user: str | None = None


class WorkflowTimelineEventRead(BaseModel):
    id: int
    execution_id: int
    node_id: str | None
    event_type: str
    message: str | None
    actor: str | None
    details: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowEvidenceRead(BaseModel):
    id: int
    execution_id: int
    node_id: str | None
    evidence_type: str
    source: str | None
    content: str | None
    file_path: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowActionLogRead(BaseModel):
    id: int
    execution_id: int
    node_id: str | None
    action_type: str
    status: str
    input_data: str | None
    output_data: str | None
    duration_ms: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOARStatistics(BaseModel):
    total_playbooks: int
    active_playbooks: int
    total_executions: int
    completed_executions: int
    failed_executions: int
    pending_approvals: int
    avg_execution_time_ms: float
    most_executed_playbooks: list[dict[str, Any]]
    execution_status_counts: dict[str, int]
