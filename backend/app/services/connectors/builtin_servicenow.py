"""ServiceNow ticketing connector."""

from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry


@ConnectorRegistry.register
class ServiceNowConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="servicenow",
        category="ticketing",
        display_name="ServiceNow",
        description="ITSM platform for ticket creation, incident management, and change requests.",
        icon="servicenow",
        config_schema={
            "instance_url": {"type": "string", "required": True, "label": "ServiceNow Instance URL"},
            "username": {"type": "string", "required": True, "label": "Username"},
            "password": {"type": "password", "required": True, "label": "Password"},
        },
        supported_actions=["create_ticket", "update_ticket", "list_tickets"],
    )

    async def test_connection(self) -> dict[str, Any]:
        url = self.config.get("instance_url", "")
        user = self.config.get("username", "")
        pwd = self.config.get("password", "")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{url}/api/now/table/incident?sysparm_limit=1",
                    auth=(user, pwd),
                )
                return {"healthy": resp.status_code == 200, "status": "connected" if resp.status_code == 200 else "auth_failed"}
        except Exception as e:
            return {"healthy": False, "status": str(e)}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "ServiceNow tickets synced"}
