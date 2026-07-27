import pytest

from app.config.security import hash_password
from app.database.models import Alert, Asset, AssetVulnerability, User
from app.services.risk_service import RiskService, severity_to_score


def test_severity_to_score():
    assert severity_to_score("critical") == 100
    assert severity_to_score("high") == 80
    assert severity_to_score("medium") == 50
    assert severity_to_score("low") == 20
    assert severity_to_score("unknown") == 30


@pytest.mark.asyncio
async def test_calculate_asset_risk(db_session):
    asset = Asset(
        hostname="risky-server",
        ip_address="192.168.1.99",
        type="database",
        criticality=90,
        risk_score=0,
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    alert = Alert(
        wazuh_alert_id="risk-alert-1",
        title="High severity alert",
        severity=15,
        asset_id=asset.id,
        status="new",
    )
    db_session.add(alert)

    vuln = AssetVulnerability(
        asset_id=asset.id,
        cve="CVE-2024-0001",
        severity="high",
        cvss_score=80,
    )
    db_session.add(vuln)
    await db_session.commit()

    service = RiskService(db_session)
    score = await service.calculate_asset_risk(asset.id)
    assert 0 <= score <= 100
    assert asset.risk_score == score
