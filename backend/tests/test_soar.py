import pytest


@pytest.mark.asyncio
async def test_create_and_run_playbook(client):
    await client.post("/api/auth/register", json={
        "username": "soaruser",
        "email": "soar@goldendome.local",
        "password": "StrongPass123!",
        "role": "soc_analyst",
    })
    login = await client.post("/api/auth/login", data={"username": "soaruser", "password": "StrongPass123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Test Playbook",
        "description": "Integration test",
        "trigger": "manual",
        "status": "active",
        "actions": [
            {"action": "block_ip", "params": {"ip": "10.0.0.55"}},
            {"action": "create_ticket", "params": {"title": "SOC Ticket"}},
        ],
    }
    create_resp = await client.post("/api/soar/playbooks", json=payload, headers=headers)
    assert create_resp.status_code == 201
    playbook = create_resp.json()
    assert playbook["name"] == payload["name"]
    assert playbook["status"] == "active"

    run_resp = await client.post(f"/api/soar/playbooks/{playbook['id']}/run", json={}, headers=headers)
    assert run_resp.status_code == 200
    execution = run_resp.json()
    assert execution["status"] == "completed"
    assert "Blocked IP" in execution["output_log"]

    list_resp = await client.get("/api/soar/executions", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["data"][0]["id"] == execution["id"]
