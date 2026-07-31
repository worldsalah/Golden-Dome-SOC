import json
import logging
from typing import Any, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.models import Alert, Asset, AssetVulnerability, Incident, RiskScore, ThreatIntelligence
from app.security.tenant import tenant_filter
from app.services.ai_engine.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class RiskScorer:
    """Explainable risk scoring for alerts, assets, and incidents."""

    def __init__(self, db: AsyncSession, settings: Settings | None = None, tenant_id: int | None = None):
        self.db = db
        self.tenant_id = tenant_id
        self.settings = settings or get_settings()
        self.weights = {
            "severity": self.settings.RISK_WEIGHT_SEVERITY,
            "criticality": self.settings.RISK_WEIGHT_CRITICALITY,
            "vulnerability": self.settings.RISK_WEIGHT_VULNERABILITY,
            "threat_intel": self.settings.RISK_WEIGHT_THREAT_INTEL,
            "historical": self.settings.RISK_WEIGHT_HISTORICAL,
        }

    def classification(self, score: int) -> str:
        if score <= 25:
            return "low"
        if score <= 50:
            return "medium"
        if score <= 75:
            return "high"
        return "critical"

    async def calculate_alert_risk(self, alert: Alert) -> tuple[int, dict[str, Any]]:
        severity_score = min((alert.severity / 15) * 100, 100)

        asset_score = 0.0
        criticality = 0
        if alert.asset_id:
            asset = await self.db.get(Asset, alert.asset_id)
            if asset:
                criticality = asset.criticality or 0
                asset_score = criticality

        vuln_score = await self._max_vuln_score(alert.asset_id)
        ti_score = await self._threat_intel_score(alert.source_ip)
        historical_score = await self._historical_score(alert.asset_id, alert.source_ip)

        score = int(
            severity_score * self.weights["severity"]
            + asset_score * self.weights["criticality"]
            + vuln_score * self.weights["vulnerability"]
            + ti_score * self.weights["threat_intel"]
            + historical_score * self.weights["historical"]
        )
        score = max(0, min(score, 100))

        reason = {
            "severity": {"value": round(severity_score, 1), "weight": self.weights["severity"], "raw": alert.severity},
            "asset_criticality": {"value": criticality, "weight": self.weights["criticality"]},
            "vulnerability": {"value": round(vuln_score, 1), "weight": self.weights["vulnerability"]},
            "threat_intelligence": {"value": round(ti_score, 1), "weight": self.weights["threat_intel"]},
            "historical": {"value": round(historical_score, 1), "weight": self.weights["historical"]},
            "classification": self.classification(score),
        }
        return score, reason

    async def calculate_asset_risk(self, asset: Asset) -> tuple[int, dict[str, Any]]:
        # Reuse alert-based calculation using a synthetic aggregate alert.
        result = await self.db.execute(
            select(func.avg(Alert.severity), func.count(Alert.id))
            .where(Alert.asset_id == asset.id)
            .where(Alert.status.in_(["new", "acknowledged", "investigating"]))
        )
        avg_sev, count = result.one()
        severity_score = min(((avg_sev or 0) / 15) * 100, 100)

        vuln_score = await self._max_vuln_score(asset.id)
        ti_score = await self._threat_intel_score(asset.ip_address)
        historical_score = min(count * 10, 100)

        score = int(
            severity_score * self.weights["severity"]
            + (asset.criticality or 0) * self.weights["criticality"]
            + vuln_score * self.weights["vulnerability"]
            + ti_score * self.weights["threat_intel"]
            + historical_score * self.weights["historical"]
        )
        score = max(0, min(score, 100))

        reason = {
            "alert_count": count,
            "average_severity": round(severity_score, 1),
            "asset_criticality": asset.criticality,
            "vulnerability": round(vuln_score, 1),
            "threat_intelligence": round(ti_score, 1),
            "historical": round(historical_score, 1),
            "classification": self.classification(score),
        }
        return score, reason

    async def calculate_incident_risk(self, incident: Incident) -> tuple[int, dict[str, Any]]:
        severity_map = {"low": 20, "medium": 50, "high": 80, "critical": 100}
        severity_score = severity_map.get(incident.severity or "medium", 50)

        # Aggregate linked alert risk
        total_alert_score = 0
        max_alert_score = 0
        for alert in incident.alerts:
            alert_score, _ = await self.calculate_alert_risk(alert)
            total_alert_score += alert_score
            max_alert_score = max(max_alert_score, alert_score)
        avg_alert_score = total_alert_score / len(incident.alerts) if incident.alerts else 0

        score = int(severity_score * 0.4 + max_alert_score * 0.4 + avg_alert_score * 0.2)
        score = max(0, min(score, 100))

        reason = {
            "severity": incident.severity,
            "max_alert_score": max_alert_score,
            "average_alert_score": round(avg_alert_score, 1),
            "classification": self.classification(score),
        }
        return score, reason

    async def store_risk_score(self, target_type: str, target_id: int, score: int, reason: dict[str, Any]) -> RiskScore:
        record = RiskScore(
            target_type=target_type,
            target_id=target_id,
            tenant_id=self.tenant_id,
            score=score,
            reason=json.dumps(reason),
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def _max_vuln_score(self, asset_id: int | None) -> float:
        if not asset_id:
            return 0.0
        stmt = select(AssetVulnerability.cvss_score).where(AssetVulnerability.asset_id == asset_id)
        filt = tenant_filter(AssetVulnerability, self.tenant_id)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        scores = [s for s in result.scalars().all() if s is not None]
        if not scores:
            return 0.0
        return max(scores) * 10  # CVSS 0-10 -> 0-100

    async def _threat_intel_score(self, indicator: str | None) -> float:
        if not indicator:
            return 0.0
        stmt = select(ThreatIntelligence.reputation_score).where(ThreatIntelligence.indicator == indicator).order_by(ThreatIntelligence.last_checked.desc())
        filt = tenant_filter(ThreatIntelligence, self.tenant_id)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        scores = result.scalars().all()
        return max(scores) if scores else 0.0

    def _tenant_filter_stmt(self, stmt, model):
        filt = tenant_filter(model, self.tenant_id)
        if filt is not None:
            stmt = stmt.where(filt)
        return stmt

    async def _historical_score(self, asset_id: int | None, source_ip: str | None) -> float:
        score = 0
        if asset_id:
            stmt = self._tenant_filter_stmt(
                select(func.count(Alert.id)).where(Alert.asset_id == asset_id),
                Alert,
            )
            count_result = await self.db.execute(stmt)
            score += min(count_result.scalar_one() * 5, 50)
        if source_ip:
            stmt = self._tenant_filter_stmt(
                select(func.count(Alert.id)).where(Alert.source_ip == source_ip),
                Alert,
            )
            count_result = await self.db.execute(stmt)
            score += min(count_result.scalar_one() * 5, 50)
        return score

    async def get_top_risky_assets(self, limit: int = 10) -> Sequence[Asset]:
        stmt = select(Asset).order_by(desc(Asset.risk_score)).limit(limit)
        filt = tenant_filter(Asset, self.tenant_id)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        return result.scalars().all()
