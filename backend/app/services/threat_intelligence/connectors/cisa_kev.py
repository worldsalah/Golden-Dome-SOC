import logging
from datetime import timedelta
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)


class CISAKEVConnector(BaseConnector):
    """CISA Known Exploited Vulnerabilities catalog connector."""

    @property
    def name(self) -> str:
        return "cisa_kev"

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._catalog_url = "https://api.cisa.gov/known-exploited-vulnerabilities/catalog"
        self._catalog: dict[str, dict[str, Any]] | None = None
        self._fetched_at: Any = None

    async def _fetch_catalog(self) -> dict[str, dict[str, Any]]:
        if self._catalog is not None and self._fetched_at is not None:
            if utc_now() - self._fetched_at < timedelta(hours=24):
                return self._catalog
        try:
            response = await self._retryable_get(self._catalog_url)
            if response.status_code == 200:
                data = response.json()
                catalog = {}
                for entry in data.get("vulnerabilities", []):
                    cve_id = entry.get("cveID")
                    if cve_id:
                        catalog[cve_id.lower()] = entry
                self._catalog = catalog
                self._fetched_at = utc_now()
                return catalog
        except Exception as exc:
            logger.debug("CISA KEV catalog fetch failed: %s", exc)
            self._healthy = False
        return self._catalog or {}

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        if ioc_type != "cve":
            return self._normalize_common()
        catalog = await self._fetch_catalog()
        entry = catalog.get(ioc.lower())
        if entry:
            return {
                "provider": self.name,
                "provider_score": 100,
                "provider_reference": entry.get("notes"),
                "raw_data": entry,
                "malicious": True,
                "threat_category": "exploited_vulnerability",
                "cisa_kev": True,
            }
        return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": self._healthy}
