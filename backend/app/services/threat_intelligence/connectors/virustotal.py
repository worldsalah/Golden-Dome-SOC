import logging
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class VirusTotalConnector(BaseConnector):
    """VirusTotal file hash and URL reputation connector."""

    @property
    def name(self) -> str:
        return "virustotal"

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        if not self.api_key or ioc_type not in ("hash", "url", "domain", "ip"):
            return self._normalize_common()
        try:
            if ioc_type == "hash":
                url = f"https://www.virustotal.com/api/v3/files/{ioc}"
            elif ioc_type == "ip":
                url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
            elif ioc_type == "domain":
                url = f"https://www.virustotal.com/api/v3/domains/{ioc}"
            else:  # url
                import base64
                encoded = base64.urlsafe_b64encode(ioc.encode()).decode().strip("=")
                url = f"https://www.virustotal.com/api/v3/urls/{encoded}"

            response = await self._retryable_get(url, headers={"x-apikey": self.api_key})
            if response.status_code == 200:
                attrs = response.json().get("data", {}).get("attributes", {})
                stats = attrs.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values()) or 1
                score = int((malicious / total) * 100)
                classification = attrs.get("popular_threat_classification", {})
                threat_label = classification.get("suggested_threat_label")
                return {
                    "provider": self.name,
                    "provider_score": score,
                    "provider_reference": f"https://www.virustotal.com/gui/{ioc_type}/{ioc}",
                    "raw_data": attrs,
                    "malicious": score >= 10,
                    "malware": threat_label,
                    "reputation_score": score,
                }
        except Exception as exc:
            logger.debug("VirusTotal enrichment failed for %s: %s", ioc, exc)
            self._healthy = False
        return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": self._healthy, "api_key_configured": bool(self.api_key)}
