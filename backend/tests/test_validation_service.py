from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from app.database.models import Alert, AlertStatus, MITRETechnique
from app.services.validation_service import ValidationService

NOW = datetime.now(timezone.utc)


def _mock_wazuh(rules, rule_stats):
    wazuh = mock.AsyncMock()
    wazuh.get_rules.return_value = {"data": {"affected_items": rules}}
    wazuh.get_rule_stats.return_value = rule_stats
    return wazuh


@pytest.mark.asyncio
async def test_validated_detection_with_recent_alerts_and_low_fp(db_session):
    db_session.add(MITRETechnique(technique_id="T1110", name="Brute Force", tactic="Credential Access", detection_status="detected"))
    db_session.add(Alert(wazuh_alert_id="a1", title="x", severity=10, rule_id="200001", status=AlertStatus.NEW.value))
    db_session.add(Alert(wazuh_alert_id="a2", title="x", severity=10, rule_id="200001", status=AlertStatus.RESOLVED.value))
    await db_session.commit()

    rules = [{"id": 200001, "level": 10, "description": "SSH brute force", "status": "enabled",
              "groups": ["goldendome"], "mitre": {"id": ["T1110"]}}]
    rule_stats = {"200001": {"alert_count": 12, "last_trigger": NOW.isoformat(), "avg_level": 10}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_validation_center()

    entry = result["detections"][0]
    assert entry["rule_id"] == "200001"
    assert entry["mitre_technique"] == "T1110"
    assert entry["alert_count"] == 12
    assert entry["false_positive_rate"] == 0.0
    assert entry["false_positive_sample_size"] == 2
    assert entry["coverage_percentage"] == 100.0
    assert entry["validation_status"] == "validated"
    assert entry["detection_confidence"] > 70
    assert result["summary"]["total_detections"] == 1
    assert result["summary"]["validated"] == 1


@pytest.mark.asyncio
async def test_pending_detection_with_no_alerts_has_zero_coverage(db_session):
    rules = [{"id": 200099, "level": 8, "description": "Untested rule", "status": "enabled",
              "groups": ["goldendome"]}]
    rule_stats: dict = {}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_validation_center()

    entry = result["detections"][0]
    assert entry["alert_count"] == 0
    assert entry["mitre_technique"] is None
    assert entry["coverage_percentage"] == 0.0
    assert entry["validation_status"] == "pending"
    assert entry["false_positive_rate"] is None


@pytest.mark.asyncio
async def test_high_false_positive_rate_marks_detection_failed(db_session):
    for i in range(3):
        db_session.add(Alert(wazuh_alert_id=f"fp{i}", title="x", severity=8, rule_id="200005", status=AlertStatus.FALSE_POSITIVE.value))
    db_session.add(Alert(wazuh_alert_id="tp1", title="x", severity=8, rule_id="200005", status=AlertStatus.RESOLVED.value))
    await db_session.commit()

    rules = [{"id": 200005, "level": 8, "description": "Noisy rule", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200005": {"alert_count": 4, "last_trigger": NOW.isoformat(), "avg_level": 8}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_validation_center()

    entry = result["detections"][0]
    assert entry["false_positive_rate"] == 75.0
    assert entry["validation_status"] == "failed"


@pytest.mark.asyncio
async def test_stale_detection_when_last_trigger_beyond_window(db_session):
    old_trigger = (NOW - timedelta(days=120)).isoformat()
    rules = [{"id": 200006, "level": 9, "description": "Old rule", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200006": {"alert_count": 5, "last_trigger": old_trigger, "avg_level": 9}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_validation_center()

    entry = result["detections"][0]
    assert entry["validation_status"] == "stale"
