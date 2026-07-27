import json
import logging
import time
from typing import Any

from sqlalchemy import select

from app.database.models import (
    Playbook,
    PlaybookExecution,
    WorkflowApproval,
    WorkflowEvidence,
    WorkflowTimelineEvent,
)
from app.services.soar.workflow_engine.actions import (
    ActionRegistry,
    _add_evidence,
    _add_timeline_event,
    _log_action,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Execute node-based SOAR workflows with conditions, approvals, and retries."""

    def __init__(self, db: Any, playbook: Playbook, execution: PlaybookExecution, triggered_by: str = "system"):
        self.db = db
        self.playbook = playbook
        self.execution = execution
        self.triggered_by = triggered_by
        self.context = self._load_context()

    def _load_context(self) -> dict[str, Any]:
        try:
            ctx = json.loads(self.execution.context or "{}")
        except Exception:
            ctx = {}
        ctx.setdefault("variables", {})
        ctx.setdefault("input_data", self._load_input_data())
        ctx.setdefault("playbook", self._playbook_dict())
        ctx["db"] = self.db
        ctx["execution"] = self.execution
        ctx["triggered_by"] = self.triggered_by
        return ctx

    def _load_input_data(self) -> dict[str, Any]:
        try:
            return json.loads(self.execution.input_data or "{}")
        except Exception:
            return {}

    def _playbook_dict(self) -> dict[str, Any]:
        return {
            "id": self.playbook.id,
            "name": self.playbook.name,
            "trigger": self.playbook.trigger,
            "category": getattr(self.playbook, "category", "response"),
        }

    def _nodes(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.playbook.nodes or "[]")
        except Exception:
            return []

    def _actions(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.playbook.actions or "[]")
        except Exception:
            return []

    def _save_state(self) -> None:
        self.execution.context = json.dumps({k: v for k, v in self.context.items() if k not in ("db", "execution")})

    async def execute(self) -> dict[str, Any]:
        start = time.time()
        nodes = self._nodes()
        if nodes:
            return await self._execute_nodes(nodes)
        # Legacy sequential action runner
        results = await self._execute_legacy_actions()
        self.execution.output_log = json.dumps(results)
        self.execution.completed_at = self._now()
        self.execution.status = "completed"
        await self.db.commit()
        await self.db.refresh(self.execution)
        return {"status": "completed", "results": results, "duration_ms": int((time.time() - start) * 1000)}

    async def _execute_legacy_actions(self) -> list[dict[str, Any]]:
        results = []
        actions = self._actions()
        await _add_timeline_event(self.context, "execution_started", f"Started legacy execution of {self.playbook.name}")
        for idx, action_def in enumerate(actions):
            action_type = action_def.get("action") or action_def.get("type")
            params = action_def.get("params", {})
            result = await self._run_action_handler(action_type, params, node_id=f"legacy_{idx}")
            results.append({"step": idx + 1, "action": action_type, "result": result})
        await _add_timeline_event(self.context, "execution_completed", f"Completed legacy execution of {self.playbook.name}")
        return results

    async def _execute_nodes(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        node_map = {n["id"]: n for n in nodes if "id" in n}
        states = self._load_node_states()
        current_id = self.execution.current_node_id or self._start_node(node_map)
        await _add_timeline_event(self.context, "execution_started", f"Started workflow {self.playbook.name} at node {current_id}")

        while current_id and current_id != "end":
            self.execution.current_node_id = current_id
            node = node_map.get(current_id)
            if not node:
                break
            if states.get(current_id) == "completed":
                current_id = self._next_node(node, node_map, states)
                continue

            node_type = node.get("type", "action")
            if node_type == "approval":
                approval = await self._get_approval(current_id)
                if approval:
                    if approval.status == "pending":
                        self.execution.status = "awaiting_approval"
                        self.execution.approval_status = "pending"
                        self.execution.requires_approval = True
                        await _add_timeline_event(self.context, "approval_requested", f"Awaiting approval at node {current_id}", node_id=current_id)
                        self._save_state()
                        await self.db.commit()
                        await self.db.refresh(self.execution)
                        return {"status": "awaiting_approval", "node_id": current_id}
                    if approval.status == "denied":
                        states[current_id] = "completed"
                        self.execution.status = "cancelled"
                        self.execution.approval_status = "denied"
                        self.execution.requires_approval = False
                        self.execution.completed_at = self._now()
                        await _add_timeline_event(self.context, "approval_denied", f"Approval denied at node {current_id}", node_id=current_id)
                        self._save_state()
                        await self.db.commit()
                        await self.db.refresh(self.execution)
                        return {"status": "cancelled", "node_id": current_id}
                    # approved -> fall through to execute action (log) and continue
                    result = {"approval_id": approval.id, "status": "approved"}
                else:
                    result = await self._create_approval(node)
                    states[current_id] = "pending"
                    self.execution.node_states = json.dumps(states)
                    self.execution.status = "awaiting_approval"
                    self.execution.approval_status = "pending"
                    self.execution.requires_approval = True
                    await _add_timeline_event(self.context, "approval_requested", f"Awaiting approval at node {current_id}", node_id=current_id)
                    self._save_state()
                    await self.db.commit()
                    await self.db.refresh(self.execution)
                    return {"status": "awaiting_approval", "node_id": current_id}
            else:
                result = await self._run_node(node)
            states[current_id] = "completed"
            self.execution.node_states = json.dumps(states)
            self.context["variables"][f"{current_id}_result"] = result
            current_id = self._next_node(node, node_map, states)

        self.execution.current_node_id = None
        self.execution.status = "completed"
        self.execution.approval_status = "na"
        self.execution.requires_approval = False
        self.execution.completed_at = self._now()
        await _add_timeline_event(self.context, "execution_completed", f"Workflow {self.playbook.name} completed")
        self._save_state()
        self.execution.output_log = json.dumps(self.context["variables"])
        await self.db.commit()
        await self.db.refresh(self.execution)
        return {"status": "completed", "variables": self.context["variables"]}

    def _start_node(self, node_map: dict[str, Any]) -> str | None:
        for node_id, node in node_map.items():
            if node.get("type") == "trigger":
                return node_id
        return next(iter(node_map), None)

    def _load_node_states(self) -> dict[str, str]:
        try:
            return json.loads(self.execution.node_states or "{}")
        except Exception:
            return {}

    def _next_node(self, node: dict[str, Any], node_map: dict[str, Any], states: dict[str, str]) -> str | None:
        next_nodes = node.get("next_nodes", [])
        if not next_nodes:
            return None
        if len(next_nodes) == 1:
            return next_nodes[0]
        for n_id in next_nodes:
            n = node_map.get(n_id)
            cond = n.get("condition") if n else None
            if self._evaluate_condition(cond):
                return n_id
        return next_nodes[-1]

    def _evaluate_condition(self, condition: str | None) -> bool:
        if not condition:
            return True
        # Very lightweight condition evaluator: allow simple variable comparison expressions
        try:
            # Provide a safe dict of variable references
            variables = self.context["variables"]
            return bool(eval(condition, {"__builtins__": {}}, variables))  # noqa: S307
        except Exception:
            return True

    def _render_value(self, value: Any) -> Any:
        if isinstance(value, str):
            rendered = value
            for key, val in self.context.get("input_data", {}).items():
                rendered = rendered.replace(f"{{{{input.{key}}}}}", str(val))
            for key, val in self.context.get("variables", {}).items():
                if isinstance(val, (str, int, float, bool)):
                    rendered = rendered.replace(f"{{{{variables.{key}}}}}", str(val))
            return rendered
        if isinstance(value, dict):
            return {k: self._render_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._render_value(v) for v in value]
        return value

    async def _run_node(self, node: dict[str, Any]) -> dict[str, Any]:
        node_id = node.get("id")
        node_type = node.get("type", "action")
        config = self._render_value(node.get("config", {}))
        await _add_timeline_event(self.context, "node_started", f"Running {node_type} node {node_id}", node_id=node_id)
        if node_type in ("trigger", "start"):
            return {"status": "ok"}
        if node_type == "condition":
            cond = node.get("condition") or config.get("condition")
            result = {"matched": self._evaluate_condition(cond)}
            await _log_action(self.context, "condition", "ok", config, result, node_id=node_id)
            return result
        if node_type == "collect_evidence":
            return await ActionRegistry.get("collect_evidence")(self.context, config, node_id=node_id)
        if node_type == "ai_decision":
            return await ActionRegistry.get("ai_recommend")(self.context, config, node_id=node_id)
        handler = ActionRegistry.get(node_type)
        if handler:
            return await handler(self.context, config, node_id=node_id)
        # Generic action handler for registered actions
        action_name = config.get("action") or node_type
        return await self._run_action_handler(action_name, config, node_id=node_id)

    async def _run_action_handler(self, action_name: str | None, config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
        import asyncio

        handler = ActionRegistry.get(action_name or "")
        if not handler:
            return {"status": "skipped", "reason": f"Unknown action {action_name}"}

        max_retries = int(config.get("retries", config.get("retry", 0)))
        delay = float(config.get("retry_delay", 1.0))
        start = time.time()
        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                result = await handler(self.context, config, node_id=node_id)
                status = "ok"
                break
            except Exception as exc:
                last_exception = exc
                logger.warning("Action %s attempt %d/%d failed: %s", action_name, attempt + 1, max_retries + 1, exc)
                if attempt < max_retries:
                    await asyncio.sleep(delay * (2**attempt))
        else:
            logger.exception("Action %s failed after %d retries", action_name, max_retries)
            result = {"status": "error", "error": str(last_exception)}
            status = "error"

        await _log_action(self.context, action_name or "unknown", status, config, result, duration_ms=int((time.time() - start) * 1000), node_id=node_id)
        return result

    async def _create_approval(self, node: dict[str, Any]) -> dict[str, Any]:
        node_id = node.get("id")
        config = self._render_value(node.get("config", {}))
        summary = config.get("summary") or f"Approval required at {node_id}"
        risk = config.get("risk_level", "medium")
        approval = WorkflowApproval(
            execution_id=self.execution.id,
            playbook_id=self.playbook.id,
            node_id=node_id,
            action_summary=summary,
            risk_level=risk,
            status="pending",
            requested_by=self.triggered_by,
            details=json.dumps({"config": config}),
        )
        self.db.add(approval)
        await self.db.commit()
        await self.db.refresh(approval)
        return {"approval_id": approval.id, "status": "pending"}

    async def _get_approval(self, node_id: str):
        result = await self.db.execute(
            select(WorkflowApproval).where(
                WorkflowApproval.execution_id == self.execution.id,
                WorkflowApproval.node_id == node_id,
            )
        )
        return result.scalar_one_or_none()

    def _now(self):
        from app.utils.datetime_helper import utc_now
        return utc_now()

    @staticmethod
    async def resume_execution(db: Any, execution: PlaybookExecution) -> dict[str, Any]:
        result = await db.execute(select(Playbook).where(Playbook.id == execution.playbook_id))
        playbook = result.scalar_one_or_none()
        if not playbook:
            return {"status": "error", "reason": "playbook not found"}
        engine = WorkflowEngine(db, playbook, execution, triggered_by=execution.triggered_by or "system")
        return await engine.execute()
