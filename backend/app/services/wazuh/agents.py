import logging
from typing import Any

from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError

logger = logging.getLogger(__name__)


class WazuhAgentsClient:
    """Wrapper for Wazuh agent endpoints."""

    def __init__(self, client: WazuhApiClient | None = None):
        self.client = client or WazuhApiClient()

    async def list(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        try:
            return await self.client.request(
                "GET", "/agents", params={"limit": limit, "offset": offset}
            )
        except WazuhApiClientError:
            raise
        except Exception as exc:
            logger.exception("Failed to list Wazuh agents")
            raise WazuhApiClientError(str(exc)) from exc

    async def get(self, agent_id: str) -> dict[str, Any]:
        try:
            return await self.client.request("GET", "/agents", params={"agents_list": agent_id})
        except WazuhApiClientError:
            raise
        except Exception as exc:
            logger.exception("Failed to get Wazuh agent %s", agent_id)
            raise WazuhApiClientError(str(exc)) from exc

    async def close(self) -> None:
        await self.client.close()
