import json
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, Incident, IncidentSeverity, IncidentStatus, MITRETechnique
from app.services.ai_engine.analysis import SentinelAnalysisService
from app.services.ai_engine.threat_intel import ThreatIntelEnricher
from app.services.threat_intelligence.enrichment.orchestrator import ThreatIntelligenceEngine

from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)


class AlertEnrichmentService:
    """Enrich an alert with MITRE, threat intelligence, AI analysis, and optional incident creation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = SentinelAnalysisService(db)
        self.ti_service = ThreatIntelEnricher(db)
        self.ti_engine = ThreatIntelligenceEngine(db)

    async def enrich(self, alert_id: int, create_incident: bool = False) -> dict:
        alert = await self.db.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        result = {"alert_id": alert.id, "enriched_at": utc_now().isoformat()}

        # MITRE enrichment
        if alert.mitre_technique:
            mitre = await self._lookup_mitre(alert.mitre_technique)
            result["mitre"] = mitre

        # Threat intelligence enrichment (legacy service)
        ti_results = []
        if alert.source_ip:
            ti_results.append(await self.ti_service.enrich(alert.source_ip, type_hint="ip"))
        if alert.destination_ip:
            ti_results.append(await self.ti_service.enrich(alert.destination_ip, type_hint="ip"))
        result["threat_intelligence"] = ti_results
        await self.ti_service.close()

        # Threat intelligence engine (new normalized IOC extraction, enrichment, correlation)
        try:
            ti_engine_result = await self.ti_engine.enrich_alert(alert, persist_links=True)
            result["threat_iocs_extracted"] = ti_engine_result
        except Exception as exc:
            logger.exception("Threat intelligence engine enrichment failed for alert %s", alert_id)
            result["threat_iocs_extracted"] = {"error": str(exc)}
        finally:
            await self.ti_engine.close()

        # AI analysis
        try:
            ai_result = await self.ai_service.analyze_alert(alert_id)
            mitre_mapping = ai_result.get("mitre_mapping", {})
            risk_assessment = ai_result.get("risk_assessment", {})
            result["ai_analysis"] = {
                "summary": ai_result.get("executive_summary", ""),
                "severity": risk_assessment.get("severity"),
                "risk_score": ai_result.get("risk_score", 0),
                "mitre_technique_id": mitre_mapping.get("technique_id"),
                "mitre_tactic": mitre_mapping.get("tactic"),
                "investigation_steps": ai_result.get("investigation_steps", []),
                "response_steps": ai_result.get("recommended_response", {}),
            }
        except Exception as exc:
            logger.exception("AI analysis failed for alert %s", alert_id)
            result["ai_analysis"] = {"error": str(exc)}

        # Optional incident creation
        if create_incident and alert.severity >= 10:
            incident = await self._create_incident_from_alert(alert, result.get("ai_analysis", {}))
            result["incident"] = {"id": incident.id, "name": incident.name}

        await self.db.commit()
        return result

    async def _lookup_mitre(self, technique_id: str) -> dict | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(MITRETechnique).where(MITRETechnique.technique_id == technique_id)
        )
        technique = result.scalar_one_or_none()
        if not technique:
            return None
        return {
            "technique_id": technique.technique_id,
            "name": technique.name,
            "tactic": technique.tactic,
            "description": technique.description,
            "detection_status": technique.detection_status,
        }

    async def _create_incident_from_alert(self, alert: Alert, ai_analysis: dict) -> Incident:
        name = f"{alert.title or 'Alert'} - {alert.id}"
        severity = IncidentSeverity.HIGH.value
        if alert.severity >= 13:
            severity = IncidentSeverity.CRITICAL.value
        elif alert.severity >= 7:
            severity = IncidentSeverity.MEDIUM.value
        elif alert.severity >= 4:
            severity = IncidentSeverity.LOW.value

        incident = Incident(
            name=name,
            description=ai_analysis.get("summary") or json.dumps({"alert_id": alert.id}),
            severity=severity,
            status=IncidentStatus.OPEN.value,
        )
        self.db.add(incident)
        await self.db.flush()
        incident.alerts.append(alert)
        await self.db.commit()
        await self.db.refresh(incident)
        logger.info("Created incident %d from alert %d", incident.id, alert.id)
        return incident
