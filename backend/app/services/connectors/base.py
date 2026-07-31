"""Connector framework — plugin architecture for all integrations.

Connectors are registered via entry points or explicit registration.
Each connector type extends BaseConnector and implements test_connection() and collect().
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel


class ConnectorManifest(BaseModel):
    """Describes a connector type's metadata and configuration schema."""
    type: str
    category: str
    display_name: str
    description: str
    icon: str | None = None
    config_schema: dict[str, Any] = {}
    supported_actions: list[str] = []


class BaseConnector(ABC):
    """Abstract base class for all connectors."""
    manifest: ClassVar[ConnectorManifest]

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test the connection and return health status."""
        ...

    @abstractmethod
    async def collect(self) -> dict[str, Any]:
        """Collect data from the connected source."""
        ...


class ConnectorRegistry:
    """Registry for connector types — allows adding integrations without modifying core."""

    _connectors: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_class: type[BaseConnector]) -> type[BaseConnector]:
        """Register a connector class. Can be used as a decorator."""
        connector_type = connector_class.manifest.type
        cls._connectors[connector_type] = connector_class
        return connector_class

    @classmethod
    def get(cls, connector_type: str) -> type[BaseConnector] | None:
        return cls._connectors.get(connector_type)

    @classmethod
    def list_all(cls) -> list[ConnectorManifest]:
        return [c.manifest for c in cls._connectors.values()]

    @classmethod
    def list_by_category(cls, category: str) -> list[ConnectorManifest]:
        return [c.manifest for c in cls._connectors.values() if c.manifest.category == category]

    @classmethod
    def create(cls, connector_type: str, config: dict[str, Any] | None = None) -> BaseConnector | None:
        connector_class = cls.get(connector_type)
        if not connector_class:
            return None
        return connector_class(config=config)
