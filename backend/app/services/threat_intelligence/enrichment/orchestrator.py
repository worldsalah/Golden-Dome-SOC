import json
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.models import (
    Alert,
    Campaign,
    Incident,
    Malware,
    ThreatActor,
    ThreatIOC,
    ThreatSource,
    VulnerabilityIntelligence,
)
from app.services.threat_intelligence.cache import SimpleTTLCache
from app.services.threat_intelligence.connectors import (
    AbuseIPDBConnector,
    AlienVaultOTXConnector,
    CISAKEVConnector,
    MalwareBazaarConnector,
    MITREAttackConnector,
    URLHausConnector,
    VirusTotalConnector,
)
from app.services.threat_intelligence.correlation.confidence_score import calculate_confidence
from app.services.threat_intelligence.correlation.threat_score import calculate_threat_score
from app.services.threat_intelligence.enrichment.io_extractor import detect_ioc_type
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)


class ThreatIntelligenceEngine:
    """High-level orchestrator for IOC extraction, enrichment, scoring, and persistence."""

    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.cache = SimpleTTLCache(default_ttl=self.settings.TI_CACHE_HOURS * 3600)
        self.connectors = self._build_connectors()

    def _build_connectors(self) -> list[Any]:
        return [
            AbuseIPDBConnector(api_key=self.settings.ABUSEIPDB_API_KEY, timeout=20.0),
            VirusTotalConnector(api_key=self.settings.VIRUSTOTAL_API_KEY, timeout=25.0),
            AlienVaultOTXConnector(api_key=self.settings.ALIENVAULT_OTX_API_KEY, timeout=20.0),
            URLHausConnector(api_url=self.settings.URLHAUS_API_URL, timeout=20.0),
            MalwareBazaarConnector(timeout=20.0),
            CISAKEVConnector(timeout=30.0),
            MITREAttackConnector(),
        ]

    async def close(self) -> None:
        for connector in self.connectors:
            try:
                await connector.close()
            except Exception as exc:
                logger.debug("Failed to close connector %s: %s", connector.name, exc)

    async def enrich(self, value: str, ioc_type: str | None = None) -> dict[str, Any]:
        ioc_type = ioc_type or detect_ioc_type(value)
        cache_key = f"ti:{ioc_type}:{value}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        provider_results: list[dict[str, Any]] = []
        for connector in self.connectors:
            try:
                result = await connector.enrich(value, ioc_type)
                if result.get("provider_score") is not None or result.get("raw_data"):
                    provider_results.append(result)
            except Exception as exc:
                logger.debug("Connector %s failed for %s: %s", connector.name, value, exc)

        merged = self._merge_results(value, ioc_type, provider_results)
        normalized = await self._persist_and_normalize(value, ioc_type, merged, provider_results)
        await self.cache.set(cache_key, normalized)
        return normalized

    def _merge_results(self, value: str, ioc_type: str, provider_results: list[dict[str, Any]]) -> dict[str, Any]:
        reputation_score = 0
        country: str | None = None
        asn: str | None = None
        isp: str | None = None
        threat_category: str | None = None
        malware: str | None = None
        cisa_kev = False
        malicious = False
        sources: list[dict[str, Any]] = []
        references: list[str] = []

        for r in provider_results:
            score = r.get("provider_score") or 0
            reputation_score = max(reputation_score, score)
            if r.get("country"):
                country = r["country"]
            if r.get("asn"):
                asn = r["asn"]
            if r.get("isp"):
                isp = r["isp"]
            if r.get("threat_category"):
                threat_category = r["threat_category"]
            if r.get("malware"):
                malware = r["malware"]
            if r.get("malicious"):
                malicious = True
            if r.get("cisa_kev"):
                cisa_kev = True
            if r.get("provider"):
                sources.append({"name": r["provider"], "score": score})
            if r.get("provider_reference"):
                references.append(r["provider_reference"])

        confidence = calculate_confidence(sources)
        scoring = calculate_threat_score(
            reputation_score=reputation_score,
            source_count=len(sources),
            has_malware=bool(malware),
            has_cisa_kev=cisa_kev,
        )

        return {
            "value": value,
            "type": ioc_type,
            "reputation_score": reputation_score,
            "confidence": confidence,
            "malicious": malicious or reputation_score >= 40,
            "threat_score": scoring["score"],
            "severity": scoring["classification"],
            "source_count": len(sources),
            "country": country,
            "asn": asn,
            "isp": isp,
            "threat_category": threat_category,
            "malware": malware,
            "cisa_kev": cisa_kev,
            "sources": sources,
            "references": references,
            "scoring": scoring,
            "enriched_at": utc_now().isoformat(),
        }

    async def _persist_and_normalize(
        self,
        value: str,
        ioc_type: str,
        merged: dict[str, Any],
        provider_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        now = utc_now()
        result = await self.db.execute(
            select(ThreatIOC).where(ThreatIOC.value == value).where(ThreatIOC.type == ioc_type)
        )
        ioc = result.scalar_one_or_none()
        if ioc:
            ioc.reputation_score = merged["reputation_score"]
            ioc.confidence = merged["confidence"]
            ioc.threat_score = merged["threat_score"]
            ioc.severity = merged["severity"]
            ioc.malicious = merged["malicious"]
            ioc.source_count = merged["source_count"]
            ioc.country = merged["country"]
            ioc.asn = merged["asn"]
            ioc.isp = merged["isp"]
            ioc.threat_category = merged["threat_category"]
            ioc.last_seen = now
            ioc.updated_at = now
        else:
            ioc = ThreatIOC(
                type=ioc_type,
                value=value,
                first_seen=now,
                last_seen=now,
                confidence=merged["confidence"],
                reputation_score=merged["reputation_score"],
                threat_score=merged["threat_score"],
                severity=merged["severity"],
                malicious=merged["malicious"],
                source_count=merged["source_count"],
                country=merged["country"],
                asn=merged["asn"],
                isp=merged["isp"],
                threat_category=merged["threat_category"],
            )
            self.db.add(ioc)

        await self.db.flush()

        # Replace child sources with fresh list
        await self.db.execute(delete(ThreatSource).where(ThreatSource.ioc_id == ioc.id))
        for provider_result in provider_results:
            source = ThreatSource(
                ioc_id=ioc.id,
                provider=provider_result.get("provider", "unknown"),
                provider_score=provider_result.get("provider_score"),
                provider_reference=provider_result.get("provider_reference"),
                raw_data=json.dumps(provider_result.get("raw_data") or {}),
                last_updated=now,
            )
            self.db.add(source)

        await self.db.commit()
        await self.db.refresh(ioc, ["sources"])

        normalized = dict(merged)
        normalized["id"] = ioc.id
        normalized["first_seen"] = ioc.first_seen.isoformat() if ioc.first_seen else None
        normalized["last_seen"] = ioc.last_seen.isoformat() if ioc.last_seen else None
        normalized["sources"] = [
            {"name": s.provider, "score": s.provider_score, "reference": s.provider_reference}
            for s in ioc.sources
        ]
        return normalized

    async def enrich_alert(self, alert: Alert, persist_links: bool = True) -> dict[str, Any]:
        from app.services.threat_intelligence.enrichment.io_extractor import IOCExtractor
        from app.services.threat_intelligence.correlation.correlation_engine import ThreatCorrelationEngine

        extractor = IOCExtractor()
        text = " ".join(filter(None, [
            alert.title or "",
            alert.description or "",
            alert.raw_log or "",
            alert.source_ip or "",
            alert.destination_ip or "",
        ]))
        extracted = extractor.extract(text)

        enriched_iocs: list[dict[str, Any]] = []
        for ioc_type, values in extracted.items():
            for value in values:
                try:
                    normalized = await self.enrich(value, ioc_type)
                    enriched_iocs.append(normalized)
                except Exception as exc:
                    logger.debug("Failed to enrich IOC %s (%s): %s", value, ioc_type, exc)

        if persist_links:
            correlation_engine = ThreatCorrelationEngine(self.db)
            await correlation_engine.enrich_alert_iocs(alert)

        return {
            "alert_id": alert.id,
            "iocs_extracted": extracted,
            "iocs_enriched": enriched_iocs,
            "enriched_at": utc_now().isoformat(),
        }

    async def enrich_incident(self, incident: Incident) -> dict[str, Any]:
        alert_iocs: list[dict[str, Any]] = []
        for alert in incident.alerts:
            alert_iocs.append(await self.enrich_alert(alert, persist_links=True))
        return {
            "incident_id": incident.id,
            "alert_enrichments": alert_iocs,
            "enriched_at": utc_now().isoformat(),
        }

    async def health(self) -> list[dict[str, Any]]:
        return [await connector.health() for connector in self.connectors]
