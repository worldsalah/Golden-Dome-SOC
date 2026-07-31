import logging
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class AlienVaultOTXConnector(BaseConnector):
    """AlienVault Open Threat Exchange pulse indicator connector."""

    @property
    def name(self) -> str:
        return "alienvault_otx"

    def _endpoint(self, ioc: str, ioc_type: str) -> str | None:
        base = "https://otx.alienvault.com/api/v1/indicators"
        if ioc_type == "ip":
            return f"{base}/IPv4/{ioc}/general"
        if ioc_type == "domain":
            return f"{base}/domain/{ioc}/general"
        if ioc_type == "hash":
            return f"{base}/file/{ioc}/general"
        if ioc_type == "url":
            return f"{base}/url/{ioc}/general"
        return None

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        # OTX is a free community API that works without a key for basic queries
        endpoint = self._endpoint(ioc, ioc_type)
        if not endpoint:
            return self._normalize_common()
        try:
            headers = {}
            if self.api_key:
                headers["X-OTX-API-KEY"] = self.api_key
            response = await self._retryable_get(
                endpoint,
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                pulse_count = data.get("pulse_info", {}).get("count", 0)
                score = min(pulse_count * 10, 100)
                return {
                    "provider": self.name,
                    "provider_score": score,
                    "provider_reference": f"https://otx.alienvault.com/indicator/{ioc_type}/{ioc}",
                    "raw_data": data,
                    "reputation_score": score,
                    "malicious": score >= 30,
                    "country": (data.get("country") or {}).get("country_code"),
                    "asn": data.get("asn"),
                }
        except Exception as exc:
            logger.debug("AlienVault OTX enrichment failed for %s: %s", ioc, exc)
            self._healthy = False
        return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": self._healthy, "api_key_configured": bool(self.api_key)}
