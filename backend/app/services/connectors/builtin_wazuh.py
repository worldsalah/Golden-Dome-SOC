"""Wazuh connector — SIEM/XDR integration."""

from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry


@ConnectorRegistry.register
class WazuhConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="wazuh",
        category="security",
        display_name="Wazuh SIEM",
        description="Open-source SIEM and XDR platform for threat detection, integrity monitoring, and compliance.",
        icon="wazuh",
        config_schema={
            "host": {"type": "string", "required": True, "label": "Wazuh Manager Host"},
            "port": {"type": "integer", "default": 55000, "label": "API Port"},
            "username": {"type": "string", "required": True, "label": "API Username"},
            "password": {"type": "password", "required": True, "label": "API Password"},
        },
        supported_actions=["collect_alerts", "list_agents", "agent_status"],
    )

    async def test_connection(self) -> dict[str, Any]:
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 55000)
        try:
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                resp = await client.get(f"https://{host}:{port}/security/user/authenticate")
                return {"healthy": resp.status_code in (200, 401), "status": "reachable"}
        except Exception as e:
            return {"healthy": False, "status": str(e)}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "Wazuh connector collects via sync_worker"}
