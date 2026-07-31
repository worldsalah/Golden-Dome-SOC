"""FortiGate firewall connector."""

from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry


@ConnectorRegistry.register
class FortiGateConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="fortigate",
        category="security",
        display_name="FortiGate Firewall",
        description="Fortinet FortiGate next-gen firewall integration for log collection and threat blocking.",
        icon="fortinet",
        config_schema={
            "host": {"type": "string", "required": True, "label": "FortiGate IP"},
            "api_token": {"type": "password", "required": True, "label": "API Token"},
            "verify_ssl": {"type": "boolean", "required": False, "default": True, "label": "Verify SSL certificate"},
        },
        supported_actions=["collect_logs", "block_ip", "list_policies"],
    )

    async def test_connection(self) -> dict[str, Any]:
        host = self.config.get("host")
        token = self.config.get("api_token", "")
        verify = self.config.get("verify_ssl", True)
        try:
            async with httpx.AsyncClient(verify=verify, timeout=10) as client:
                resp = await client.get(
                    f"https://{host}/api/v2/cmdb/system/status",
                    headers={"Authorization": f"Bearer {token}"},
                )
                return {"healthy": resp.status_code == 200, "status": "connected" if resp.status_code == 200 else "auth_failed"}
        except Exception as e:
            return {"healthy": False, "status": str(e)}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "FortiGate logs collected via syslog/OpenSearch"}
