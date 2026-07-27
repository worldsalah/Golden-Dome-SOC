import logging
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class AbuseIPDBConnector(BaseConnector):
    """AbuseIPDB IP reputation connector."""

    @property
    def name(self) -> str:
        return "abuseipdb"

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        if ioc_type != "ip" or not self.api_key:
            return self._normalize_common()
        try:
            response = await self._retryable_get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ioc, "maxAgeInDays": 90},
                headers={"Key": self.api_key, "Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            score = int(data.get("abuseConfidenceScore", 0))
            return {
                "provider": self.name,
                "provider_score": score,
                "provider_reference": f"https://www.abuseipdb.com/check/{ioc}",
                "raw_data": data,
                "country": data.get("countryCode"),
                "asn": data.get("isp"),
                "isp": data.get("isp"),
                "threat_category": data.get("usageType"),
                "malicious": score >= 25,
            }
        except Exception as exc:
            logger.debug("AbuseIPDB enrichment failed for %s: %s", ioc, exc)
            self._healthy = False
            return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": self._healthy, "api_key_configured": bool(self.api_key)}
