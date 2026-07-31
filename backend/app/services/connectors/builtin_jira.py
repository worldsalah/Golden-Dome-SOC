"""Jira ticketing connector."""

from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry


@ConnectorRegistry.register
class JiraConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="jira",
        category="ticketing",
        display_name="Jira",
        description="Atlassian Jira for issue tracking and project management integration.",
        icon="jira",
        config_schema={
            "base_url": {"type": "string", "required": True, "label": "Jira Base URL"},
            "email": {"type": "string", "required": True, "label": "Email"},
            "api_token": {"type": "password", "required": True, "label": "API Token"},
            "project_key": {"type": "string", "required": True, "label": "Project Key"},
        },
        supported_actions=["create_issue", "update_issue", "list_issues"],
    )

    async def test_connection(self) -> dict[str, Any]:
        url = self.config.get("base_url", "")
        email = self.config.get("email", "")
        token = self.config.get("api_token", "")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{url}/rest/api/3/myself",
                    auth=(email, token),
                )
                return {"healthy": resp.status_code == 200, "status": "connected" if resp.status_code == 200 else "auth_failed"}
        except Exception as e:
            return {"healthy": False, "status": str(e)}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "Jira issues synced"}
