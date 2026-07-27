import pytest

from app.database.models import Alert, Asset
from app.services.ai_engine.analysis import SentinelAnalysisService
from app.services.ai_engine.knowledge_base import KnowledgeBase
from app.services.ai_engine.model_manager import ModelManager
from app.services.ai_engine.report_generator import IncidentReportGenerator
from app.services.ai_engine.risk_scorer import RiskScorer
from app.services.ai_engine.threat_intel import ThreatIntelEnricher


@pytest.mark.asyncio
async def test_model_manager_fallback_generation():
    mgr = ModelManager()
    mgr.base_url = "http://invalid-ollama:11434"  # force unreachable endpoint
    result = await mgr.generate("Analyze brute force alert severity 13", system=None)
    assert result["success"]
    assert result["source"] == "fallback"
    assert "raw" in result
    # Basic JSON validation is done inside the fallback


@pytest.mark.asyncio
async def test_knowledge_base_mitre_lookup():
    kb = KnowledgeBase()
    mitre = kb.lookup_mitre("T1110")
    assert mitre["name"] == "Brute Force"
    assert "Credential Access" in mitre["tactic"]


@pytest.mark.asyncio
async def test_playbook_selection():
    kb = KnowledgeBase()
    playbook = kb.playbook_for("T1110", "Multiple failed logons")
    assert any("Reset affected credentials" in step for step in playbook["short_term"])


@pytest.mark.asyncio
async def test_risk_scorer_alert(db_session):
    asset = Asset(hostname="test-asset", criticality=5)
    db_session.add(asset)
    await db_session.flush()

    alert = Alert(
        wazuh_alert_id="w-001",
        title="Brute force attempt",
        severity=12,
        source_ip="10.0.0.1",
        asset_id=asset.id,
        status="new",
    )
    db_session.add(alert)
    await db_session.commit()

    scorer = RiskScorer(db_session)
    score, reason = await scorer.calculate_alert_risk(alert)
    assert 0 <= score <= 100
    assert "severity" in reason
    assert "asset_criticality" in reason


@pytest.mark.asyncio
async def test_threat_intel_enricher_detects_ip(db_session):
    enricher = ThreatIntelEnricher(db_session)
    result = await enricher.enrich("8.8.8.8", "ip")
    assert result["indicator"] == "8.8.8.8"
    assert result["type"] == "ip"
    assert 0 <= result["reputation_score"] <= 100
    await enricher.close()


@pytest.mark.asyncio
async def test_sentinel_analysis_service(db_session):
    asset = Asset(hostname="win-server", criticality=7)
    db_session.add(asset)
    await db_session.flush()

    alert = Alert(
        wazuh_alert_id="w-002",
        title="Multiple failed RDP logons",
        severity=10,
        source_ip="192.168.1.100",
        asset_id=asset.id,
        status="new",
    )
    db_session.add(alert)
    await db_session.commit()

    service = SentinelAnalysisService(db_session)
    analysis = await service.analyze_alert(alert.id, persist=True)

    assert analysis["executive_summary"]
    assert analysis["mitre_mapping"]["technique_id"]
    assert 0 <= analysis["risk_score"] <= 100
    assert "investigation_steps" in analysis
    assert "recommended_response" in analysis
    assert analysis["analysis_id"]


@pytest.mark.asyncio
async def test_incident_report_generator(db_session):
    from app.database.models import Incident

    incident = Incident(name="Test Incident", severity="high", status="open")
    db_session.add(incident)
    await db_session.commit()

    generator = IncidentReportGenerator(db_session)
    report = await generator.generate(incident)

    assert report["report"]["title"]
    assert report["report"]["summary"]
    markdown = generator.to_markdown(report["report"])
    assert "#" in markdown
    pdf = generator.to_pdf(report["report"])
    assert isinstance(pdf, bytes)
    assert len(pdf) > 0
