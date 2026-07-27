import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for threat intelligence providers.

    Each connector must implement ``name`` and ``enrich``. It is expected to
    return a normalized dictionary so that the enrichment orchestrator can
    merge results from multiple providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def __init__(self, api_key: str | None = None, timeout: float = 20.0):
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._healthy = True

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def enrich(self, ioc: str, ioc_type: str) -> dict[str, Any]:
        """Return a normalized enrichment result for the given IOC."""
        ...

    async def health(self) -> dict[str, Any]:
        """Quick health check for the provider. Subclasses may override."""
        return {"name": self.name, "healthy": self._healthy}

    def _normalize_common(self, provider_score: int | None = None) -> dict[str, Any]:
        return {
            "provider": self.name,
            "provider_score": provider_score,
            "provider_reference": None,
            "raw_data": {},
        }

    async def _retryable_get(self, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self.client.get(url, **kwargs)
                return response
            except Exception as exc:
                last_error = exc
                logger.debug("%s GET attempt %s failed: %s", self.name, attempt + 1, exc)
        self._healthy = False
        raise last_error or RuntimeError(f"{self.name} request failed")

    async def _retryable_post(self, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self.client.post(url, **kwargs)
                return response
            except Exception as exc:
                last_error = exc
                logger.debug("%s POST attempt %s failed: %s", self.name, attempt + 1, exc)
        self._healthy = False
        raise last_error or RuntimeError(f"{self.name} request failed")
