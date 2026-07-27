import pytest

from app.database.models import Alert


@pytest.mark.asyncio
async def test_list_alerts_requires_auth(client):
    response = await client.get("/api/alerts")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_alerts(client):
    # Register and login to obtain token
    await client.post("/api/auth/register", json={
        "username": "alertuser",
        "email": "alert@goldendome.local",
        "password": "StrongPass123!",
        "role": "soc_analyst",
    })
    login = await client.post("/api/auth/login", data={
        "username": "alertuser",
        "password": "StrongPass123!",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/alerts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
