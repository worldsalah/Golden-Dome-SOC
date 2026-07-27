import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, Asset, AssetVulnerability, Incident

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Gathers contextual data around an alert for the AI analysis pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_alert_context(self, alert: Alert) -> dict[str, Any]:
        asset_info = await self._asset_context(alert.asset_id)
        incident_info = await self._incident_context(alert.id)
        vuln_info = await self._vulnerability_context(alert.asset_id)

        return {
            "title": alert.title,
            "severity": alert.severity,
            "source_ip": alert.source_ip or "N/A",
            "destination_ip": alert.destination_ip or "N/A",
            "rule_id": alert.rule_id or "N/A",
            "mitre_technique": alert.mitre_technique or "N/A",
            "status": alert.status,
            "asset": asset_info,
            "related_incidents": incident_info,
            "vulnerabilities": vuln_info,
            "raw_log": (alert.raw_log or "")[:2000],
        }

    async def _asset_context(self, asset_id: int | None) -> dict[str, Any]:
        if not asset_id:
            return {"info": "No asset linked to this alert"}
        asset = await self.db.get(Asset, asset_id)
        if not asset:
            return {"info": f"Asset {asset_id} not found"}
        return {
            "id": asset.id,
            "hostname": asset.hostname,
            "ip_address": asset.ip_address,
            "type": asset.type,
            "os": asset.operating_system,
            "criticality": asset.criticality,
            "risk_score": asset.risk_score,
        }

    async def _incident_context(self, alert_id: int) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(Incident)
            .join(Incident.alerts)
            .where(Alert.id == alert_id)
        )
        incidents = result.scalars().all()
        return [
            {"id": inc.id, "name": inc.name, "severity": inc.severity, "status": inc.status}
            for inc in incidents
        ]

    async def _vulnerability_context(self, asset_id: int | None) -> list[dict[str, Any]]:
        if not asset_id:
            return []
        result = await self.db.execute(
            select(AssetVulnerability)
            .where(AssetVulnerability.asset_id == asset_id)
            .order_by(AssetVulnerability.cvss_score.desc())
        )
        vulns = result.scalars().all()
        return [
            {
                "cve": v.cve,
                "severity": v.severity,
                "cvss_score": v.cvss_score,
                "description": (v.description or "")[:200],
            }
            for v in vulns[:5]
        ]

    @staticmethod
    def context_to_text(context: dict[str, Any]) -> str:
        return json.dumps(context, indent=2, default=str)
