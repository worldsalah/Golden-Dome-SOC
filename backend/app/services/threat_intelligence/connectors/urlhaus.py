import logging
from typing import Any

from app.services.threat_intelligence.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class URLHausConnector(BaseConnector):
    """URLHaus malware distribution URL/host connector."""

    @property
    def name(self) -> str:
        return "urlhaus"

    def __init__(self, api_url: str = "https://urlhaus-api.abuse.ch/v1", timeout: float = 20.0):
        super().__init__(timeout=timeout)
        self.api_url = api_url

    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        try:
            if ioc_type in ("ip", "domain"):
                response = await self._retryable_post(
                    f"{self.api_url}/host",
                    data={"host": ioc},
                )
            elif ioc_type == "url":
                response = await self._retryable_post(
                    f"{self.api_url}/url",
                    data={"url": ioc},
                )
            else:
                return self._normalize_common()

            if response.status_code == 200:
                data = response.json()
                if data.get("urls") or data.get("query_status") == "ok":
                    return {
                        "provider": self.name,
                        "provider_score": 90,
                        "provider_reference": "https://urlhaus.abuse.ch/",
                        "raw_data": data,
                        "malicious": True,
                        "threat_category": "malware",
                    }
        except Exception as exc:
            logger.debug("URLHaus enrichment failed for %s: %s", ioc, exc)
            self._healthy = False
        return self._normalize_common()

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "healthy": self._healthy}
