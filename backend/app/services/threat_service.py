import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ThreatIntelligence


from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)


class ThreatService:
    """Service for threat intelligence lookups and enrichment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_ip_reputation(self, ip_address: str) -> ThreatIntelligence | None:
        result = await self.db.execute(
            select(ThreatIntelligence)
            .where(ThreatIntelligence.indicator == ip_address)
            .where(ThreatIntelligence.type == "ip")
        )
        return result.scalar_one_or_none()

    async def add_indicator(
        self,
        indicator: str,
        type: str,
        source: str,
        reputation_score: int,
        country: str | None = None,
        malware: str | None = None,
    ) -> ThreatIntelligence:
        ti = ThreatIntelligence(
            indicator=indicator,
            type=type,
            source=source,
            reputation_score=reputation_score,
            country=country,
            malware=malware,
            last_checked=utc_now(),
        )
        self.db.add(ti)
        await self.db.commit()
        await self.db.refresh(ti)
        logger.info("Added threat intel indicator: %s (%s)", indicator, type)
        return ti

    async def enrich_ip(self, ip_address: str) -> dict:
        ti = await self.check_ip_reputation(ip_address)
        if ti:
            return {
                "indicator": ti.indicator,
                "type": ti.type,
                "source": ti.source,
                "reputation_score": ti.reputation_score,
                "country": ti.country,
                "malware": ti.malware,
                "last_checked": ti.last_checked.isoformat() if ti.last_checked else None,
            }
        return {
            "indicator": ip_address,
            "type": "ip",
            "source": "local",
            "reputation_score": 0,
            "country": None,
            "malware": None,
            "last_checked": None,
        }

    async def cleanup_stale_indicators(self, days: int = 90) -> int:
        cutoff = utc_now() - timedelta(days=days)
        result = await self.db.execute(
            select(ThreatIntelligence).where(ThreatIntelligence.last_checked < cutoff)
        )
        stale = result.scalars().all()
        for indicator in stale:
            await self.db.delete(indicator)
        await self.db.commit()
        logger.info("Cleaned up %d stale threat intelligence indicators", len(stale))
        return len(stale)
