import json
import logging
from functools import wraps
from typing import Any, Awaitable, Callable

from sqlalchemy import select

from app.database.models import (
    Alert,
    Asset,
    Campaign,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    Malware,
    PlaybookExecution,
    ThreatActor,
    ThreatIOC,
    VulnerabilityIntelligence,
    WorkflowActionLog,
    WorkflowEvidence,
    WorkflowTimelineEvent,
)

logger = logging.getLogger(__name__)

ActionHandler = Callable[..., Awaitable[dict[str, Any]]]


class ActionRegistry:
    """Registry of workflow action handlers."""

    _handlers: dict[str, ActionHandler] = {}

    @classmethod
    def register(cls, name: str, handler: ActionHandler) -> None:
        cls._handlers[name] = handler

    @classmethod
    def get(cls, name: str) -> ActionHandler | None:
        return cls._handlers.get(name)

    @classmethod
    def list_actions(cls) -> list[str]:
        return sorted(cls._handlers.keys())


def action(name: str) -> Callable[[ActionHandler], ActionHandler]:
    def decorator(handler: ActionHandler) -> ActionHandler:
        ActionRegistry.register(name, handler)

        @wraps(handler)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return await handler(*args, **kwargs)

        return wrapper

    return decorator


async def _log_action(
    ctx: dict[str, Any],
    action_type: str,
    status: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    duration_ms: int | None = None,
    node_id: str | None = None,
) -> None:
    db = ctx["db"]
    execution = ctx["execution"]
    log = WorkflowActionLog(
        execution_id=execution.id,
        node_id=node_id,
        action_type=action_type,
        status=status,
        input_data=json.dumps(input_data),
        output_data=json.dumps(output_data),
        duration_ms=duration_ms,
    )
    db.add(log)


async def _add_evidence(
    ctx: dict[str, Any],
    evidence_type: str,
    content: dict[str, Any],
    source: str | None = None,
    node_id: str | None = None,
) -> None:
    db = ctx["db"]
    execution = ctx["execution"]
    ev = WorkflowEvidence(
        execution_id=execution.id,
        node_id=node_id,
        evidence_type=evidence_type,
        source=source or "workflow",
        content=json.dumps(content),
    )
    db.add(ev)


async def _add_timeline_event(
    ctx: dict[str, Any],
    event_type: str,
    message: str,
    details: dict[str, Any] | None = None,
    actor: str | None = None,
    node_id: str | None = None,
) -> None:
    db = ctx["db"]
    execution = ctx["execution"]
    event = WorkflowTimelineEvent(
        execution_id=execution.id,
        node_id=node_id,
        event_type=event_type,
        message=message,
        actor=actor or ctx.get("triggered_by", "system"),
        details=json.dumps(details or {}),
    )
    db.add(event)


@action("collect_evidence")
async def collect_evidence(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    evidence_types = config.get("evidence_types", ["input"])
    collected = []
    for et in evidence_types:
        if et == "input":
            collected.append({"type": "input", "data": ctx.get("input_data", {})})
        elif et == "context":
            collected.append({"type": "context", "data": ctx.get("variables", {})})
    for item in collected:
        await _add_evidence(ctx, item["type"], item["data"], node_id=node_id)
    result = {"collected": len(collected)}
    await _log_action(ctx, "collect_evidence", "ok", config, result, node_id=node_id)
    return result


@action("enrich_ioc")
async def enrich_ioc(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    indicator = config.get("indicator") or ctx.get("variables", {}).get("indicator") or ctx.get("input_data", {}).get("indicator")
    ioc_type = config.get("type") or ctx.get("variables", {}).get("type") or ctx.get("input_data", {}).get("type")
    if not indicator:
        return {"status": "skipped", "reason": "no indicator"}
    from app.services.threat_intelligence.enrichment.orchestrator import ThreatIntelligenceEngine

    engine = ThreatIntelligenceEngine(ctx["db"])
    try:
        result = await engine.enrich(indicator, ioc_type)
        await engine.close()
    except Exception as exc:
        await engine.close()
        logger.debug("IOC enrichment failed in workflow: %s", exc)
        result = {"status": "error", "error": str(exc)}
    await _add_evidence(ctx, "ioc_enrichment", result, source="threat_intelligence", node_id=node_id)
    ctx["variables"]["ioc_result"] = result
    await _log_action(ctx, "enrich_ioc", "ok" if "error" not in result else "error", config, result, node_id=node_id)
    return result


@action("enrich_alert")
async def enrich_alert(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    alert_id = config.get("alert_id") or ctx.get("input_data", {}).get("alert_id")
    if not alert_id:
        return {"status": "skipped", "reason": "no alert_id"}
    result = await ctx["db"].execute(select(Alert).where(Alert.id == int(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        return {"status": "error", "reason": "alert not found"}
    from app.services.alert_enrichment import AlertEnrichmentService

    service = AlertEnrichmentService(ctx["db"])
    enrichment = await service.enrich(alert)
    ctx["variables"]["alert_enrichment"] = enrichment
    await _add_evidence(ctx, "alert_enrichment", enrichment, source="alert_enrichment", node_id=node_id)
    await _log_action(ctx, "enrich_alert", "ok", config, {"enriched": True}, node_id=node_id)
    return enrichment


@action("query_threat_intel")
async def query_threat_intel(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    indicator = config.get("indicator") or ctx.get("variables", {}).get("indicator")
    result_rows = await ctx["db"].execute(select(ThreatIOC).where(ThreatIOC.value == indicator))
    rows = result_rows.scalars().all()
    result = {"matches": [{"value": r.value, "type": r.type, "score": r.threat_score} for r in rows]}
    await _add_evidence(ctx, "threat_intel_query", result, source="database", node_id=node_id)
    ctx["variables"]["threat_intel_result"] = result
    await _log_action(ctx, "query_threat_intel", "ok", config, result, node_id=node_id)
    return result


@action("ai_recommend")
async def ai_recommend(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    prompt_context = {
        "input": ctx.get("input_data", {}),
        "variables": ctx.get("variables", {}),
        "playbook": ctx.get("playbook", {}).get("name"),
    }
    # Lightweight deterministic recommendation when AI is not available
    recommendation = _deterministic_recommendation(prompt_context)
    result = {
        "recommendation": recommendation["action"],
        "confidence": recommendation["confidence"],
        "business_impact": recommendation["business_impact"],
        "alternatives": recommendation["alternatives"],
        "priority": recommendation["priority"],
    }
    ctx["variables"]["ai_recommendation"] = result
    await _add_evidence(ctx, "ai_recommendation", result, source="ai_decision_engine", node_id=node_id)
    await _log_action(ctx, "ai_recommend", "ok", config, result, node_id=node_id)
    return result


def _deterministic_recommendation(context: dict[str, Any]) -> dict[str, Any]:
    variables = context.get("variables", {})
    ioc = variables.get("ioc_result", {})
    score = ioc.get("threat_score", 0) if isinstance(ioc, dict) else 0
    if score >= 80:
        return {"action": "block_and_isolate", "confidence": 95, "business_impact": "high", "alternatives": ["notify_only"], "priority": "critical"}
    if score >= 50:
        return {"action": "request_approval_for_block", "confidence": 75, "business_impact": "medium", "alternatives": ["monitor", "notify"], "priority": "high"}
    return {"action": "monitor_and_notify", "confidence": 60, "business_impact": "low", "alternatives": ["close"], "priority": "medium"}


@action("create_incident")
async def create_incident(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    name = config.get("name") or f"SOAR incident from playbook {ctx['playbook']['name']}"
    severity = config.get("severity", "medium")
    description = config.get("description") or json.dumps(ctx.get("input_data", {}))
    incident = Incident(
        name=name,
        description=description,
        severity=severity,
        status=IncidentStatus.OPEN.value,
    )
    ctx["db"].add(incident)
    await ctx["db"].flush()
    ctx["variables"]["incident_id"] = incident.id
    await _add_evidence(ctx, "created_incident", {"incident_id": incident.id}, source="soar", node_id=node_id)
    await _log_action(ctx, "create_incident", "ok", config, {"incident_id": incident.id}, node_id=node_id)
    return {"incident_id": incident.id}


@action("update_incident")
async def update_incident(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    incident_id = config.get("incident_id") or ctx.get("variables", {}).get("incident_id")
    if not incident_id:
        return {"status": "skipped", "reason": "no incident_id"}
    result = await ctx["db"].execute(select(Incident).where(Incident.id == int(incident_id)))
    incident = result.scalar_one_or_none()
    if not incident:
        return {"status": "error", "reason": "incident not found"}
    if "severity" in config:
        incident.severity = config["severity"]
    if "status" in config:
        incident.status = config["status"]
    if "owner" in config:
        # owner stored as note for now
        incident.description = (incident.description or "") + f"\nOwner: {config['owner']}"
    await _log_action(ctx, "update_incident", "ok", config, {"incident_id": incident.id}, node_id=node_id)
    return {"updated": True, "incident_id": incident.id}


@action("block_ip")
async def block_ip(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    ip = config.get("ip") or ctx.get("variables", {}).get("ip") or ctx.get("input_data", {}).get("ip")
    if not ip:
        return {"status": "skipped", "reason": "no ip"}
    result = {"status": "simulated", "action": "block_ip", "ip": ip, "message": f"Blocked IP {ip} via firewall (simulated)"}
    ctx["variables"]["blocked_ip"] = ip
    await _add_evidence(ctx, "response_action", result, source="responder", node_id=node_id)
    await _log_action(ctx, "block_ip", "ok", config, result, node_id=node_id)
    return result


@action("quarantine_host")
async def quarantine_host(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    host = config.get("host") or ctx.get("variables", {}).get("host") or ctx.get("input_data", {}).get("host")
    if not host:
        return {"status": "skipped", "reason": "no host"}
    result = {"status": "simulated", "action": "quarantine_host", "host": host, "message": f"Quarantined host {host} (simulated)"}
    await _add_evidence(ctx, "response_action", result, source="responder", node_id=node_id)
    await _log_action(ctx, "quarantine_host", "ok", config, result, node_id=node_id)
    return result


@action("isolate_endpoint")
async def isolate_endpoint(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    endpoint = config.get("endpoint") or ctx.get("variables", {}).get("host") or ctx.get("input_data", {}).get("host")
    if not endpoint:
        return {"status": "skipped", "reason": "no endpoint"}
    result = {"status": "simulated", "action": "isolate_endpoint", "endpoint": endpoint, "message": f"Isolated endpoint {endpoint} (simulated)"}
    await _add_evidence(ctx, "response_action", result, source="responder", node_id=node_id)
    await _log_action(ctx, "isolate_endpoint", "ok", config, result, node_id=node_id)
    return result


@action("disable_user")
async def disable_user(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    user = config.get("user") or ctx.get("input_data", {}).get("user")
    if not user:
        return {"status": "skipped", "reason": "no user"}
    result = {"status": "simulated", "action": "disable_user", "user": user, "message": f"Disabled user {user} (simulated)"}
    await _add_evidence(ctx, "response_action", result, source="responder", node_id=node_id)
    await _log_action(ctx, "disable_user", "ok", config, result, node_id=node_id)
    return result


@action("send_email")
async def send_email(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    from app.services.soar.notifications.notification_service import NotificationService

    recipient = config.get("recipient", "soc@goldendome.local")
    subject = config.get("subject", "SOAR Notification")
    body = config.get("body", "A SOAR playbook has executed.")
    result = await NotificationService().send_email(recipient, subject, body, config.get("sender"))
    await _add_timeline_event(ctx, "notification", f"email to {recipient}: {subject}", node_id=node_id)
    await _log_action(ctx, "send_email", result.get("status", "ok"), config, result, node_id=node_id)
    return result


@action("notify")
async def notify(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    from app.services.soar.notifications.notification_service import NotificationService

    channel = config.get("channel", "notification_center")
    message = config.get("message", "SOAR workflow notification")
    result = await NotificationService().notify(channel, config, message)
    await _add_timeline_event(ctx, "notification", f"{channel}: {message}", node_id=node_id)
    await _log_action(ctx, "notify", result.get("status", "ok"), config, result, node_id=node_id)
    return result


@action("create_ticket")
async def create_ticket(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    title = config.get("title") or "SOAR Ticket"
    result = {"status": "simulated", "ticket_id": f"TICKET-{ctx['execution'].id}", "title": title}
    await _log_action(ctx, "create_ticket", "ok", config, result, node_id=node_id)
    return result


@action("webhook")
async def webhook(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    url = config.get("url", "")
    result = {"status": "simulated", "url": url, "message": f"Called webhook {url} (simulated)"}
    await _log_action(ctx, "webhook", "ok", config, result, node_id=node_id)
    return result


@action("generate_report")
async def generate_report(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    report_type = config.get("report_type", "summary")
    summary = {
        "playbook": ctx["playbook"]["name"],
        "execution_id": ctx["execution"].id,
        "input": ctx.get("input_data", {}),
        "variables": ctx.get("variables", {}),
    }
    result = {"report_type": report_type, "summary": summary}
    await _add_evidence(ctx, "report", result, source="soar", node_id=node_id)
    await _log_action(ctx, "generate_report", "ok", config, result, node_id=node_id)
    return result


@action("wait_approval")
async def wait_approval(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    # Handled by engine; this action returns a placeholder if executed directly.
    return {"status": "awaiting_approval", "node_id": node_id, "reason": config.get("reason", "approval required")}


@action("close_incident")
async def close_incident(ctx: dict[str, Any], config: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    incident_id = config.get("incident_id") or ctx.get("variables", {}).get("incident_id")
    if not incident_id:
        return {"status": "skipped", "reason": "no incident_id"}
    result = await ctx["db"].execute(select(Incident).where(Incident.id == int(incident_id)))
    incident = result.scalar_one_or_none()
    if incident:
        incident.status = IncidentStatus.CLOSED.value
    result = {"incident_id": incident_id, "status": "closed"}
    await _log_action(ctx, "close_incident", "ok", config, result, node_id=node_id)
    return result
