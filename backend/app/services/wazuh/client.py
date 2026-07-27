import logging
from typing import Any

import httpx

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class WazuhApiClientError(Exception):
    """Custom exception for Wazuh Manager API client failures."""


class WazuhApiClient:
    """Low-level async client for the Wazuh Manager REST API."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                verify=self.settings.WAZUH_API_VERIFY_SSL,
                timeout=self.settings.WAZUH_API_TIMEOUT,
            )
        return self._client

    async def authenticate(self) -> str:
        """Obtain a JWT token from the Wazuh API."""
        client = await self._get_client()
        url = f"{self.settings.WAZUH_API_URL}/security/user/authenticate"
        try:
            response = await client.post(
                url,
                auth=(self.settings.WAZUH_API_USERNAME, self.settings.WAZUH_API_PASSWORD),
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("data", {}).get("token")
            if not token:
                raise WazuhApiClientError("Wazuh API token missing in response")
            self._token = token
            logger.info("Authenticated with Wazuh Manager API")
            return token
        except httpx.HTTPStatusError as exc:
            logger.error("Wazuh authentication failed: %s", exc.response.text)
            raise WazuhApiClientError(f"Wazuh authentication failed: {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.error("Wazuh API request error: %s", exc)
            raise WazuhApiClientError(f"Wazuh API unreachable: {exc}")

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request with automatic retry on 401."""
        if not self._token:
            await self.authenticate()

        client = await self._get_client()
        url = f"{self.settings.WAZUH_API_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
            )
            if response.status_code == 401:
                logger.warning("Wazuh token expired, re-authenticating")
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self._token}"
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Wazuh API error %s: %s", exc.response.status_code, exc.response.text)
            raise WazuhApiClientError(
                f"Wazuh API error: {exc.response.status_code} - {exc.response.text}"
            )
        except httpx.RequestError as exc:
            logger.error("Wazuh API request error: %s", exc)
            raise WazuhApiClientError(f"Wazuh API unreachable: {exc}")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
