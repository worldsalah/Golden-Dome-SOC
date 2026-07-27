import logging
from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, Asset, AssetVulnerability

logger = logging.getLogger(__name__)


def severity_to_score(severity: str) -> int:
    mapping = {
        "critical": 100,
        "high": 80,
        "medium": 50,
        "low": 20,
        "informational": 0,
    }
    return mapping.get((severity or "").lower(), 30)


class RiskService:
    """Calculate asset risk scores based on multiple factors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_asset_risk(self, asset_id: int) -> int:
        asset = await self.db.get(Asset, asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        criticality = asset.criticality or 0

        # Alert severity contribution (max 100)
        alerts_result = await self.db.execute(
            select(Alert.severity)
            .where(Alert.asset_id == asset_id)
            .where(Alert.status.in_(["new", "acknowledged", "investigating"]))
        )
        severities: Sequence[int] = alerts_result.scalars().all()
        if severities:
            avg_alert_severity = sum(severities) / len(severities)
            # Wazuh rule levels go up to 15; scale to 100
            alert_score = min((avg_alert_severity / 15) * 100, 100)
        else:
            alert_score = 0

        # Vulnerability contribution (max 100)
        vuln_result = await self.db.execute(
            select(AssetVulnerability.severity)
            .where(AssetVulnerability.asset_id == asset_id)
        )
        vuln_scores = [severity_to_score(v) for v in vuln_result.scalars().all()]
        vuln_score = max(vuln_scores) if vuln_scores else 0

        # Threat intelligence contribution (placeholder: derive from source IP reputation)
        threat_score = await self._get_threat_score_for_asset(asset)

        # Weighted formula
        risk_score = (
            criticality * 0.30
            + alert_score * 0.35
            + vuln_score * 0.25
            + threat_score * 0.10
        )

        risk_score = max(0, min(int(risk_score), 100))
        asset.risk_score = risk_score
        await self.db.commit()
        await self.db.refresh(asset)
        logger.info("Calculated risk score for asset %s: %d", asset.hostname, risk_score)
        return risk_score

    async def _get_threat_score_for_asset(self, asset: Asset) -> int:
        # Future integration: query threat intelligence for asset IPs/domains
        # For now, return a default based on whether the asset has recent alerts
        alert_result = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.asset_id == asset.id)
        )
        count = alert_result.scalar_one()
        return min(count * 10, 100)

    async def calculate_all_asset_risks(self) -> dict[int, int]:
        result = await self.db.execute(select(Asset.id))
        scores = {}
        for (asset_id,) in result.all():
            try:
                scores[asset_id] = await self.calculate_asset_risk(asset_id)
            except Exception as exc:
                logger.warning("Failed to calculate risk for asset %s: %s", asset_id, exc)
        return scores

    async def get_top_risky_assets(self, limit: int = 10) -> Sequence[Asset]:
        result = await self.db.execute(
            select(Asset).order_by(desc(Asset.risk_score)).limit(limit)
        )
        return result.scalars().all()
