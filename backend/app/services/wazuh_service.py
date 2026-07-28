import json
import logging
from typing import Any

from app.config.settings import get_settings
from app.services.wazuh.agents import WazuhAgentsClient
from app.services.wazuh.alerts import WazuhAlertsClient
from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError
from app.services.wazuh.rules import WazuhRulesClient
from app.services.wazuh.vulnerabilities import WazuhVulnerabilitiesClient

logger = logging.getLogger(__name__)


class WazuhServiceError(Exception):
    """Custom exception for Wazuh service failures."""


class WazuhService:
    """High-level facade for the Wazuh Manager API and Wazuh Indexer (OpenSearch)."""

    def __init__(self, api_client: WazuhApiClient | None = None):
        self.api_client = api_client or WazuhApiClient()
        self.settings = self.api_client.settings or get_settings()
        self.alerts_client = WazuhAlertsClient()
        self.agents_client = WazuhAgentsClient(self.api_client)
        self.vulnerabilities_client = WazuhVulnerabilitiesClient(self.api_client)
        self.rules_client = WazuhRulesClient(self.api_client)

    async def _authenticate(self) -> str:
        """Backward-compatible wrapper for tests and legacy code."""
        return await self.api_client.authenticate()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Thin wrapper around the low-level API client to keep old code working."""
        try:
            return await self.api_client.request(method, endpoint, params=params, json_data=json_data)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_agents(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        try:
            return await self.agents_client.list(limit=limit, offset=offset)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_agent_details(self, agent_id: str) -> dict[str, Any]:
        try:
            return await self.agents_client.get(agent_id)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_vulnerabilities(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        try:
            return await self.vulnerabilities_client.list(
                agent_id=agent_id, limit=limit, offset=offset
            )
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_alerts(
        self,
        size: int = 100,
        severity: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self.alerts_client.get_alerts(
                size=size,
                severity=severity,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_security_events(
        self,
        size: int = 100,
        rule_id: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self.alerts_client.get_security_events(size=size, rule_id=rule_id)
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_rules(
        self,
        limit: int = 500,
        offset: int = 0,
        group: str | None = None,
        rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            return await self.rules_client.list(
                limit=limit, offset=offset, group=group, rule_ids=rule_ids
            )
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_rule_stats(
        self,
        rule_ids: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        try:
            return await self.alerts_client.get_rule_stats(
                rule_ids=rule_ids, start_time=start_time, end_time=end_time
            )
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def normalize_alert(self, raw_alert: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw Wazuh/OpenSearch alert into the platform schema."""
        rule = raw_alert.get("rule", {}) or {}
        agent = raw_alert.get("agent", {}) or {}
        data = raw_alert.get("data", {}) or {}
        source = data.get("srcip") or raw_alert.get("srcip") or agent.get("ip")
        destination = data.get("dstip") or raw_alert.get("dstip")

        mitre = rule.get("mitre", {}) or {}
        techniques = mitre.get("id", [])
        if isinstance(techniques, str):
            techniques = [techniques]
        tactics = mitre.get("tactic", [])
        if isinstance(tactics, str):
            tactics = [tactics]

        return {
            "wazuh_alert_id": str(raw_alert.get("id", "")) or str(hash(json.dumps(raw_alert, sort_keys=True))),
            "title": rule.get("description", "Wazuh Alert"),
            "description": rule.get("comment", ""),
            "severity": int(rule.get("level", 1)),
            "source_ip": source,
            "destination_ip": destination,
            "rule_id": str(rule.get("id", "")),
            "mitre_technique": techniques[0] if techniques else None,
            "mitre_tactic": tactics[0] if tactics else None,
            "status": "new",
            "raw_log": json.dumps(raw_alert),
            "timestamp": raw_alert.get("timestamp"),
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
        }
