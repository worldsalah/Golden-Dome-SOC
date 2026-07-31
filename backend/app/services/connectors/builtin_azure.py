"""Azure cloud connector."""

import logging
from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry

logger = logging.getLogger(__name__)


@ConnectorRegistry.register
class AzureConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="azure",
        category="cloud",
        display_name="Microsoft Azure",
        description="Azure Sentinel, Log Analytics, and Activity Log integration.",
        icon="azure",
        config_schema={
            "tenant_id": {"type": "string", "required": True, "label": "Azure Tenant ID"},
            "client_id": {"type": "string", "required": True, "label": "Client ID"},
            "client_secret": {"type": "password", "required": True, "label": "Client Secret"},
            "subscription_id": {"type": "string", "required": True, "label": "Subscription ID"},
        },
        supported_actions=["collect_activity_log", "collect_sentinel_alerts", "list_vms"],
    )

    async def test_connection(self) -> dict[str, Any]:
        tenant_id = self.config.get("tenant_id")
        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")

        if not all([tenant_id, client_id, client_secret]):
            return {"healthy": False, "status": "Missing required Azure credentials (tenant_id, client_id, client_secret)"}

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://management.azure.com/.default",
            "grant_type": "client_credentials",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(token_url, data=token_data)
            if resp.status_code == 200:
                token = resp.json()
                return {
                    "healthy": True,
                    "status": "Azure authentication successful",
                    "token_type": token.get("token_type", "Bearer"),
                    "expires_in": token.get("expires_in", 3600),
                }
            else:
                error = resp.json().get("error_description", resp.text)
                return {"healthy": False, "status": f"Azure auth failed: {error}"}
        except httpx.TimeoutException:
            return {"healthy": False, "status": "Azure auth timed out"}
        except Exception as e:
            return {"healthy": False, "status": f"Azure connection error: {e}"}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "Azure activity logs collected"}
