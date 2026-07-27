import asyncio
import logging
from typing import Any

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class WazuhAlertsClientError(Exception):
    """Custom exception for Wazuh Indexer query failures."""


class WazuhAlertsClient:
    """Client for querying Wazuh alerts from the OpenSearch indexer."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: OpenSearch | None = None

    def _get_client(self) -> OpenSearch:
        if self._client is None:
            self._client = OpenSearch(
                hosts=[self.settings.OPENSEARCH_URL],
                http_auth=(
                    self.settings.OPENSEARCH_USERNAME,
                    self.settings.OPENSEARCH_PASSWORD,
                ),
                verify_certs=self.settings.OPENSEARCH_VERIFY_SSL,
                ssl_show_warn=False,
            )
        return self._client

    async def query(
        self,
        index: str,
        size: int = 100,
        query: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        client = self._get_client()
        body: dict[str, Any] = {"size": size}
        if query:
            body["query"] = query
        if sort:
            body["sort"] = sort
        else:
            body["sort"] = [{"timestamp": {"order": "desc"}}]

        try:
            response = await asyncio.to_thread(client.search, index=index, body=body)
            hits = response.get("hits", {}).get("hits", [])
            return [hit.get("_source", {}) for hit in hits]
        except OpenSearchException as exc:
            logger.error("OpenSearch query failed: %s", exc)
            raise WazuhAlertsClientError("OpenSearch query failed") from exc

    async def get_alerts(
        self,
        size: int = 100,
        severity: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        must: list[dict[str, Any]] = []
        if severity is not None:
            must.append({"term": {"rule.level": severity}})
        if start_time or end_time:
            range_clause: dict[str, str] = {}
            if start_time:
                range_clause["gte"] = start_time
            if end_time:
                range_clause["lte"] = end_time
            must.append({"range": {"timestamp": range_clause}})

        query = {"bool": {"must": must}} if must else {"match_all": {}}
        return await self.query("wazuh-alerts-*", size=size, query=query)

    async def get_security_events(
        self,
        size: int = 100,
        rule_id: str | None = None,
    ) -> list[dict[str, Any]]:
        must: list[dict[str, Any]] = []
        if rule_id:
            must.append({"term": {"rule.id": rule_id}})
        query = {"bool": {"must": must}} if must else {"match_all": {}}
        return await self.query("wazuh-alerts-*,wazuh-archives-*", size=size, query=query)
