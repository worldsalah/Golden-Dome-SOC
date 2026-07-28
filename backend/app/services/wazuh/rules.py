import logging
from typing import Any

from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError

logger = logging.getLogger(__name__)


class WazuhRulesClient:
    """Wrapper for the Wazuh Manager /rules endpoints."""

    def __init__(self, client: WazuhApiClient | None = None):
        self.client = client or WazuhApiClient()

    async def list(
        self,
        limit: int = 500,
        offset: int = 0,
        group: str | None = None,
        rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """List rules loaded on the Wazuh Manager (built-in and custom)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if group:
            params["group"] = group
        if rule_ids:
            params["rule_ids"] = ",".join(rule_ids)
        try:
            return await self.client.request("GET", "/rules", params=params)
        except WazuhApiClientError:
            raise
        except Exception as exc:
            logger.exception("Failed to list Wazuh rules")
            raise WazuhApiClientError(str(exc)) from exc

    async def get_groups(self) -> dict[str, Any]:
        try:
            return await self.client.request("GET", "/rules/groups")
        except WazuhApiClientError:
            raise
        except Exception as exc:
            logger.exception("Failed to list Wazuh rule groups")
            raise WazuhApiClientError(str(exc)) from exc

    async def close(self) -> None:
        await self.client.close()
