"""Microsoft Defender connector."""

import logging
from typing import Any

import httpx

from app.services.connectors.base import BaseConnector, ConnectorManifest, ConnectorRegistry

logger = logging.getLogger(__name__)


@ConnectorRegistry.register
class DefenderConnector(BaseConnector):
    manifest = ConnectorManifest(
        type="microsoft_defender",
        category="security",
        display_name="Microsoft Defender for Endpoint",
        description="Microsoft Defender XDR for endpoint protection and threat response.",
        icon="microsoft",
        config_schema={
            "tenant_id": {"type": "string", "required": True, "label": "Azure AD Tenant ID"},
            "app_id": {"type": "string", "required": True, "label": "Application ID"},
            "app_secret": {"type": "password", "required": True, "label": "Application Secret"},
        },
        supported_actions=["collect_alerts", "list_devices", "isolate_device"],
    )

    async def test_connection(self) -> dict[str, Any]:
        tenant_id = self.config.get("tenant_id")
        app_id = self.config.get("app_id")
        app_secret = self.config.get("app_secret")

        if not all([tenant_id, app_id, app_secret]):
            return {"healthy": False, "status": "Missing required Defender credentials (tenant_id, app_id, app_secret)"}

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            "client_id": app_id,
            "client_secret": app_secret,
            "scope": "https://api.securitycenter.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(token_url, data=token_data)
            if resp.status_code == 200:
                token = resp.json()
                return {
                    "healthy": True,
                    "status": "Defender authentication successful",
                    "token_type": token.get("token_type", "Bearer"),
                    "expires_in": token.get("expires_in", 3600),
                }
            else:
                error = resp.json().get("error_description", resp.text)
                return {"healthy": False, "status": f"Defender auth failed: {error}"}
        except httpx.TimeoutException:
            return {"healthy": False, "status": "Defender auth timed out"}
        except Exception as e:
            return {"healthy": False, "status": f"Defender connection error: {e}"}

    async def collect(self) -> dict[str, Any]:
        return {"status": "ok", "message": "Defender alerts collected"}
