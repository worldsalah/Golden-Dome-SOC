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
    wazuh.get_alert_count.return_value = 123
    wazuh.get_manager_status.return_value = {"data": {"affected_items": [{"wazuh-analysisd": "running"}]}}
    wazuh.get_manager_stats.return_value = {"data": {"affected_items": [{"events_decoded": 7200, "events_dropped": 12, "alerts_written": 3600}]}}
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


@pytest.mark.asyncio
async def test_attack_coverage_classifies_validated_and_missing(db_session):
    db_session.add(MITRETechnique(technique_id="T1110", name="Brute Force", tactic="Credential Access", detection_status="detected"))
    db_session.add(MITRETechnique(technique_id="T1046", name="Network Service Scanning", tactic="Discovery", detection_status="planned"))
    await db_session.commit()

    rules = [{"id": 200001, "level": 10, "description": "SSH brute force", "status": "enabled",
              "groups": ["goldendome"], "mitre": {"id": ["T1110"]}}]
    rule_stats = {"200001": {"alert_count": 5, "last_trigger": NOW.isoformat(), "avg_level": 10}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_attack_coverage()

    by_id = {t["technique_id"]: t for t in result["techniques"]}
    assert by_id["T1110"]["state"] == "validated"
    assert by_id["T1110"]["mapped_rule_count"] == 1
    assert by_id["T1046"]["state"] == "missing_detection"
    assert by_id["T1046"]["mapped_rule_count"] == 0
    assert result["total_techniques"] == 2
    assert result["validated_techniques"] == 1
    assert result["overall_coverage_percentage"] == 50.0
    assert result["tactic_summary"]["Credential Access"]["validated"] == 1
    assert result["tactic_summary"]["Discovery"]["missing_detection"] == 1


@pytest.mark.asyncio
async def test_attack_coverage_marks_failed_when_rule_has_high_fp(db_session):
    db_session.add(MITRETechnique(technique_id="T1046", name="Network Service Scanning", tactic="Discovery", detection_status="detected"))
    for i in range(3):
        db_session.add(Alert(wazuh_alert_id=f"fp{i}", title="x", severity=8, rule_id="200040", status=AlertStatus.FALSE_POSITIVE.value))
    db_session.add(Alert(wazuh_alert_id="tp1", title="x", severity=8, rule_id="200040", status=AlertStatus.RESOLVED.value))
    await db_session.commit()

    rules = [{"id": 200040, "level": 12, "description": "Port scan", "status": "enabled",
              "groups": ["goldendome"], "mitre": {"id": ["T1046"]}}]
    rule_stats = {"200040": {"alert_count": 4, "last_trigger": NOW.isoformat(), "avg_level": 12}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_attack_coverage()

    entry = result["techniques"][0]
    assert entry["state"] == "failed"


@pytest.mark.asyncio
async def test_fp_analysis_suggests_whitelisting_for_noisy_rule(db_session):
    for i in range(4):
        db_session.add(Alert(wazuh_alert_id=f"fp{i}", title="x", severity=8, rule_id="200070", source_ip="10.0.0.5", status=AlertStatus.FALSE_POSITIVE.value))
    db_session.add(Alert(wazuh_alert_id="tp1", title="x", severity=8, rule_id="200070", source_ip="10.0.0.9", status=AlertStatus.RESOLVED.value))
    await db_session.commit()

    rules = [{"id": 200070, "level": 10, "description": "Noisy SQLi rule", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200070": {"alert_count": 5, "last_trigger": NOW.isoformat(), "avg_level": 10}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_false_positive_analysis()

    entry = result["rules"][0]
    assert entry["rule_id"] == "200070"
    assert entry["false_positive_rate"] == 80.0
    assert any("whitelist" in s.lower() for s in entry["suggestions"])
    assert result["rules_with_disposition_data"] == 1


@pytest.mark.asyncio
async def test_fp_analysis_flags_repeated_alerts_from_same_source(db_session):
    for i in range(6):
        db_session.add(Alert(wazuh_alert_id=f"r{i}", title="x", severity=9, rule_id="200040", source_ip="203.0.113.9", status=AlertStatus.NEW.value))
    await db_session.commit()

    rules = [{"id": 200040, "level": 12, "description": "Port scan", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200040": {"alert_count": 6, "last_trigger": NOW.isoformat(), "avg_level": 12}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_false_positive_analysis()

    entry = result["rules"][0]
    assert entry["repeated_alerts"] == 5
    assert any("duplicate" in s.lower() for s in entry["suggestions"])


@pytest.mark.asyncio
async def test_detection_performance_returns_latency_and_throughput(db_session):
    rules = [{"id": 200080, "level": 8, "description": "Chatty rule", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200080": {"alert_count": 25, "last_trigger": NOW.isoformat(), "avg_level": 8}}
    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_detection_performance()

    assert result["api_latency_ms"] >= 0
    assert result["indexer_latency_ms"] >= 0
    assert result["events_per_second"] == 2.0
    assert result["alerts_per_hour"] == 1.0
    assert result["drop_percentage"] == 0.17
    assert result["indexer_alert_volume_24h"] == 123
    assert any(d["name"] == "wazuh-analysisd" and d["status"] == "running" for d in result["daemon_health"])


@pytest.mark.asyncio
async def test_replay_alert_verdict_still_fires_when_rule_and_stats_match(db_session):
    from app.database.models import Alert
    alert = Alert(
        wazuh_alert_id="wa1",
        title="SSH brute force",
        severity=10,
        rule_id="200001",
        status="new",
        raw_log='{"rule": {"id": 200001, "description": "SSH brute force"}}',
    )
    db_session.add(alert)
    await db_session.commit()

    rules = [{"id": 200001, "level": 10, "description": "SSH brute force", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200001": {"alert_count": 5, "last_trigger": NOW.isoformat(), "avg_level": 10}}
    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.replay_alert(alert.id)

    assert result["alert_id"] == alert.id
    assert result["verdict"] == "still_fires"
    assert result["match_count_24h"] == 5
    assert result["current_rule"] is not None


@pytest.mark.asyncio
async def test_soc_health_score_earns_top_grade_when_all_metrics_healthy(db_session):
    db_session.add(MITRETechnique(technique_id="T1110", name="Brute Force", tactic="Credential Access", detection_status="detected"))
    await db_session.commit()

    rules = [{"id": 200001, "level": 10, "description": "SSH brute force", "status": "enabled",
              "groups": ["goldendome"], "mitre": {"id": ["T1110"]}}]
    rule_stats = {"200001": {"alert_count": 12, "last_trigger": NOW.isoformat(), "avg_level": 10}}
    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_soc_health_score()

    assert result["grade"] in {"A+", "A", "B"}
    assert result["overall_score"] >= 80
    assert result["open_alerts"] == 0
    assert result["open_incidents"] == 0
    assert "components" in result


@pytest.mark.asyncio
async def test_rule_optimizer_classifies_trigger_frequency_and_duplicates(db_session):
    rules = [
        {"id": 300001, "level": 8, "description": "Port scan", "status": "enabled", "groups": ["goldendome"]},
        {"id": 300002, "level": 8, "description": "Port scan", "status": "enabled", "groups": ["goldendome"]},
        {"id": 300003, "level": 8, "description": "Dormant rule", "status": "enabled", "groups": ["goldendome"]},
        {"id": 300004, "level": 8, "description": "Rare event", "status": "enabled", "groups": ["goldendome"]},
        {"id": 300005, "level": 12, "description": "Noisy rule", "status": "enabled", "groups": ["goldendome"]},
    ]
    rule_stats = {
        "300001": {"alert_count": 150, "last_trigger": NOW.isoformat(), "avg_level": 8},
        "300002": {"alert_count": 150, "last_trigger": NOW.isoformat(), "avg_level": 8},
        "300003": {"alert_count": 0, "last_trigger": None, "avg_level": 8},
        "300004": {"alert_count": 3, "last_trigger": NOW.isoformat(), "avg_level": 8},
        "300005": {"alert_count": 200, "last_trigger": NOW.isoformat(), "avg_level": 12},
    }
    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_rule_optimizer()

    assert result["total_rules"] == 5
    assert any(r["rule_id"] == "300003" for r in result["never_triggered"])
    assert any(r["rule_id"] == "300004" for r in result["rarely_triggered"])
    assert any(r["rule_id"] == "300001" and r["alert_count"] == 150 for r in result["frequently_triggered"])
    assert any(r["rule_id"] == "300005" for r in result["inefficient"])
    assert len(result["duplicate_groups"]) >= 1


@pytest.mark.asyncio
async def test_fp_analysis_flags_rule_with_no_confirmed_incidents(db_session):
    rules = [{"id": 200080, "level": 8, "description": "Chatty rule", "status": "enabled", "groups": ["goldendome"]}]
    rule_stats = {"200080": {"alert_count": 25, "last_trigger": NOW.isoformat(), "avg_level": 8}}

    service = ValidationService(db_session, wazuh_service=_mock_wazuh(rules, rule_stats))
    result = await service.get_false_positive_analysis()

    entry = result["rules"][0]
    assert entry["real_incidents"] == 0
    assert any("confirmed incident" in s.lower() for s in entry["suggestions"])
