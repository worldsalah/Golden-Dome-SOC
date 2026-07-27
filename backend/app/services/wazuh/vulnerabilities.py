import logging
from typing import Any

from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError

logger = logging.getLogger(__name__)


class WazuhVulnerabilitiesClient:
    """Wrapper for Wazuh vulnerability endpoints."""

    def __init__(self, client: WazuhApiClient | None = None):
        self.client = client or WazuhApiClient()

    async def list(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if agent_id:
            params["agents_list"] = agent_id
        try:
            return await self.client.request("GET", "/vulnerability", params=params)
        except WazuhApiClientError:
            raise
        except Exception as exc:
            logger.exception("Failed to list Wazuh vulnerabilities")
            raise WazuhApiClientError(str(exc)) from exc

    async def close(self) -> None:
        await self.client.close()
