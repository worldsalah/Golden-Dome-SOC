import json
import logging
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Playbook,
    PlaybookExecution,
    WorkflowActionLog,
    WorkflowApproval,
    WorkflowEvidence,
    WorkflowTimelineEvent,
)
from app.services.soar.workflow_engine.actions import ActionRegistry
from app.services.soar.workflow_engine.engine import WorkflowEngine
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)

BUILTIN_PLAYBOOKS: list[dict[str, Any]] = [
    {
        "name": "Brute Force Response",
        "description": "Enrich, analyze, create an incident, and recommend blocking for brute force alerts.",
        "trigger": "alert",
        "category": "response",
        "version": "1.0.0",
        "tags": "brute_force,login,firewall",
        "is_builtin": True,
        "actions": [
            {"action": "enrich_ioc", "params": {"indicator": "{{input.ip}}"}},
            {"action": "ai_recommend", "params": {}},
            {"action": "create_incident", "params": {"name": "Brute Force Alert - {{input.ip}}", "severity": "high"}},
            {"action": "send_email", "params": {"subject": "Brute Force Response Triggered"}},
            {"action": "block_ip", "params": {"ip": "{{input.ip}}"}},
        ],
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Brute Force Alert", "config": {}, "next_nodes": ["enrich"]},
            {"id": "enrich", "type": "enrich_ioc", "name": "Enrich Source IP", "config": {"indicator": "{{input.ip}}"}, "next_nodes": ["ai_decision"]},
            {"id": "ai_decision", "type": "ai_decision", "name": "AI Recommendation", "config": {}, "next_nodes": ["create_incident"]},
            {"id": "create_incident", "type": "create_incident", "name": "Create Incident", "config": {"name": "Brute Force Alert - {{input.ip}}", "severity": "high"}, "next_nodes": ["notify"]},
            {"id": "notify", "type": "notify", "name": "Notify Analyst", "config": {"channel": "notification_center", "message": "Brute force incident created"}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Approve IP Block", "config": {"risk_level": "high", "summary": "Block source IP {{input.ip}}"}, "next_nodes": ["block_ip"]},
            {"id": "block_ip", "type": "block_ip", "name": "Block IP", "config": {"ip": "{{input.ip}}"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "Close", "config": {}},
        ],
    },
    {
        "name": "Malware Detection",
        "description": "Investigate a malware alert, collect evidence, isolate endpoint, and generate a report.",
        "trigger": "alert",
        "category": "response",
        "version": "1.0.0",
        "tags": "malware,endpoint,isolation",
        "is_builtin": True,
        "actions": [
            {"action": "enrich_alert", "params": {}},
            {"action": "create_incident", "params": {"name": "Malware Detection - {{input.host}}", "severity": "critical"}},
            {"action": "quarantine_host", "params": {"host": "{{input.host}}"}},
            {"action": "send_email", "params": {"subject": "Malware incident opened"}},
            {"action": "generate_report", "params": {"report_type": "technical"}},
        ],
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Malware Alert", "config": {}, "next_nodes": ["enrich_alert"]},
            {"id": "enrich_alert", "type": "enrich_alert", "name": "Enrich Alert", "config": {}, "next_nodes": ["create_incident"]},
            {"id": "create_incident", "type": "create_incident", "name": "Create Critical Incident", "config": {"name": "Malware Detection - {{input.host}}", "severity": "critical"}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Approve Isolation", "config": {"risk_level": "critical", "summary": "Isolate endpoint {{input.host}}"}, "next_nodes": ["isolate"]},
            {"id": "isolate", "type": "isolate_endpoint", "name": "Isolate Endpoint", "config": {"endpoint": "{{input.host}}"}, "next_nodes": ["notify"]},
            {"id": "notify", "type": "notify", "name": "Notify Analyst", "config": {"channel": "notification_center", "message": "Endpoint isolated"}, "next_nodes": ["report"]},
            {"id": "report", "type": "generate_report", "name": "Generate Report", "config": {"report_type": "technical"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "Close", "config": {}},
        ],
    },
    {
        "name": "Ransomware Response",
        "description": "Critical ransomware workflow: assess, create incident, collect evidence, and provide recovery checklist.",
        "trigger": "alert",
        "category": "response",
        "version": "1.0.0",
        "tags": "ransomware,critical,recovery",
        "is_builtin": True,
        "actions": [
            {"action": "enrich_alert", "params": {}},
            {"action": "create_incident", "params": {"name": "Ransomware Alert", "severity": "critical"}},
            {"action": "collect_evidence", "params": {"evidence_types": ["input", "context"]}},
            {"action": "send_email", "params": {"subject": "Critical ransomware incident", "recipient": "executives@goldendome.local"}},
            {"action": "generate_report", "params": {"report_type": "executive"}},
        ],
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Ransomware Detection", "config": {}, "next_nodes": ["enrich_alert"]},
            {"id": "enrich_alert", "type": "enrich_alert", "name": "AI Severity Assessment", "config": {}, "next_nodes": ["create_incident"]},
            {"id": "create_incident", "type": "create_incident", "name": "Create Critical Incident", "config": {"name": "Ransomware Alert", "severity": "critical"}, "next_nodes": ["evidence"]},
            {"id": "evidence", "type": "collect_evidence", "name": "Collect Evidence", "config": {"evidence_types": ["input", "context"]}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Executive Notification", "config": {"risk_level": "critical", "summary": "Notify executives of ransomware incident"}, "next_nodes": ["notify"]},
            {"id": "notify", "type": "notify", "name": "Executive Notification", "config": {"channel": "email", "message": "Critical ransomware incident {{execution.id}}"}, "next_nodes": ["report"]},
            {"id": "report", "type": "generate_report", "name": "Recovery Checklist", "config": {"report_type": "executive"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "Close", "config": {}},
        ],
    },
    {
        "name": "Suspicious PowerShell",
        "description": "Analyze suspicious PowerShell commands, map MITRE techniques, and create incident.",
        "trigger": "alert",
        "category": "investigation",
        "version": "1.0.0",
        "tags": "powershell,mitre,investigation",
        "is_builtin": True,
        "actions": [
            {"action": "collect_evidence", "params": {"evidence_types": ["input"]}},
            {"action": "ai_recommend", "params": {}},
            {"action": "create_incident", "params": {"name": "Suspicious PowerShell - {{input.host}}", "severity": "medium"}},
        ],
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "PowerShell Alert", "config": {}, "next_nodes": ["evidence"]},
            {"id": "evidence", "type": "collect_evidence", "name": "Collect Logs", "config": {"evidence_types": ["input"]}, "next_nodes": ["ai_decision"]},
            {"id": "ai_decision", "type": "ai_decision", "name": "AI Analysis", "config": {}, "next_nodes": ["create_incident"]},
            {"id": "create_incident", "type": "create_incident", "name": "Create Incident", "config": {"name": "Suspicious PowerShell - {{input.host}}", "severity": "medium"}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Analyst Approval", "config": {"risk_level": "medium", "summary": "Continue response for {{input.host}}"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "Close", "config": {}},
        ],
    },
    {
        "name": "Port Scan Response",
        "description": "Correlate port scan events, lookup reputation, and recommend firewall block.",
        "trigger": "alert",
        "category": "response",
        "version": "1.0.0",
        "tags": "port_scan,reconnaissance,firewall",
        "is_builtin": True,
        "actions": [
            {"action": "enrich_ioc", "params": {"indicator": "{{input.ip}}"}},
            {"action": "ai_recommend", "params": {}},
            {"action": "block_ip", "params": {"ip": "{{input.ip}}"}},
        ],
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Port Scan Alert", "config": {}, "next_nodes": ["enrich"]},
            {"id": "enrich", "type": "enrich_ioc", "name": "IP Reputation", "config": {"indicator": "{{input.ip}}"}, "next_nodes": ["ai_decision"]},
            {"id": "ai_decision", "type": "ai_decision", "name": "AI Recommendation", "config": {}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Approve Firewall Block", "config": {"risk_level": "medium", "summary": "Block scanning IP {{input.ip}}"}, "next_nodes": ["block_ip"]},
            {"id": "block_ip", "type": "block_ip", "name": "Block IP", "config": {"ip": "{{input.ip}}"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "Close", "config": {}},
        ],
    },
]


class SoarService:
    """SOAR playbook management, execution, and monitoring service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_builtin_playbooks(self) -> int:
        """Insert built-in playbooks if they do not exist."""
        count = 0
        for data in BUILTIN_PLAYBOOKS:
            existing = await self.db.execute(select(Playbook).where(Playbook.name == data["name"], Playbook.is_builtin == True))  # noqa: E712
            if existing.scalar_one_or_none():
                continue
            playbook = Playbook(
                name=data["name"],
                description=data["description"],
                trigger=data["trigger"],
                trigger_config=json.dumps(data.get("trigger_config", {})),
                category=data["category"],
                version=data["version"],
                tags=data.get("tags"),
                is_builtin=True,
                actions=json.dumps(data["actions"]),
                nodes=json.dumps(data["nodes"]),
                status="active",
                created_by=None,
            )
            self.db.add(playbook)
            count += 1
        if count:
            await self.db.commit()
        logger.info("Seeded %d built-in playbooks", count)
        return count

    async def get_playbooks(
        self,
        page: int = 1,
        limit: int = 100,
        status: str | None = None,
    ) -> tuple[Sequence[Playbook], int]:
        query = select(Playbook)
        if status:
            query = query.where(Playbook.status == status)

        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        query = query.order_by(desc(Playbook.updated_at)).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_playbook(self, playbook_id: int) -> Playbook | None:
        result = await self.db.execute(select(Playbook).where(Playbook.id == playbook_id))
        return result.scalar_one_or_none()

    async def create_playbook(self, data: dict[str, Any], created_by: int | None = None) -> Playbook:
        playbook = Playbook(
            name=data["name"],
            description=data.get("description"),
            trigger=data.get("trigger", "manual"),
            trigger_config=json.dumps(data.get("trigger_config", {})),
            status=data.get("status", "active"),
            category=data.get("category", "response"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags"),
            is_builtin=data.get("is_builtin", False),
            actions=json.dumps(data.get("actions", [])),
            nodes=json.dumps(data.get("nodes", [])),
            created_by=created_by,
        )
        self.db.add(playbook)
        await self.db.commit()
        await self.db.refresh(playbook)
        logger.info("Created playbook %s (id=%d)", playbook.name, playbook.id)
        return playbook

    async def update_playbook(self, playbook_id: int, data: dict[str, Any]) -> Playbook | None:
        playbook = await self.get_playbook(playbook_id)
        if not playbook:
            return None
        if playbook.is_builtin:
            raise ValueError("Built-in playbooks cannot be modified")
        for field, value in data.items():
            if field in ("actions", "nodes", "trigger_config"):
                value = json.dumps(value)
            setattr(playbook, field, value)
        await self.db.commit()
        await self.db.refresh(playbook)
        return playbook

    async def delete_playbook(self, playbook_id: int) -> bool:
        playbook = await self.get_playbook(playbook_id)
        if not playbook:
            return False
        if playbook.is_builtin:
            raise ValueError("Built-in playbooks cannot be deleted")
        await self.db.delete(playbook)
        await self.db.commit()
        return True

    async def trigger_alert_playbooks(self, alert: Any, triggered_by: str = "system") -> list[PlaybookExecution]:
        """Run all active alert-triggered playbooks whose filters match an alert."""
        from app.config.settings import get_settings

        if not get_settings().SOAR_AUTO_TRIGGER_ENABLED:
            return []

        result = await self.db.execute(
            select(Playbook).where(Playbook.trigger == "alert", Playbook.status == "active")
        )
        playbooks = result.scalars().all()
        executions = []
        for pb in playbooks:
            try:
                config = json.loads(pb.trigger_config or "{}")
            except Exception:
                config = {}
            if not self._alert_matches(alert, config):
                continue
            input_data = {
                "alert_id": getattr(alert, "id", None),
                "title": getattr(alert, "title", None),
                "severity": getattr(alert, "severity", None),
                "source_ip": getattr(alert, "source_ip", None),
                "destination_ip": getattr(alert, "destination_ip", None),
                "rule_id": getattr(alert, "rule_id", None),
                "mitre_technique": getattr(alert, "mitre_technique", None),
                "status": getattr(alert, "status", None),
            }
            execution = await self.execute_playbook(
                pb,
                triggered_by=triggered_by,
                input_data={k: v for k, v in input_data.items() if v is not None},
                trigger_event=f"alert:{getattr(alert, 'id', '')}",
            )
            executions.append(execution)
        return executions

    def _alert_matches(self, alert: Any, config: dict[str, Any]) -> bool:
        if not config:
            return True
        if "severity_min" in config and (getattr(alert, "severity", 0) or 0) < config["severity_min"]:
            return False
        if "rule_id" in config and config["rule_id"] != getattr(alert, "rule_id", None):
            return False
        if "mitre_technique" in config and config["mitre_technique"] != getattr(alert, "mitre_technique", None):
            return False
        return True

    async def export_playbook(self, playbook_id: int) -> dict[str, Any] | None:
        playbook = await self.get_playbook(playbook_id)
        if not playbook:
            return None
        return {
            "format_version": "1.0",
            "exported_at": utc_now().isoformat(),
            "playbook": {
                "name": playbook.name,
                "description": playbook.description,
                "trigger": playbook.trigger,
                "trigger_config": json.loads(playbook.trigger_config or "{}"),
                "status": playbook.status,
                "category": playbook.category,
                "version": playbook.version,
                "tags": playbook.tags,
                "actions": json.loads(playbook.actions or "[]"),
                "nodes": json.loads(playbook.nodes or "[]"),
            },
        }

    async def import_playbook(self, payload: dict[str, Any], created_by: int | None = None) -> Playbook:
        playbook_data = payload.get("playbook", payload)
        name = playbook_data.get("name")
        # Avoid duplicate names on import
        suffix = ""
        counter = 1
        while await self.db.execute(select(Playbook).where(Playbook.name == f"{name}{suffix}")) and (await self.db.execute(select(Playbook).where(Playbook.name == f"{name}{suffix}"))).scalar_one_or_none():
            suffix = f" ({counter})"
            counter += 1
        data = {
            "name": f"{name}{suffix}",
            "description": playbook_data.get("description"),
            "trigger": playbook_data.get("trigger", "manual"),
            "trigger_config": playbook_data.get("trigger_config", {}),
            "status": playbook_data.get("status", "active"),
            "category": playbook_data.get("category", "response"),
            "version": playbook_data.get("version", "1.0.0"),
            "tags": playbook_data.get("tags"),
            "is_builtin": False,
            "actions": playbook_data.get("actions", []),
            "nodes": playbook_data.get("nodes", []),
        }
        return await self.create_playbook(data, created_by=created_by)

    async def execute_playbook(
        self,
        playbook: Playbook,
        triggered_by: str = "manual",
        input_data: dict[str, Any] | None = None,
        trigger_event: str | None = None,
    ) -> PlaybookExecution:
        execution = PlaybookExecution(
            playbook_id=playbook.id,
            status="running",
            triggered_by=triggered_by,
            trigger_event=trigger_event,
            input_data=json.dumps(input_data or {}),
            context=json.dumps({"variables": {}}),
            node_states=json.dumps({}),
            results=json.dumps({}),
            logs=json.dumps([]),
            approval_status="na",
            requires_approval=False,
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        engine = WorkflowEngine(self.db, playbook, execution, triggered_by=triggered_by)
        try:
            await engine.execute()
        except Exception as exc:
            logger.exception("Playbook %d execution failed", playbook.id)
            execution.status = "failed"
            execution.output_log = json.dumps({"error": str(exc)})
            execution.completed_at = utc_now()
            await self.db.commit()
            await self.db.refresh(execution)
        return execution

    async def get_execution(self, execution_id: int) -> PlaybookExecution | None:
        result = await self.db.execute(select(PlaybookExecution).where(PlaybookExecution.id == execution_id))
        return result.scalar_one_or_none()

    async def get_executions(self, playbook_id: int | None = None, limit: int = 100) -> Sequence[PlaybookExecution]:
        query = select(PlaybookExecution).order_by(desc(PlaybookExecution.started_at))
        if playbook_id:
            query = query.where(PlaybookExecution.playbook_id == playbook_id)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pending_approvals(self, limit: int = 100) -> Sequence[WorkflowApproval]:
        result = await self.db.execute(
            select(WorkflowApproval).where(WorkflowApproval.status == "pending").order_by(desc(WorkflowApproval.created_at)).limit(limit)
        )
        return result.scalars().all()

    async def approve_execution_node(self, approval_id: int, decision: str, user: str | None = None) -> WorkflowApproval | None:
        result = await self.db.execute(select(WorkflowApproval).where(WorkflowApproval.id == approval_id))
        approval = result.scalar_one_or_none()
        if not approval or approval.status != "pending":
            return None
        approval.status = decision
        approval.approved_by = user
        approval.approved_at = utc_now()
        execution = await self.get_execution(approval.execution_id)
        if execution and decision == "approved":
            execution.approval_status = "approved"
            execution.status = "running"
            await self.db.commit()
            await WorkflowEngine.resume_execution(self.db, execution)
        else:
            if execution:
                execution.approval_status = "denied"
                execution.status = "cancelled"
            await self.db.commit()
        await self.db.refresh(approval)
        return approval

    async def get_execution_timeline(self, execution_id: int, limit: int = 200) -> Sequence[WorkflowTimelineEvent]:
        result = await self.db.execute(
            select(WorkflowTimelineEvent)
            .where(WorkflowTimelineEvent.execution_id == execution_id)
            .order_by(WorkflowTimelineEvent.timestamp)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_execution_evidence(self, execution_id: int, limit: int = 200) -> Sequence[WorkflowEvidence]:
        result = await self.db.execute(
            select(WorkflowEvidence)
            .where(WorkflowEvidence.execution_id == execution_id)
            .order_by(WorkflowEvidence.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_execution_action_logs(self, execution_id: int, limit: int = 200) -> Sequence[WorkflowActionLog]:
        result = await self.db.execute(
            select(WorkflowActionLog)
            .where(WorkflowActionLog.execution_id == execution_id)
            .order_by(WorkflowActionLog.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_statistics(self) -> dict[str, Any]:
        total_playbooks = (
            await self.db.execute(select(func.count()).select_from(Playbook))
        ).scalar_one()
        active_playbooks = (
            await self.db.execute(select(func.count()).select_from(Playbook).where(Playbook.status == "active"))
        ).scalar_one()
        total_executions = (
            await self.db.execute(select(func.count()).select_from(PlaybookExecution))
        ).scalar_one()
        completed_executions = (
            await self.db.execute(select(func.count()).select_from(PlaybookExecution).where(PlaybookExecution.status == "completed"))
        ).scalar_one()
        failed_executions = (
            await self.db.execute(select(func.count()).select_from(PlaybookExecution).where(PlaybookExecution.status == "failed"))
        ).scalar_one()
        pending_approvals = (
            await self.db.execute(select(func.count()).select_from(WorkflowApproval).where(WorkflowApproval.status == "pending"))
        ).scalar_one()

        avg_ms = 0.0
        if total_executions:
            rows = await self.db.execute(
                select(PlaybookExecution.started_at, PlaybookExecution.completed_at)
                .where(PlaybookExecution.completed_at.isnot(None))
            )
            durations = [
                (completed_at - started_at).total_seconds() * 1000
                for started_at, completed_at in rows.all()
                if started_at and completed_at
            ]
            if durations:
                avg_ms = sum(durations) / len(durations)

        status_counts = {}
        status_rows = await self.db.execute(select(PlaybookExecution.status, func.count()).group_by(PlaybookExecution.status))
        for st, cnt in status_rows.all():
            status_counts[st] = cnt

        most_executed = []
        top_rows = await self.db.execute(
            select(PlaybookExecution.playbook_id, Playbook.name, func.count())
            .join(Playbook, PlaybookExecution.playbook_id == Playbook.id)
            .group_by(PlaybookExecution.playbook_id, Playbook.name)
            .order_by(desc(func.count()))
            .limit(10)
        )
        for pid, name, cnt in top_rows.all():
            most_executed.append({"playbook_id": pid, "name": name, "count": cnt})

        return {
            "total_playbooks": total_playbooks,
            "active_playbooks": active_playbooks,
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "pending_approvals": pending_approvals,
            "avg_execution_time_ms": avg_ms,
            "execution_status_counts": status_counts,
            "most_executed_playbooks": most_executed,
        }

    @staticmethod
    def list_action_types() -> list[str]:
        return ActionRegistry.list_actions()
