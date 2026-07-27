import json
import logging
from typing import Any

from app.utils.datetime_helper import utc_now
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AiAnalysis, AiFeedback, AiQueryLog, Alert, AnomalyRecord, Asset, Incident, IncidentTimeline, ThreatIntelligence
from app.services.ai_engine.anomaly_detector import AnomalyDetector
from app.services.ai_engine.context_builder import ContextBuilder
from app.services.ai_engine.input_guard import validate_input
from app.services.ai_engine.knowledge_base import KnowledgeBase
from app.services.ai_engine.model_manager import ModelManager
from app.services.ai_engine.prompts import (
    ALERT_ANALYSIS_PROMPT,
    DAILY_REPORT_PROMPT,
    INCIDENT_REPORT_PROMPT,
    PLAYBOOK_GENERATOR_PROMPT,
    SYSTEM_PROMPT,
    THREAT_HUNT_PROMPT,
)
from app.services.ai_engine.rag_retriever import RAGRetriever
from app.services.ai_engine.risk_scorer import RiskScorer
from app.services.ai_engine.threat_intel import ThreatIntelEnricher

logger = logging.getLogger(__name__)


class SentinelAnalysisService:
    """End-to-end Sentinel AI analysis pipeline for security alerts and incidents."""

    def __init__(
        self,
        db: AsyncSession,
        model: ModelManager | None = None,
        enricher: ThreatIntelEnricher | None = None,
        risk_scorer: RiskScorer | None = None,
    ):
        self.db = db
        self.model = model or ModelManager()
        self.enricher = enricher or ThreatIntelEnricher(db)
        self.risk_scorer = risk_scorer or RiskScorer(db)
        self.context_builder = ContextBuilder(db)
        self.kb = KnowledgeBase(db)
        self.rag = RAGRetriever(db)

    async def analyze_alert(self, alert_id: int, persist: bool = True, user_id: int | None = None) -> dict[str, Any]:
        alert = await self.db.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        # Enrich source IP threat intelligence before building context
        ti_data: dict[str, Any] = {}
        if alert.source_ip:
            ti_data = await self.enricher.enrich(alert.source_ip, "ip")

        context = await self.context_builder.build_alert_context(alert)
        context["threat_intelligence"] = ti_data

        prompt = ALERT_ANALYSIS_PROMPT.substitute(
            title=context["title"],
            severity=context["severity"],
            source_ip=context["source_ip"],
            destination_ip=context["destination_ip"],
            rule_id=context["rule_id"],
            mitre_technique=context["mitre_technique"],
            asset_info=json.dumps(context["asset"], indent=2),
            incident_info=json.dumps(context["related_incidents"], indent=2),
            ti_info=json.dumps(ti_data, indent=2),
            vuln_info=json.dumps(context["vulnerabilities"], indent=2),
            raw_log=context["raw_log"],
        )

        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format="json")
        parsed = self._safe_parse(response["raw"])

        if not parsed:
            parsed = self._fallback_analysis(alert, context)
            response["source"] = f"{response.get('source', 'unknown')}-fallback-parsed"

        # Augment MITRE mapping from knowledge base if the LLM returned empty fields
        mitre = self.kb.lookup_mitre(parsed.get("mitre_mapping", {}).get("technique_id") or alert.mitre_technique)
        if parsed.get("mitre_mapping", {}).get("technique_id") in (None, "", "N/A"):
            parsed.setdefault("mitre_mapping", {})
            parsed["mitre_mapping"]["tactic"] = parsed["mitre_mapping"].get("tactic") or mitre["tactic"]
            parsed["mitre_mapping"]["technique"] = parsed["mitre_mapping"].get("technique") or mitre["name"]
            parsed["mitre_mapping"]["technique_id"] = alert.mitre_technique or "T1190"

        # Compute explainable risk score
        risk_score, risk_reason = await self.risk_scorer.calculate_alert_risk(alert)
        parsed["risk_score"] = parsed.get("risk_score") or risk_score
        parsed["risk_reason"] = risk_reason
        parsed["risk_classification"] = self.risk_scorer.classification(risk_score)

        # Merge recommended response with knowledge-base playbook
        playbook = self.kb.playbook_for(
            parsed.get("mitre_mapping", {}).get("technique_id"), alert.title
        )
        parsed.setdefault("recommended_response", {})
        for key in ["immediate", "short_term", "long_term"]:
            existing = parsed["recommended_response"].get(key) or []
            parsed["recommended_response"][key] = existing or playbook.get(key, [])

        if persist:
            analysis = AiAnalysis(
                alert_id=alert.id,
                summary=parsed.get("executive_summary", ""),
                explanation=json.dumps(parsed.get("technical_explanation", {})),
                recommendation=json.dumps(parsed.get("recommended_response", {})),
                confidence=parsed.get("risk_assessment", {}).get("confidence", 0),
                risk_score=parsed["risk_score"],
                severity=parsed.get("risk_assessment", {}).get("severity"),
                priority=parsed.get("risk_assessment", {}).get("priority"),
                mitre_tactic=parsed.get("mitre_mapping", {}).get("tactic"),
                mitre_technique=parsed.get("mitre_mapping", {}).get("technique"),
                mitre_technique_id=parsed.get("mitre_mapping", {}).get("technique_id"),
                investigation_steps=json.dumps(parsed.get("investigation_steps", [])),
                response_steps=json.dumps(parsed.get("recommended_response", {})),
                analyst_notes=parsed.get("analyst_notes", ""),
                raw_response=json.dumps({"source": response.get("source"), "raw": response["raw"]}),
            )
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            parsed["analysis_id"] = analysis.id

        parsed["llm_source"] = response.get("source", "unknown")
        await self._log_query(
            "/ai/analyze-alert",
            {"alert_id": alert_id},
            parsed.get("executive_summary", ""),
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return parsed

    async def analyze_incident(self, incident_id: int, user_id: int | None = None) -> dict[str, Any]:
        incident = await self.db.get(Incident, incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        await self.db.refresh(incident, ['alerts'])

        analyses = []
        for alert in incident.alerts:
            try:
                analysis = await self.analyze_alert(alert.id, persist=True)
                analyses.append({"alert_id": alert.id, "analysis": analysis})
            except Exception as exc:
                logger.warning("Failed to analyze alert %s for incident %s: %s", alert.id, incident_id, exc)

        if user_id:
            await self._log_query(
                "/ai/analyze-incident",
                {"incident_id": incident_id},
                f"Analyzed {len(analyses)} alerts for incident {incident_id}",
                "internal",
                user_id=user_id,
            )

        risk_score, risk_reason = await self.risk_scorer.calculate_incident_risk(incident)
        await self.risk_scorer.store_risk_score("incident", incident.id, risk_score, risk_reason)

        return {
            "incident_id": incident.id,
            "risk_score": risk_score,
            "risk_reason": risk_reason,
            "analyses": analyses,
        }

    async def chat(self, question: str, alert_id: int | None = None, user_id: int | None = None) -> dict[str, Any]:
        question = validate_input(question)
        context = "No specific alert context provided."
        if alert_id:
            alert = await self.db.get(Alert, alert_id)
            if alert:
                ctx = await self.context_builder.build_alert_context(alert)
                # Include any prior AI analysis
                analyses = alert.ai_analyses
                ctx["prior_analyses"] = [
                    {"summary": a.summary, "recommendation": a.recommendation} for a in analyses
                ]
                context = ContextBuilder.context_to_text(ctx)

        from app.services.ai_engine.prompts import CHAT_PROMPT
        prompt = CHAT_PROMPT.substitute(context=context, question=question)
        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format=None)
        answer = response["raw"].strip()
        await self._log_query(
            "/ai/chat",
            {"question": question, "alert_id": alert_id},
            answer,
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return {"answer": answer, "source": response.get("source", "unknown")}

    async def investigate_incident(self, incident_id: int, user_id: int | None = None) -> dict[str, Any]:
        incident = await self.db.get(Incident, incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        await self.db.refresh(incident, ["alerts", "timeline"])

        analyses_result = await self.db.execute(
            select(AiAnalysis).where(AiAnalysis.incident_id == incident_id)
        )
        stored = analyses_result.scalars().all()
        analyses = [self._analysis_to_dict(a) for a in stored]

        timeline = [
            {"action": t.action, "note": t.note, "timestamp": t.timestamp.isoformat()}
            for t in incident.timeline
        ]
        alerts = [
            {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status}
            for a in incident.alerts
        ]

        ti_data: dict[str, Any] = {}
        for alert in incident.alerts:
            if alert.source_ip:
                ti_data[alert.source_ip] = await self.enricher.enrich(alert.source_ip, "ip")

        risk_score, risk_reason = await self.risk_scorer.calculate_incident_risk(incident)

        prompt = INCIDENT_REPORT_PROMPT.substitute(
            incident=json.dumps({"id": incident.id, "name": incident.name, "severity": incident.severity, "status": incident.status, "description": incident.description}, default=str),
            alerts=json.dumps(alerts, default=str),
            timeline=json.dumps(timeline, default=str),
            analyses=json.dumps(analyses, default=str),
            threat_intel=json.dumps(ti_data, default=str),
            risk_score=f"{risk_score} - {risk_reason}",
        )
        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format="json")
        parsed = self._safe_parse(response["raw"], required_keys=["summary"])
        if not parsed:
            parsed = {
                "title": incident.name,
                "severity": incident.severity,
                "summary": "AI incident investigation completed; fallback report generated.",
                "timeline": timeline,
                "affected_assets": list({a.get("asset") for a in alerts}),
                "indicators_of_compromise": [a["source_ip"] for a in alerts],
                "mitre_mapping": [],
                "investigation_performed": ["Reviewed related alerts and timeline."],
                "recommended_remediation": {"immediate": [], "short_term": [], "long_term": []},
                "lessons_learned": [],
            }
        parsed["incident_id"] = incident.id
        parsed["risk_score"] = risk_score
        parsed["risk_reason"] = risk_reason
        parsed.setdefault("llm_source", response.get("source", "unknown"))
        await self._log_query(
            "/ai/investigate-incident",
            {"incident_id": incident_id},
            parsed.get("summary", ""),
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return parsed

    async def threat_hunt(self, query: str, user_id: int | None = None) -> dict[str, Any]:
        query = validate_input(query)
        from datetime import datetime, timedelta
        cutoff = utc_now() - timedelta(days=7)
        result = await self.db.execute(
            select(Alert)
            .where(Alert.created_at >= cutoff)
            .order_by(Alert.created_at.desc())
            .limit(100)
        )
        alerts = result.scalars().all()
        alert_context = [
            {"title": a.title, "severity": a.severity, "source_ip": a.source_ip, "status": a.status, "created_at": a.created_at.isoformat()}
            for a in alerts
        ]

        retrieved = await self.rag.build_context(query, top_k=5)

        anomaly_result = await self.db.execute(
            select(AnomalyRecord)
            .where(AnomalyRecord.created_at >= cutoff)
            .order_by(AnomalyRecord.created_at.desc())
            .limit(20)
        )
        anomaly_records = [
            {
                "feature_type": r.feature_type,
                "record_id": r.record_id,
                "score": r.anomaly_score,
                "features": r.features,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in anomaly_result.scalars().all()
        ]

        prompt = THREAT_HUNT_PROMPT.substitute(
            query=query,
            alerts=json.dumps(alert_context, default=str),
            context=retrieved,
            anomalies=json.dumps(anomaly_records, default=str),
        )
        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format="json")
        parsed = self._safe_parse(response["raw"], required_keys=["summary"])
        if not parsed:
            parsed = {
                "summary": f"No structured result could be generated for hunt query: {query}",
                "hypotheses": [],
                "recommended_queries": [],
                "indicators_to_hunt": [],
                "mitre_techniques": [],
                "priority": "P4",
                "confidence": 0,
            }
        if isinstance(retrieved, str):
            parsed["rag_sources"] = [line.strip() for line in retrieved.splitlines() if line.strip()][:3]
        else:
            parsed["rag_sources"] = retrieved[:3] if isinstance(retrieved, list) else []
        parsed.setdefault("llm_source", response.get("source", "unknown"))
        await self._log_query(
            "/ai/threat-hunt",
            {"query": query},
            parsed.get("summary", ""),
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return parsed

    async def generate_playbook(self, alert_description: str, mitre_technique: str | None = None, severity: int = 5, user_id: int | None = None) -> dict[str, Any]:
        alert_description = validate_input(alert_description)
        prompt = PLAYBOOK_GENERATOR_PROMPT.substitute(
            alert_description=alert_description,
            mitre_technique=mitre_technique or "Unknown",
            severity=str(severity),
        )
        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format="json")
        parsed = self._safe_parse(response["raw"], required_keys=["name", "actions"])
        if not parsed:
            parsed = {
                "name": "Generic Response Playbook",
                "description": alert_description,
                "trigger": "alert",
                "actions": [{"action": "create_ticket", "params": {}}],
                "expected_outcome": "Track and triage the alert.",
                "automation_notes": "Require human confirmation before containment.",
            }
        parsed["llm_source"] = response.get("source", "unknown")
        await self._log_query(
            "/ai/generate-playbook",
            {"description": alert_description},
            parsed.get("name", ""),
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return parsed

    async def generate_daily_report(self, user_id: int | None = None) -> dict[str, Any]:
        from datetime import date, datetime, timedelta, timezone
        today = date.today()
        start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        alerts_result = await self.db.execute(
            select(Alert).where(Alert.created_at >= start).where(Alert.created_at < end)
        )
        alerts = alerts_result.scalars().all()
        critical = [a for a in alerts if a.severity >= 10]

        incidents_result = await self.db.execute(
            select(Incident)
        )
        incidents = incidents_result.scalars().all()
        open_incidents = [i for i in incidents if i.status in ("open", "in_progress")]

        ti_result = await self.db.execute(
            select(ThreatIntelligence).order_by(ThreatIntelligence.last_seen.desc()).limit(10)
        )
        ti = ti_result.scalars().all()

        stats = {
            "total_alerts": len(alerts),
            "critical_alerts": len(critical),
            "total_incidents": len(incidents),
            "open_incidents": len(open_incidents),
        }

        prompt = DAILY_REPORT_PROMPT.substitute(
            date=str(today),
            stats=json.dumps(stats, default=str),
            top_alerts=json.dumps([{"title": a.title, "severity": a.severity, "status": a.status} for a in critical[:10]], default=str),
            incidents=json.dumps([{"id": i.id, "name": i.name, "severity": i.severity, "status": i.status} for i in open_incidents], default=str),
            threat_intel=json.dumps([{"indicator": i.indicator, "type": i.type, "confidence": i.confidence} for i in ti], default=str),
        )
        response = await self.model.generate(prompt=prompt, system=SYSTEM_PROMPT, format="json")
        parsed = self._safe_parse(response["raw"])
        if not parsed:
            parsed = {
                "title": f"Daily SOC Report - {today}",
                "date": str(today),
                "executive_summary": "Daily summary generated from current telemetry.",
                "key_metrics": stats,
                "top_threats": [a.title for a in critical[:5]],
                "incident_status": [],
                "recommendations": ["Review critical alerts", "Triage open incidents"],
            }
        parsed["llm_source"] = response.get("source", "unknown")
        parsed["key_metrics"] = parsed.get("key_metrics") or stats
        await self._log_query(
            "/ai/generate-report",
            {"type": "daily"},
            parsed.get("executive_summary", ""),
            response.get("source", "unknown"),
            user_id=user_id,
        )
        return parsed

    async def get_feedback(self, limit: int = 100) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(AiFeedback).order_by(AiFeedback.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": f.id,
                "analysis_id": f.analysis_id,
                "user_id": f.user_id,
                "helpful": f.helpful,
                "incorrect": f.incorrect,
                "comment": f.comment,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in rows
        ]

    async def submit_feedback(self, analysis_id: int, user_id: int | None, helpful: bool, incorrect: bool, comment: str | None = None) -> AiFeedback:
        analysis = await self.db.get(AiAnalysis, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        feedback = AiFeedback(
            analysis_id=analysis_id,
            user_id=user_id,
            helpful=helpful,
            incorrect=incorrect,
            comment=comment or "",
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(AiAnalysis)
            .order_by(AiAnalysis.created_at.desc())
            .limit(limit)
        )
        analyses = result.scalars().all()
        return [self._analysis_to_dict(a) for a in analyses]

    async def get_query_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        from datetime import datetime
        result = await self.db.execute(
            select(AiQueryLog).order_by(AiQueryLog.created_at.desc()).limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "endpoint": log.endpoint,
                "request_payload": log.request_payload,
                "response_summary": log.response_summary,
                "source": log.source,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    async def detect_anomalies(self, hours: int = 168) -> dict[str, Any]:
        detector = AnomalyDetector()
        auth = await detector.analyze_auth_patterns(self.db, hours=hours)
        traffic = await detector.analyze_traffic_patterns(self.db, hours=hours)
        return {"auth": auth, "traffic": traffic}

    async def _log_query(
        self,
        endpoint: str,
        request: dict[str, Any],
        summary: str,
        source: str,
        user_id: int | None = None,
    ) -> None:
        try:
            log = AiQueryLog(
                user_id=user_id,
                endpoint=endpoint,
                request_payload=json.dumps(request, default=str),
                response_summary=summary[:1000],
                source=source,
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as exc:
            logger.warning("Failed to log AI query: %s", exc)

    def _analysis_to_dict(self, analysis: AiAnalysis) -> dict[str, Any]:
        return {
            "id": analysis.id,
            "alert_id": analysis.alert_id,
            "incident_id": analysis.incident_id,
            "summary": analysis.summary,
            "explanation": analysis.explanation,
            "recommendation": analysis.recommendation,
            "confidence": analysis.confidence,
            "risk_score": analysis.risk_score,
            "severity": analysis.severity,
            "priority": analysis.priority,
            "mitre_tactic": analysis.mitre_tactic,
            "mitre_technique": analysis.mitre_technique,
            "mitre_technique_id": analysis.mitre_technique_id,
            "investigation_steps": analysis.investigation_steps,
            "response_steps": analysis.response_steps,
            "analyst_notes": analysis.analyst_notes,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }

    def _safe_parse(self, raw: str, required_keys: list[str] | None = None) -> dict[str, Any] | None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if not parsed:
            stripped = raw.strip()
            if stripped.startswith("```"):
                lines = stripped.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                try:
                    parsed = json.loads("\n".join(lines))
                except json.JSONDecodeError:
                    return None
        if not isinstance(parsed, dict):
            return None
        if required_keys and not all(k in parsed for k in required_keys):
            return None
        return parsed

    def _fallback_analysis(self, alert: Alert, context: dict[str, Any]) -> dict[str, Any]:
        kb = KnowledgeBase()
        mitre = kb.lookup_mitre(alert.mitre_technique)
        playbook = kb.playbook_for(alert.mitre_technique, alert.title)
        return {
            "executive_summary": f"Alert '{alert.title}' was triggered with severity {alert.severity}. The event requires triage.",
            "technical_explanation": {
                "what": alert.description or "No detailed description available.",
                "how": f"Detection rule {alert.rule_id} produced this alert.",
                "logs": alert.raw_log or "Raw log not available.",
                "indicators": [alert.source_ip, alert.destination_ip],
            },
            "mitre_mapping": {
                "tactic": mitre["tactic"],
                "technique": mitre["name"],
                "technique_id": alert.mitre_technique or "T1190",
            },
            "risk_assessment": {
                "severity": "high" if alert.severity >= 10 else "medium" if alert.severity >= 7 else "low",
                "confidence": 60,
                "business_impact": "Potential unauthorized access if confirmed.",
                "priority": "P1" if alert.severity >= 10 else "P2" if alert.severity >= 7 else "P3",
            },
            "investigation_steps": [
                "Check source IP reputation.",
                "Review asset logs for related activity.",
                "Verify whether the activity was authorized.",
            ],
            "recommended_response": {
                "immediate": playbook.get("immediate", []),
                "short_term": playbook.get("short_term", []),
                "long_term": playbook.get("long_term", []),
            },
            "analyst_notes": "Fallback analysis generated because the LLM response could not be parsed.",
        }
