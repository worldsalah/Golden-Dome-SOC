import asyncio
import logging
from typing import Any

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

from app.config.settings import get_settings
from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError

logger = logging.getLogger(__name__)


class WazuhVulnerabilitiesClient:
    """Wrapper for Wazuh vulnerability data via OpenSearch (wazuh-states-vulnerabilities index)."""

    def __init__(self, client: WazuhApiClient | None = None):
        self.client = client or WazuhApiClient()
        self.settings = self.client.settings or get_settings()
        self._os_client: OpenSearch | None = None

    def _get_os_client(self) -> OpenSearch:
        if self._os_client is None:
            self._os_client = OpenSearch(
                hosts=[self.settings.OPENSEARCH_URL],
                http_auth=(
                    self.settings.OPENSEARCH_USERNAME,
                    self.settings.OPENSEARCH_PASSWORD,
                ),
                verify_certs=self.settings.OPENSEARCH_VERIFY_SSL,
                ssl_show_warn=False,
            )
        return self._os_client

    async def list(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Query the wazuh-states-vulnerabilities-* index in OpenSearch directly."""
        os_client = self._get_os_client()
        must: list[dict[str, Any]] = []
        if agent_id:
            must.append({"term": {"agent.id": agent_id}})

        body: dict[str, Any] = {
            "size": limit,
            "from": offset,
            "query": {"bool": {"must": must}} if must else {"match_all": {}},
        }

        try:
            response = await asyncio.to_thread(
                os_client.search, index="wazuh-states-vulnerabilities-*", body=body
            )
        except OpenSearchException as exc:
            logger.error("OpenSearch vulnerability query failed: %s", exc)
            return {"data": [], "total": 0, "error": str(exc)}

        hits = response.get("hits", {}).get("hits", [])
        total = response.get("hits", {}).get("total", {}).get("value", 0)

        items = []
        for hit in hits:
            src = hit.get("_source", {})
            vuln = src.get("vulnerability", {})
            pkg = src.get("package", {})
            agent = src.get("agent", {})
            host = src.get("host", {})
            items.append({
                "id": hit.get("_id", ""),
                "cve": vuln.get("id", ""),
                "title": vuln.get("description", "")[:200],
                "description": vuln.get("description", ""),
                "severity": vuln.get("severity", "Unknown"),
                "cvss3_score": vuln.get("cvss3", {}).get("base_score") if isinstance(vuln.get("cvss3"), dict) else vuln.get("score"),
                "package_name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "architecture": pkg.get("architecture", ""),
                "condition": vuln.get("condition", ""),
                "agent_id": agent.get("id", ""),
                "agent_name": agent.get("name", ""),
                "os": host.get("os", {}).get("full", ""),
                "references": vuln.get("references", []),
            })

        return {"data": items, "total": total}

    async def close(self) -> None:
        await self.client.close()
