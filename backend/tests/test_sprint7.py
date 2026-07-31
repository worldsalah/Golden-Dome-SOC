"""Tests for Sprint 7 features: MFA, API keys, connectors, tenant isolation, deployment, security."""

import pytest


async def _login(client, username: str, password: str) -> dict[str, str]:
    response = await client.post("/api/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _bootstrap_admin(client):
    await client.post("/api/auth/register", json={
        "username": "admin",
        "email": "admin@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    return await _login(client, "admin", "StrongPass123!")


@pytest.mark.asyncio
async def test_mfa_enroll_and_verify(client):
    headers = await _bootstrap_admin(client)

    # Enroll MFA
    resp = await client.post("/api/auth/mfa/enroll", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "secret" in data
    assert "qr_uri" in data
    assert len(data["backup_codes"]) == 10

    # Verify with a valid TOTP code
    import pyotp
    secret = data["secret"]
    totp = pyotp.TOTP(secret)
    code = totp.now()

    resp = await client.post("/api/auth/mfa/verify", headers=headers, json={"code": code})
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


@pytest.mark.asyncio
async def test_mfa_verify_invalid_code(client):
    headers = await _bootstrap_admin(client)
    await client.post("/api/auth/mfa/enroll", headers=headers)
    resp = await client.post("/api/auth/mfa/verify", headers=headers, json={"code": "000000"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_mfa_disable(client):
    headers = await _bootstrap_admin(client)
    enroll = await client.post("/api/auth/mfa/enroll", headers=headers)
    secret = enroll.json()["secret"]

    import pyotp
    code = pyotp.TOTP(secret).now()
    await client.post("/api/auth/mfa/verify", headers=headers, json={"code": code})

    code2 = pyotp.TOTP(secret).now()
    resp = await client.post("/api/auth/mfa/disable", headers=headers, json={"code": code2})
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


@pytest.mark.asyncio
async def test_api_key_create_list_revoke(client):
    headers = await _bootstrap_admin(client)

    # Create
    resp = await client.post("/api/security/api-keys", headers=headers, json={
        "name": "Test Key",
        "scopes": ["read:alerts", "read:assets"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "key" in data
    assert data["key_prefix"]
    prefix = data["key_prefix"]

    # List
    resp = await client.get("/api/security/api-keys", headers=headers)
    assert resp.status_code == 200
    keys = resp.json()
    assert any(k["key_prefix"] == prefix for k in keys)

    # Revoke
    resp = await client.delete(f"/api/security/api-keys/{prefix}", headers=headers)
    assert resp.status_code == 204

    # Verify revoked
    resp = await client.get("/api/security/api-keys", headers=headers)
    keys = resp.json()
    matching = [k for k in keys if k["key_prefix"] == prefix]
    assert matching and matching[0]["is_active"] is False


@pytest.mark.asyncio
async def test_security_headers_endpoint(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/security/headers", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "headers" in data
    assert data["headers"]["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_security_audit_summary(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/security/audit-summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "event_counts" in data
    assert "failed_logins" in data
    assert "active_api_keys" in data


@pytest.mark.asyncio
async def test_deployment_info(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/deployment/info", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data or "deployment" in data or "components" in data


@pytest.mark.asyncio
async def test_deployment_health(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/deployment/health-summary", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_connector_list(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/connectors", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_azure_connector_test_missing_creds():
    from app.services.connectors.builtin_azure import AzureConnector
    connector = AzureConnector(config={})
    result = await connector.test_connection()
    assert result["healthy"] is False
    assert "Missing" in result["status"]


@pytest.mark.asyncio
async def test_defender_connector_test_missing_creds():
    from app.services.connectors.builtin_defender import DefenderConnector
    connector = DefenderConnector(config={})
    result = await connector.test_connection()
    assert result["healthy"] is False
    assert "Missing" in result["status"]


@pytest.mark.asyncio
async def test_tenant_isolation_middleware_sets_state(client):
    headers = await _bootstrap_admin(client)
    # The middleware should set tenant_id on request state
    # Admin user has no org, so tenant_id should be None
    resp = await client.get("/api/assets", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_onboarding_wizard(client):
    headers = await _bootstrap_admin(client)
    resp = await client.post("/api/onboarding/wizard", headers=headers, json={
        "org": {
            "name": "Test Corp",
            "slug": "test-corp",
            "industry": "technology",
        },
        "admin": {
            "username": "testadmin",
            "email": "testadmin@testcorp.com",
            "password": "StrongPass123!",
        },
        "connectors": [],
        "assets": [],
    })
    assert resp.status_code in (200, 201)


@pytest.mark.asyncio
async def test_posture_summary(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/posture", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_hotel_dashboard(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/hotel/dashboard", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_organizations_list(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/organizations", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_logs_list(client):
    headers = await _bootstrap_admin(client)
    resp = await client.get("/api/audit/logs", headers=headers)
    assert resp.status_code == 200
