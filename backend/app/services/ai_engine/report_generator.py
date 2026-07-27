import json
import logging
from datetime import datetime
from io import BytesIO
from typing import Any

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, Asset, Incident, IncidentTimeline, User
from app.services.ai_engine.knowledge_base import KnowledgeBase
from app.services.ai_engine.model_manager import ModelManager
from app.services.ai_engine.prompts import INCIDENT_REPORT_PROMPT


from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)


class IncidentReportGenerator:
    """Generate structured SOC incident reports in Markdown and PDF."""

    def __init__(self, db: AsyncSession, model: ModelManager | None = None):
        self.db = db
        self.model = model or ModelManager()

    async def generate(self, incident: Incident) -> dict[str, Any]:
        await self.db.refresh(incident, ['alerts', 'ai_analyses'])
        alerts = await self._alerts_for(incident)
        timeline = await self._timeline_for(incident)
        analyses = [a.__dict__ for a in incident.ai_analyses]
        threat_intel = await self._threat_intel_for(alerts)

        context = {
            "incident": {
                "id": incident.id,
                "name": incident.name,
                "severity": incident.severity,
                "status": incident.status,
                "description": incident.description,
            },
            "alerts": [self._alert_dict(a) for a in alerts],
            "timeline": [
                {"action": t.action, "note": t.note, "timestamp": t.timestamp.isoformat()}
                for t in timeline
            ],
            "analyses": analyses,
            "threat_intel": threat_intel,
            "risk_score": None,  # populated by caller if desired
        }

        prompt = INCIDENT_REPORT_PROMPT.substitute(
            incident=json.dumps(context["incident"], default=str, indent=2),
            alerts=json.dumps(context["alerts"], default=str, indent=2),
            timeline=json.dumps(context["timeline"], default=str, indent=2),
            analyses=json.dumps(context["analyses"], default=str, indent=2),
            threat_intel=json.dumps(context["threat_intel"], default=str, indent=2),
            risk_score=json.dumps(context["risk_score"], default=str),
        )

        llm_response = await self.model.generate(prompt=prompt, system=None, format="json")
        parsed = self._safe_json_parse(llm_response["raw"])

        if not parsed or "title" not in parsed:
            # Build a deterministic fallback report when the LLM response is missing required fields
            parsed = self._fallback_report(incident, alerts, timeline, threat_intel)

        return {
            "report": parsed,
            "llm_source": llm_response.get("source", "unknown"),
            "generated_at": utc_now().isoformat(),
        }

    def to_markdown(self, report: dict[str, Any]) -> str:
        lines = [
            f"# {report.get('title', 'SOC Incident Report')}",
            "",
            f"**Severity:** {report.get('severity', 'N/A')}  ",
            f"**Generated:** {utc_now().isoformat()}  ",
            "",
            "## Executive Summary",
            "",
            report.get("summary", "No summary provided."),
            "",
            "## Affected Assets",
            "",
        ]
        for asset in report.get("affected_assets", []):
            lines.append(f"- {asset}")
        lines.extend(["", "## Indicators of Compromise", ""])
        for ioc in report.get("indicators_of_compromise", []):
            lines.append(f"- {ioc}")
        lines.extend(["", "## MITRE ATT&CK Mapping", ""])
        for mapping in report.get("mitre_mapping", []):
            lines.append(f"- {mapping.get('tactic')} / {mapping.get('technique')} ({mapping.get('technique_id')})")
        lines.extend(["", "## Investigation Performed", ""])
        for step in report.get("investigation_performed", []):
            lines.append(f"- {step}")
        lines.extend(["", "## Recommended Remediation", ""])
        for key in ["immediate", "short_term", "long_term"]:
            lines.append(f"### {key.replace('_', ' ').title()}")
            for item in report.get("recommended_remediation", {}).get(key, []):
                lines.append(f"- {item}")
        lines.extend(["", "## Lessons Learned", ""])
        for lesson in report.get("lessons_learned", []):
            lines.append(f"- {lesson}")
        return "\n".join(lines)

    def to_pdf(self, report: dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(report.get("title", "SOC Incident Report"), styles["Title"]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(f"Severity: {report.get('severity', 'N/A')}", styles["Normal"]))
        story.append(Paragraph(f"Generated: {utc_now().isoformat()}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        story.append(Paragraph(report.get("summary", ""), styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Indicators of Compromise", styles["Heading2"]))
        iocs = report.get("indicators_of_compromise", [])
        if iocs:
            data = [[Paragraph(str(ioc), styles["Normal"])] for ioc in iocs]
            table = Table(data, colWidths=[6 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Recommended Remediation", styles["Heading2"]))
        for key in ["immediate", "short_term", "long_term"]:
            story.append(Paragraph(key.replace("_", " ").title(), styles["Heading3"]))
            for item in report.get("recommended_remediation", {}).get(key, []):
                story.append(Paragraph(f"• {item}", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    async def _alerts_for(self, incident: Incident) -> list[Alert]:
        return list(incident.alerts)

    async def _timeline_for(self, incident: Incident) -> list[IncidentTimeline]:
        result = await self.db.execute(
            select(IncidentTimeline).where(IncidentTimeline.incident_id == incident.id)
        )
        return list(result.scalars().all())

    async def _threat_intel_for(self, alerts: list[Alert]) -> list[dict[str, Any]]:
        ips = {a.source_ip for a in alerts if a.source_ip}
        kb = KnowledgeBase()
        intel = []
        for ip in ips:
            intel.append({"indicator": ip, "type": "ip", "note": "Enrichment available via threat intelligence endpoints"})
        return intel

    def _alert_dict(self, alert: Alert) -> dict[str, Any]:
        return {
            "id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "source_ip": alert.source_ip,
            "destination_ip": alert.destination_ip,
            "mitre_technique": alert.mitre_technique,
        }

    def _safe_json_parse(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Attempt to strip markdown fences
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            try:
                return json.loads("\n".join(lines))
            except json.JSONDecodeError:
                return None
        return None

    def _fallback_report(self, incident: Incident, alerts: list[Alert], timeline: list[IncidentTimeline], threat_intel: list[dict[str, Any]]) -> dict[str, Any]:
        iocs = sorted({a.source_ip for a in alerts if a.source_ip})
        techniques = sorted({a.mitre_technique for a in alerts if a.mitre_technique})
        kb = KnowledgeBase()
        mitre = [kb.lookup_mitre(tid) for tid in techniques]
        return {
            "title": f"Incident Report: {incident.name}",
            "severity": incident.severity,
            "summary": (
                f"Incident {incident.name} contains {len(alerts)} linked alert(s). "
                "Manual investigation is required to confirm impact and scope."
            ),
            "timeline": [f"{t.timestamp.isoformat()} - {t.action}: {t.note}" for t in timeline],
            "affected_assets": sorted({a.title for a in alerts}),
            "indicators_of_compromise": iocs,
            "mitre_mapping": [
                {"tactic": m["tactic"], "technique": m["name"], "technique_id": tid}
                for tid, m in zip(techniques, mitre)
            ],
            "investigation_performed": [
                "Reviewed linked alerts and timeline.",
                "Identified observable indicators.",
                "Consulted internal MITRE knowledge base.",
            ],
            "recommended_remediation": {
                "immediate": ["Contain confirmed malicious activity."],
                "short_term": ["Perform root-cause analysis and eradicate persistence."],
                "long_term": ["Tune detections and document lessons learned."],
            },
            "lessons_learned": ["Ensure response actions are logged and reviewed."],
        }
