import json
from unittest import mock

import pytest
import respx
from httpx import Response

from app.services.wazuh_service import WazuhService


@pytest.fixture
def service():
    return WazuhService()


@pytest.mark.asyncio
async def test_normalize_alert(service):
    raw = {
        "id": "alert-123",
        "timestamp": "2024-01-01T00:00:00Z",
        "rule": {
            "id": "100100",
            "level": 12,
            "description": "Port scan detected",
            "mitre": {"id": ["T1046"]},
        },
        "agent": {"id": "001", "name": "test-agent", "ip": "192.168.1.10"},
        "data": {"srcip": "10.0.0.1", "dstip": "192.168.1.10"},
    }
    normalized = await service.normalize_alert(raw)
    assert normalized["wazuh_alert_id"] == "alert-123"
    assert normalized["severity"] == 12
    assert normalized["mitre_technique"] == "T1046"
    assert normalized["source_ip"] == "10.0.0.1"


@pytest.mark.asyncio
async def test_wazuh_authentication_success(service):
    with respx.mock(base_url=service.settings.WAZUH_API_URL) as rsps:
        rsps.post("/security/user/authenticate").mock(
            return_value=Response(200, json={"data": {"token": "fake-jwt-token"}})
        )
        token = await service._authenticate()
        assert token == "fake-jwt-token"
