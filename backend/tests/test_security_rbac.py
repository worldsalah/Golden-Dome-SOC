import pytest


async def _login(client, username: str, password: str) -> dict[str, str]:
    response = await client.post("/api/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_rbac_prevents_viewer_mutation_and_administration(client):
    bootstrap = await client.post("/api/auth/register", json={
        "username": "securityadmin",
        "email": "securityadmin@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    assert bootstrap.status_code == 201
    admin_headers = await _login(client, "securityadmin", "StrongPass123!")

    viewer = await client.post("/api/users", headers=admin_headers, json={
        "username": "securityviewer",
        "email": "securityviewer@goldendome.local",
        "password": "StrongPass123!",
        "role": "viewer",
        "is_active": True,
    })
    assert viewer.status_code == 201
    viewer_headers = await _login(client, "securityviewer", "StrongPass123!")

    assert (await client.get("/api/assets", headers=viewer_headers)).status_code == 200
    assert (await client.get("/api/users", headers=viewer_headers)).status_code == 403
    assert (await client.post("/api/assets", headers=viewer_headers, json={
        "hostname": "forbidden-host", "ip_address": "10.0.0.10", "type": "workstation", "criticality": 1,
    })).status_code == 403


@pytest.mark.asyncio
async def test_pagination_rejects_out_of_range_input(client):
    await client.post("/api/auth/register", json={
        "username": "paginationadmin",
        "email": "paginationadmin@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    headers = await _login(client, "paginationadmin", "StrongPass123!")
    assert (await client.get("/api/assets?page=0", headers=headers)).status_code == 422
    assert (await client.get("/api/assets?limit=101", headers=headers)).status_code == 422
