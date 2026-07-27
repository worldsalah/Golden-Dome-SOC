import pytest
import pytest_asyncio

from app.schemas.detection_rule import DetectionRuleCreate, DetectionRuleUpdate
from app.services.detection_rule_service import DetectionRuleService


@pytest_asyncio.fixture
async def service(db_session):
    return DetectionRuleService(db_session)


@pytest.mark.asyncio
async def test_create_and_retrieve_rule(service):
    data = DetectionRuleCreate(
        name="SSH Brute Force",
        description="Test",
        severity=10,
        category="Authentication",
        source="Wazuh",
        logic="event.get('rule', {}).get('id') == '200001'",
        mitre_attack_id="T1110",
    )
    rule = await service.create_rule(data, created_by=None)
    assert rule.id
    fetched = await service.get_rule(rule.id)
    assert fetched.name == "SSH Brute Force"


@pytest.mark.asyncio
async def test_rule_test_evaluates_correctly(service):
    data = DetectionRuleCreate(
        name="Port Scan",
        severity=12,
        category="Network",
        source="Wazuh",
        logic="event.get('rule', {}).get('id') == '200040' and event.get('rule', {}).get('level', 0) >= 10",
    )
    rule = await service.create_rule(data)

    result = await service.test_rule(rule, {"rule": {"id": "200040", "level": 12}})
    assert result["matched"] is True

    result = await service.test_rule(rule, {"rule": {"id": "200040", "level": 5}})
    assert result["matched"] is False


@pytest.mark.asyncio
async def test_toggle_rule(service):
    data = DetectionRuleCreate(
        name="Toggle Test",
        severity=5,
        category="Test",
        source="Wazuh",
        logic="True",
    )
    rule = await service.create_rule(data)
    assert rule.status == "active"

    updated = await service.update_rule(rule.id, DetectionRuleUpdate(status="disabled"))
    assert updated.status == "disabled"
