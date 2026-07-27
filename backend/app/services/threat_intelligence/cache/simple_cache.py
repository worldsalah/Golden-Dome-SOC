import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class SimpleTTLCache:
    """In-memory TTL cache used when Redis is not available."""

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._store: dict[str, Any] = {}
        self._expires: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            exp = self._expires.get(key)
            if exp is None:
                return None
            if time.time() > exp:
                self._store.pop(key, None)
                self._expires.pop(key, None)
                return None
            return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            self._store[key] = value
            self._expires[key] = time.time() + (ttl or self.default_ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)
            self._expires.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
            self._expires.clear()
