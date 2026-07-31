import ipaddress
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.models import IocDatabase, ThreatIntelligence


from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)


class ThreatIntelEnricher:
    """Enrich IOCs using free/community threat intelligence sources."""

    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)

    async def close(self) -> None:
        await self.client.aclose()

    async def enrich(self, indicator: str, type_hint: str | None = None) -> dict[str, Any]:
        ioc_type = type_hint or self._detect_type(indicator)
        cached = await self._cached_result(indicator, ioc_type)

        results: dict[str, Any] = {
            "indicator": indicator,
            "type": ioc_type,
            "sources": [],
            "reputation_score": cached["reputation_score"] if cached else 0,
            "confidence": cached["confidence"] if cached else 0,
            "country": cached.get("country") if cached else None,
            "asn": cached.get("asn") if cached else None,
            "threat_category": cached.get("threat_category") if cached else None,
            "malware": cached.get("malware") if cached else None,
            "first_seen": cached.get("first_seen") if cached else None,
            "last_seen": cached.get("last_seen") if cached else None,
        }

        if ioc_type == "ip":
            await self._enrich_ip(indicator, results)
        elif ioc_type == "domain":
            await self._enrich_domain(indicator, results)
        elif ioc_type == "hash":
            await self._enrich_hash(indicator, results)
        elif ioc_type == "url":
            await self._enrich_url(indicator, results)

        await self._persist(indicator, ioc_type, results)
        return results

    async def _enrich_ip(self, ip: str, results: dict[str, Any]) -> None:
        if self.settings.ABUSEIPDB_API_KEY:
            try:
                headers = {"Key": self.settings.ABUSEIPDB_API_KEY, "Accept": "application/json"}
                response = await self.client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": ip, "maxAgeInDays": 90},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                results["reputation_score"] = max(results["reputation_score"], int(score))
                results["country"] = data.get("countryCode") or results.get("country")
                results["threat_category"] = data.get("usageType") or results.get("threat_category")
                results["sources"].append({"name": "abuseipdb", "score": score})
            except Exception as exc:
                logger.debug("AbuseIPDB lookup failed for %s: %s", ip, exc)

        # AlienVault OTX (free API, works without key for basic queries)
        try:
            headers = {}
            if self.settings.ALIENVAULT_OTX_API_KEY:
                headers["X-OTX-API-KEY"] = self.settings.ALIENVAULT_OTX_API_KEY
            response = await self.client.get(
                f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                pulse_count = data.get("pulse_info", {}).get("count", 0)
                score = min(pulse_count * 10, 100)
                results["reputation_score"] = max(results["reputation_score"], score)
                results["sources"].append({"name": "alienvault_otx", "pulse_count": pulse_count})
                if pulse_count > 0:
                    results["threat_category"] = results.get("threat_category") or "malicious_ip"
        except Exception as exc:
            logger.debug("AlienVault OTX lookup failed for %s: %s", ip, exc)

        # URLHaus can also query IP reputation
        try:
            response = await self.client.post(
                f"{self.settings.URLHAUS_API_URL}/host",
                data={"host": ip},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("urls"):
                    results["reputation_score"] = max(results["reputation_score"], 80)
                    results["threat_category"] = results.get("threat_category") or "malware"
                    results["sources"].append({"name": "urlhaus", "matches": len(data["urls"])})
        except Exception as exc:
            logger.debug("URLHaus host lookup failed for %s: %s", ip, exc)

        results["confidence"] = min(50 + len(results["sources"]) * 15, 100)

    async def _enrich_domain(self, domain: str, results: dict[str, Any]) -> None:
        # AlienVault OTX (free API, works without key)
        try:
            headers = {}
            if self.settings.ALIENVAULT_OTX_API_KEY:
                headers["X-OTX-API-KEY"] = self.settings.ALIENVAULT_OTX_API_KEY
            response = await self.client.get(
                f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                pulse_count = data.get("pulse_info", {}).get("count", 0)
                score = min(pulse_count * 10, 100)
                results["reputation_score"] = max(results["reputation_score"], score)
                results["sources"].append({"name": "alienvault_otx", "pulse_count": pulse_count})
        except Exception as exc:
            logger.debug("AlienVault OTX domain lookup failed for %s: %s", domain, exc)

        try:
            response = await self.client.post(
                f"{self.settings.URLHAUS_API_URL}/host",
                data={"host": domain},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("urls"):
                    results["reputation_score"] = max(results["reputation_score"], 80)
                    results["threat_category"] = results.get("threat_category") or "malware"
                    results["sources"].append({"name": "urlhaus", "matches": len(data["urls"])})
        except Exception as exc:
            logger.debug("URLHaus host lookup failed for %s: %s", domain, exc)

        results["confidence"] = min(50 + len(results["sources"]) * 15, 100)

    async def _enrich_hash(self, file_hash: str, results: dict[str, Any]) -> None:
        if self.settings.VIRUSTOTAL_API_KEY:
            try:
                headers = {"x-apikey": self.settings.VIRUSTOTAL_API_KEY}
                response = await self.client.get(
                    f"https://www.virustotal.com/api/v3/files/{file_hash}", headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    attrs = data.get("data", {}).get("attributes", {})
                    stats = attrs.get("last_analysis_stats", {})
                    malicious = stats.get("malicious", 0)
                    total = sum(stats.values()) or 1
                    score = int((malicious / total) * 100)
                    results["reputation_score"] = max(results["reputation_score"], score)
                    results["malware"] = attrs.get("popular_threat_classification", {}).get("suggested_threat_label")
                    results["sources"].append({"name": "virustotal", "malicious": malicious, "total": total})
            except Exception as exc:
                logger.debug("VirusTotal hash lookup failed for %s: %s", file_hash, exc)

        if self.settings.ALIENVAULT_OTX_API_KEY:
            try:
                headers = {"X-OTX-API-KEY": self.settings.ALIENVAULT_OTX_API_KEY}
                response = await self.client.get(
                    f"https://otx.alienvault.com/api/v1/indicators/file/{file_hash}/general", headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    pulse_count = data.get("pulse_info", {}).get("count", 0)
                    score = min(pulse_count * 10, 100)
                    results["reputation_score"] = max(results["reputation_score"], score)
                    results["sources"].append({"name": "alienvault_otx", "pulse_count": pulse_count})
            except Exception as exc:
                logger.debug("AlienVault OTX hash lookup failed for %s: %s", file_hash, exc)

        results["confidence"] = min(50 + len(results["sources"]) * 15, 100)

    async def _enrich_url(self, url: str, results: dict[str, Any]) -> None:
        try:
            response = await self.client.post(
                f"{self.settings.URLHAUS_API_URL}/url",
                data={"url": url},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("query_status") == "ok":
                    results["reputation_score"] = max(results["reputation_score"], 90)
                    results["threat_category"] = data.get("threat") or "malware"
                    results["sources"].append({"name": "urlhaus", "status": "malicious"})
        except Exception as exc:
            logger.debug("URLHaus URL lookup failed for %s: %s", url, exc)

        results["confidence"] = min(50 + len(results["sources"]) * 15, 100)

    async def _cached_result(self, indicator: str, ioc_type: str) -> dict[str, Any] | None:
        cutoff = utc_now() - timedelta(hours=self.settings.TI_CACHE_HOURS)
        result = await self.db.execute(
            select(ThreatIntelligence)
            .where(ThreatIntelligence.indicator == indicator)
            .where(ThreatIntelligence.type == ioc_type)
            .where(ThreatIntelligence.last_checked >= cutoff)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {
            "reputation_score": row.reputation_score,
            "confidence": row.confidence,
            "country": row.country,
            "asn": row.asn,
            "threat_category": row.threat_category,
            "malware": row.malware,
            "first_seen": row.first_seen.isoformat() if row.first_seen else None,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
        }

    async def _persist(self, indicator: str, ioc_type: str, results: dict[str, Any]) -> None:
        now = utc_now()
        result = await self.db.execute(
            select(ThreatIntelligence)
            .where(ThreatIntelligence.indicator == indicator)
            .where(ThreatIntelligence.type == ioc_type)
        )
        row = result.scalar_one_or_none()
        if row:
            row.reputation_score = results["reputation_score"]
            row.confidence = results["confidence"]
            row.country = results.get("country")
            row.asn = results.get("asn")
            row.threat_category = results.get("threat_category")
            row.malware = results.get("malware")
            row.last_seen = now
            row.last_checked = now
            row.source = json.dumps([s["name"] for s in results["sources"]]) if results["sources"] else "local"
        else:
            row = ThreatIntelligence(
                indicator=indicator,
                type=ioc_type,
                source=json.dumps([s["name"] for s in results["sources"]]) if results["sources"] else "local",
                threat_category=results.get("threat_category"),
                reputation_score=results["reputation_score"],
                confidence=results["confidence"],
                country=results.get("country"),
                asn=results.get("asn"),
                malware=results.get("malware"),
                first_seen=now,
                last_seen=now,
                last_checked=now,
            )
            self.db.add(row)

        # Keep a normalized copy in the IOC database as well
        ioc_result = await self.db.execute(
            select(IocDatabase).where(IocDatabase.value == indicator).where(IocDatabase.type == ioc_type)
        )
        ioc_row = ioc_result.scalar_one_or_none()
        if ioc_row:
            ioc_row.last_seen = now
            ioc_row.confidence = results["confidence"]
            ioc_row.category = results.get("threat_category")
        else:
            ioc_row = IocDatabase(
                value=indicator,
                type=ioc_type,
                category=results.get("threat_category"),
                confidence=results["confidence"],
                first_seen=now,
                last_seen=now,
                sources=json.dumps([s["name"] for s in results["sources"]]) if results["sources"] else None,
            )
            self.db.add(ioc_row)

        await self.db.commit()

    @staticmethod
    def _detect_type(value: str) -> str:
        value = value.strip()
        if value.startswith(("http://", "https://")):
            return "url"
        try:
            ipaddress.ip_address(value)
            return "ip"
        except ValueError:
            pass
        if "." in value and len(value.split(".")[-1]) <= 6:
            return "domain"
        if len(value) in (32, 40, 64):
            return "hash"
        return "unknown"
