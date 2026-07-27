import pytest

from app.database.models import Alert, Asset, Incident, User
from app.config.security import hash_password


@pytest.mark.asyncio
async def test_alert_model(db_session):
    alert = Alert(
        wazuh_alert_id="wazuh-001",
        title="Test Alert",
        description="A suspicious activity",
        severity=12,
        source_ip="192.168.1.100",
        rule_id="100100",
        mitre_technique="T1046",
        status="new",
    )
    db_session.add(alert)
    await db_session.commit()

    assert alert.id is not None
    assert alert.status == "new"
    assert alert.mitre_technique == "T1046"


@pytest.mark.asyncio
async def test_asset_model(db_session):
    asset = Asset(
        hostname="test-server",
        ip_address="192.168.1.50",
        type="linux_server",
        operating_system="Ubuntu 22.04",
        criticality=80,
        risk_score=0,
    )
    db_session.add(asset)
    await db_session.commit()

    assert asset.id is not None
    assert asset.criticality == 80


@pytest.mark.asyncio
async def test_incident_model(db_session):
    user = User(
        username="incidentowner",
        email="owner@goldendome.local",
        hashed_password=hash_password("StrongPass123!"),
        role="soc_analyst",
    )
    db_session.add(user)
    await db_session.commit()

    incident = Incident(
        name="RDP Brute Force",
        severity="high",
        status="open",
        description="Multiple failed RDP attempts",
        assigned_user_id=user.id,
    )
    db_session.add(incident)
    await db_session.commit()

    assert incident.id is not None
    assert incident.assigned_user_id == user.id
    assert incident.status == "open"
