import pytest


@pytest.mark.asyncio
async def test_node_workflow_with_approval(client):
    await client.post("/api/auth/register", json={
        "username": "soarwfuser",
        "email": "soarwf@goldendome.local",
        "password": "StrongPass123!",
        "role": "soc_analyst",
    })
    login = await client.post("/api/auth/login", data={"username": "soarwfuser", "password": "StrongPass123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Test Approval Workflow",
        "description": "Workflow with approval gate",
        "trigger": "manual",
        "status": "active",
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Start", "config": {}, "next_nodes": ["action"]},
            {"id": "action", "type": "block_ip", "name": "Block IP", "config": {"ip": "{{input.ip}}"}, "next_nodes": ["approval"]},
            {"id": "approval", "type": "approval", "name": "Approve", "config": {"risk_level": "high", "summary": "Block {{input.ip}}"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "End", "config": {}},
        ],
        "actions": [],
    }
    create_resp = await client.post("/api/soar/playbooks", json=payload, headers=headers)
    assert create_resp.status_code == 201
    playbook = create_resp.json()

    run_resp = await client.post(f"/api/soar/playbooks/{playbook['id']}/run", json={"input_data": {"ip": "10.0.0.99"}}, headers=headers)
    assert run_resp.status_code == 200
    execution = run_resp.json()
    assert execution["status"] == "awaiting_approval"
    assert execution["current_node_id"] == "approval"

    approvals_resp = await client.get("/api/soar/approvals?status=pending", headers=headers)
    assert approvals_resp.status_code == 200
    approvals = approvals_resp.json()
    assert len(approvals) == 1
    approval = approvals[0]
    assert "10.0.0.99" in approval["action_summary"]

    decide_resp = await client.post(f"/api/soar/approvals/{approval['id']}/decision", json={"decision": "approved"}, headers=headers)
    assert decide_resp.status_code == 200

    exec_resp = await client.get(f"/api/soar/executions/{execution['id']}", headers=headers)
    assert exec_resp.status_code == 200
    completed = exec_resp.json()
    assert completed["status"] == "completed"

    timeline_resp = await client.get(f"/api/soar/executions/{execution['id']}/timeline", headers=headers)
    assert timeline_resp.status_code == 200
    assert len(timeline_resp.json()) >= 2


@pytest.mark.asyncio
async def test_alert_auto_triggers_playbook(client):
    await client.post("/api/auth/register", json={
        "username": "soartrigger",
        "email": "soartrigger@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    login = await client.post("/api/auth/login", data={"username": "soartrigger", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_playbook = await client.post("/api/soar/playbooks", json={
        "name": "Auto Trigger Test",
        "description": "Trigger on alert",
        "trigger": "alert",
        "trigger_config": {"severity_min": 5},
        "status": "active",
        "nodes": [
            {"id": "trigger", "type": "trigger", "name": "Alert", "config": {}, "next_nodes": ["notify"]},
            {"id": "notify", "type": "notify", "name": "Notify", "config": {"channel": "notification_center", "message": "Auto triggered"}, "next_nodes": ["end"]},
            {"id": "end", "type": "end", "name": "End", "config": {}},
        ],
        "actions": [],
    }, headers=headers)
    assert create_playbook.status_code == 201

    create_alert = await client.post("/api/alerts", json={
        "wazuh_alert_id": "wazuh-auto-001",
        "title": "Suspicious login",
        "severity": 7,
        "source_ip": "10.0.0.5",
        "status": "new",
    }, headers=headers)
    assert create_alert.status_code == 201

    executions_resp = await client.get("/api/soar/executions", headers=headers)
    assert executions_resp.status_code == 200
    executions = executions_resp.json()["data"]
    auto_runs = [e for e in executions if e["trigger_event"] and e["trigger_event"].startswith("alert:")]
    assert len(auto_runs) >= 1
    assert auto_runs[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_playbook_clone_and_delete(client):
    await client.post("/api/auth/register", json={
        "username": "soarcloneuser",
        "email": "soarclone@goldendome.local",
        "password": "StrongPass123!",
        "role": "admin",
    })
    login = await client.post("/api/auth/login", data={"username": "soarcloneuser", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post("/api/soar/playbooks", json={
        "name": "Clone Me",
        "trigger": "manual",
        "status": "active",
        "actions": [{"action": "create_ticket", "params": {}}],
        "nodes": [],
    }, headers=headers)
    assert create.status_code == 201
    pb_id = create.json()["id"]

    del_resp = await client.delete(f"/api/soar/playbooks/{pb_id}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/soar/playbooks/{pb_id}", headers=headers)
    assert get_resp.status_code == 404
