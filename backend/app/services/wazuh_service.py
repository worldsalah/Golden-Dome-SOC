import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import get_settings
from app.services.wazuh.agents import WazuhAgentsClient
from app.services.wazuh.alerts import WazuhAlertsClient
from app.services.wazuh.client import WazuhApiClient, WazuhApiClientError
from app.services.wazuh.rules import WazuhRulesClient
from app.services.wazuh.vulnerabilities import WazuhVulnerabilitiesClient

logger = logging.getLogger(__name__)


class WazuhServiceError(Exception):
    """Custom exception for Wazuh service failures."""


class WazuhService:
    """High-level facade for the Wazuh Manager API and Wazuh Indexer (OpenSearch)."""

    def __init__(self, api_client: WazuhApiClient | None = None):
        self.api_client = api_client or WazuhApiClient()
        self.settings = self.api_client.settings or get_settings()
        self.alerts_client = WazuhAlertsClient()
        self.agents_client = WazuhAgentsClient(self.api_client)
        self.vulnerabilities_client = WazuhVulnerabilitiesClient(self.api_client)
        self.rules_client = WazuhRulesClient(self.api_client)

    async def _authenticate(self) -> str:
        """Backward-compatible wrapper for tests and legacy code."""
        return await self.api_client.authenticate()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Thin wrapper around the low-level API client to keep old code working."""
        try:
            return await self.api_client.request(method, endpoint, params=params, json_data=json_data)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_agents(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        try:
            return await self.agents_client.list(limit=limit, offset=offset)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_agent_details(self, agent_id: str) -> dict[str, Any]:
        try:
            return await self.agents_client.get(agent_id)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_vulnerabilities(
        self,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        try:
            return await self.vulnerabilities_client.list(
                agent_id=agent_id, limit=limit, offset=offset
            )
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_alerts(
        self,
        size: int = 100,
        severity: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self.alerts_client.get_alerts(
                size=size,
                severity=severity,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_security_events(
        self,
        size: int = 100,
        rule_id: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self.alerts_client.get_security_events(size=size, rule_id=rule_id)
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_rules(
        self,
        limit: int = 500,
        offset: int = 0,
        group: str | None = None,
        rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            return await self.rules_client.list(
                limit=limit, offset=offset, group=group, rule_ids=rule_ids
            )
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_alert_count(self, hours: int = 24) -> int:
        try:
            return await self.alerts_client.count_alerts(hours=hours)
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_manager_status(self) -> dict[str, Any]:
        try:
            return await self._request("GET", "/manager/status")
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_manager_stats(self, path: str = "/manager/stats/hourly") -> dict[str, Any]:
        try:
            return await self._request("GET", path)
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_manager_info(self) -> dict[str, Any]:
        try:
            return await self._request("GET", "/manager/info")
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_cluster_status(self) -> dict[str, Any]:
        try:
            return await self._request("GET", "/cluster/status")
        except WazuhApiClientError as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_agents_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        path = f"/agents/stats" if not agent_id else f"/agents/{agent_id}/stats"
        try:
            return await self._request("GET", path)
        except WazuhServiceError as exc:
            if "404" in str(exc):
                return {"data": {"affected_items": [], "total_affected_items": 0}, "error": 0, "message": "Endpoint not available in this Wazuh version"}
            raise

    async def get_mitre(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        try:
            return await self._request("GET", "/mitre", params={"limit": limit, "offset": offset})
        except WazuhServiceError as exc:
            if "404" in str(exc):
                return {"data": {"affected_items": [], "total_affected_items": 0}, "error": 0, "message": "MITRE endpoint not available in this Wazuh version"}
            raise

    async def get_tasks(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        try:
            return await self._request("GET", "/tasks", params={"limit": limit, "offset": offset})
        except WazuhServiceError as exc:
            if "404" in str(exc):
                return {"data": {"affected_items": [], "total_affected_items": 0}, "error": 0, "message": "Tasks endpoint not available in this Wazuh version"}
            raise

    async def get_dashboard(self, hours: int = 24) -> dict[str, Any]:
        """Aggregate live Wazuh data for the main dashboard."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=hours)).isoformat()
        today_start = (now - timedelta(days=1)).isoformat()

        client = self.alerts_client._get_client()

        # Total and today's alerts
        total_count = await self.alerts_client.count_alerts(hours=99999)
        today_count = await self.alerts_client.count_alerts(hours=24)

        # Severity, rules, source IPs, MITRE techniques, and hourly timeline
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [{"range": {"timestamp": {"gte": start}}}]
                }
            },
            "aggs": {
                "by_severity": {"terms": {"field": "rule.level", "size": 10}},
                "by_rule": {"terms": {"field": "rule.id", "size": 10}},
                "by_srcip": {"terms": {"field": "data.srcip", "size": 10, "missing": "N/A"}},
                "by_mitre": {"terms": {"field": "rule.mitre.id", "size": 10}},
                "by_hour": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "hour",
                        "format": "yyyy-MM-dd HH:mm",
                        "min_doc_count": 0,
                    }
                },
                "by_os": {"terms": {"field": "agent.os.name", "size": 10, "missing": "Unknown"}},
            },
        }

        try:
            response = await asyncio.to_thread(client.search, index="wazuh-alerts-*", body=body)
        except Exception as exc:
            raise WazuhServiceError(f"Dashboard aggregation failed: {exc}") from exc

        aggs = response.get("aggregations", {})

        def _buckets(key):
            return aggs.get(key, {}).get("buckets", [])

        severity_map = {str(b["key"]): b["doc_count"] for b in _buckets("by_severity")}
        critical = sum(c for sev, c in severity_map.items() if int(sev) >= 13)
        high = sum(c for sev, c in severity_map.items() if 10 <= int(sev) < 13)
        medium = sum(c for sev, c in severity_map.items() if 4 <= int(sev) < 10)
        low = sum(c for sev, c in severity_map.items() if int(sev) < 4)

        top_rules = [{"rule_id": str(b["key"]), "count": b["doc_count"]} for b in _buckets("by_rule")]
        top_srcip = [{"ip": b["key"], "count": b["doc_count"]} for b in _buckets("by_srcip")]
        top_mitre = [{"technique": b["key"], "count": b["doc_count"]} for b in _buckets("by_mitre")]
        top_os = [{"os": b["key"], "count": b["doc_count"]} for b in _buckets("by_os")]
        hourly = [{"hour": b["key_as_string"], "count": b["doc_count"]} for b in _buckets("by_hour")]

        # Agent status
        try:
            agents = await self.get_agents(limit=500)
            agent_items = agents.get("data", {}).get("affected_items", [])
            active = sum(1 for a in agent_items if a.get("status") == "active")
            total = len(agent_items)
        except Exception:
            active = 0
            total = 0
            agent_items = []

        return {
            "active_agents": active,
            "total_agents": total,
            "agents": agent_items,
            "total_alerts": total_count,
            "alerts_today": today_count,
            "alerts_last_24h": response.get("hits", {}).get("total", {}).get("value", 0),
            "severity": {"critical": critical, "high": high, "medium": medium, "low": low},
            "top_rules": top_rules,
            "top_source_ips": top_srcip,
            "top_mitre_techniques": top_mitre,
            "top_os": top_os,
            "alerts_per_hour": hourly,
            "generated_at": now,
        }

    async def get_mitre_matrix(self, hours: int = 168) -> dict[str, Any]:
        """Generate a live MITRE ATT&CK matrix from Wazuh alerts."""
        client = self.alerts_client._get_client()

        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=hours)).isoformat()
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "rule.mitre.id"}},
                        {"range": {"timestamp": {"gte": start}}},
                    ]
                }
            },
            "aggs": {
                "by_technique": {
                    "terms": {"field": "rule.mitre.id", "size": 1000},
                    "aggs": {
                        "latest": {"max": {"field": "timestamp"}},
                        "affected_hosts": {"terms": {"field": "agent.name", "size": 10, "missing": "unknown"}},
                        "associated_rules": {"terms": {"field": "rule.id", "size": 10}},
                        "sample": {"top_hits": {"size": 1, "_source": ["rule.mitre.id", "rule.mitre.tactic"]}},
                    },
                }
            },
        }

        try:
            response = await asyncio.to_thread(client.search, index="wazuh-alerts-*", body=body)
        except Exception as exc:
            raise WazuhServiceError(f"MITRE matrix aggregation failed: {exc}") from exc

        buckets = response.get("aggregations", {}).get("by_technique", {}).get("buckets", [])
        techniques: list[dict[str, Any]] = []
        by_tactic: dict[str, list[dict[str, Any]]] = {}

        for bucket in buckets:
            technique_id = bucket.get("key")
            alert_count = bucket.get("doc_count", 0)
            last_detection = bucket.get("latest", {}).get("value_as_string")

            hosts = [h["key"] for h in bucket.get("affected_hosts", {}).get("buckets", [])]
            rules = [r["key"] for r in bucket.get("associated_rules", {}).get("buckets", [])]

            sample_hits = bucket.get("sample", {}).get("hits", {}).get("hits", [])
            tactic = "Unknown"
            if sample_hits:
                mitre = sample_hits[0].get("_source", {}).get("rule", {}).get("mitre", {})
                ids = mitre.get("id", [])
                tactics = mitre.get("tactic", [])
                if isinstance(ids, str):
                    ids = [ids]
                if isinstance(tactics, str):
                    tactics = [tactics]
                if technique_id in ids:
                    idx = ids.index(technique_id)
                    tactic = tactics[idx] if idx < len(tactics) and tactics[idx] else (tactics[0] if tactics else "Unknown")
                elif tactics:
                    tactic = tactics[0]

            tech = {
                "technique_id": technique_id,
                "name": technique_id,
                "tactic": tactic,
                "detection_status": "detected" if alert_count > 0 else "planned",
                "description": f"MITRE technique {technique_id} observed in {alert_count} alert(s)",
                "alert_count": alert_count,
                "last_detection": last_detection,
                "affected_hosts": hosts,
                "associated_rules": ", ".join(str(r) for r in rules),
            }
            techniques.append(tech)
            by_tactic.setdefault(tactic, []).append(tech)

        total_techniques = len(techniques)
        detected = sum(1 for t in techniques if t["alert_count"] > 0)

        return {
            "tactics": sorted(by_tactic.keys()),
            "matrix": by_tactic,
            "total_techniques": total_techniques,
            "detected_techniques": detected,
            "generated_at": now,
        }

    async def get_attack_map(self, hours: int = 720, size: int = 200) -> dict[str, Any]:
        """Extract attacker source IPs from Wazuh alerts and attempt GeoIP enrichment.

        Returns real data only. If no GeoIP information exists, country is 'Unknown'
        and coordinates are null.
        """
        client = self.alerts_client._get_client()
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=hours)).isoformat()

        body = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"gte": start}}},
                        {"exists": {"field": "data.srcip"}},
                    ],
                    "should": [
                        {"exists": {"field": "GeoLocation"}},
                    ],
                    "minimum_should_match": 0,
                }
            },
            "aggs": {
                "geo_enriched_sources": {
                    "filter": {"exists": {"field": "GeoLocation"}},
                    "aggs": {
                        "unique_sources": {
                            "terms": {"field": "data.srcip", "size": size},
                            "aggs": {
                                "top_hit": {"top_hits": {"size": 1, "_source": ["GeoLocation", "rule.description", "rule.level", "rule.id", "agent.name", "timestamp"]}}
                            }
                        }
                    }
                },
                "all_sources": {
                    "terms": {"field": "data.srcip", "size": size},
                    "aggs": {
                        "top_hit": {"top_hits": {"size": 1, "_source": ["GeoLocation", "rule.description", "rule.level", "rule.id", "agent.name", "timestamp"]}}
                    }
                }
            },
        }

        try:
            response = await asyncio.to_thread(client.search, index="wazuh-alerts-*", body=body)
        except Exception as exc:
            raise WazuhServiceError(f"Attack map query failed: {exc}") from exc

        attacks: list[dict[str, Any]] = []
        seen_ips: set[str] = set()

        # First add GeoIP-enriched sources
        geo_buckets = response.get("aggregations", {}).get("geo_enriched_sources", {}).get("unique_sources", {}).get("buckets", [])
        for bucket in geo_buckets:
            srcip = bucket["key"]
            count = bucket["doc_count"]
            seen_ips.add(srcip)
            top_hit = bucket.get("top_hit", {}).get("hits", {}).get("hits", [])
            src = top_hit[0]["_source"] if top_hit else {}
            rule = src.get("rule", {})
            agent = src.get("agent", {})
            geoip = src.get("GeoLocation", {}) or {}
            country = geoip.get("country_name")
            city = geoip.get("city_name")
            country_code = geoip.get("country_iso_code")
            region = geoip.get("region_name")
            lat = geoip.get("location", {}).get("lat") if isinstance(geoip.get("location"), dict) else None
            lon = geoip.get("location", {}).get("lon") if isinstance(geoip.get("location"), dict) else None

            attacks.append({
                "source_ip": srcip,
                "country": country or "Unknown",
                "country_code": country_code,
                "city": city,
                "region": region,
                "latitude": lat,
                "longitude": lon,
                "rule_description": rule.get("description", ""),
                "rule_level": rule.get("level", 1),
                "rule_id": str(rule.get("id", "")),
                "agent_name": agent.get("name", ""),
                "timestamp": src.get("timestamp"),
                "count": count,
            })

        # Then add top non-geo sources (up to size total)
        all_buckets = response.get("aggregations", {}).get("all_sources", {}).get("buckets", [])
        remaining = size - len(attacks)
        for bucket in all_buckets:
            if remaining <= 0:
                break
            srcip = bucket["key"]
            if srcip in seen_ips:
                continue
            seen_ips.add(srcip)
            count = bucket["doc_count"]
            top_hit = bucket.get("top_hit", {}).get("hits", {}).get("hits", [])
            src = top_hit[0]["_source"] if top_hit else {}
            rule = src.get("rule", {})
            agent = src.get("agent", {})
            attacks.append({
                "source_ip": srcip,
                "country": "Unknown",
                "country_code": None,
                "city": None,
                "region": None,
                "latitude": None,
                "longitude": None,
                "rule_description": rule.get("description", ""),
                "rule_level": rule.get("level", 1),
                "rule_id": str(rule.get("id", "")),
                "agent_name": agent.get("name", ""),
                "timestamp": src.get("timestamp"),
                "count": count,
            })
            remaining -= 1

        has_geoip = any(a["latitude"] is not None for a in attacks)

        return {
            "attacks": attacks,
            "total_unique_sources": len(attacks),
            "has_geoip": has_geoip,
            "generated_at": now,
        }

    async def get_rule_stats(
        self,
        rule_ids: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        try:
            return await self.alerts_client.get_rule_stats(
                rule_ids=rule_ids, start_time=start_time, end_time=end_time
            )
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def get_latest_alerts(self, size: int = 10) -> list[dict[str, Any]]:
        """Get the most recent alerts for live notifications."""
        try:
            return await self.alerts_client.get_alerts(size=size)
        except Exception as exc:
            raise WazuhServiceError(str(exc)) from exc

    async def correlate_incidents(self, hours: int = 24, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        """Cluster Wazuh alerts into correlated incidents based on source IP, destination IP,
        agent, hostname, MITRE technique, rule ID, and time window."""
        client = self.alerts_client._get_client()
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=hours)).isoformat()

        body = {
            "size": 500,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"range": {"timestamp": {"gte": start}}},
        }

        try:
            response = await asyncio.to_thread(client.search, index="wazuh-alerts-*", body=body)
        except Exception as exc:
            raise WazuhServiceError(f"Incident correlation query failed: {exc}") from exc

        hits = response.get("hits", {}).get("hits", [])
        alerts = []
        for hit in hits:
            src = hit.get("_source", {})
            data = src.get("data", {})
            rule = src.get("rule", {})
            agent = src.get("agent", {})
            mitre = rule.get("mitre", {}) or {}
            techniques = mitre.get("id", [])
            if isinstance(techniques, str):
                techniques = [techniques]
            alerts.append({
                "timestamp": src.get("timestamp"),
                "rule_id": str(rule.get("id", "")),
                "rule_description": rule.get("description", ""),
                "level": rule.get("level", 1),
                "srcip": data.get("srcip"),
                "dstip": data.get("dstip"),
                "agent_id": agent.get("id"),
                "agent_name": agent.get("name"),
                "mitre_technique": techniques[0] if techniques else None,
                "raw": src,
            })

        # Cluster by multiple dimensions: (srcip, rule_id), (agent, mitre), (srcip, dstip), time-proximity
        clusters: dict[str, list[dict[str, Any]]] = {}
        for alert in alerts:
            keys = []
            if alert["srcip"] and alert["rule_id"]:
                keys.append(f"srcip_rule:{alert['srcip']}:{alert['rule_id']}")
            if alert["agent_name"] and alert["mitre_technique"]:
                keys.append(f"agent_mitre:{alert['agent_name']}:{alert['mitre_technique']}")
            if alert["srcip"] and alert.get("dstip"):
                keys.append(f"src_dst:{alert['srcip']}:{alert['dstip']}")
            if alert["rule_id"] and alert["agent_name"]:
                keys.append(f"rule_agent:{alert['rule_id']}:{alert['agent_name']}")
            if not keys:
                keys.append(f"rule:{alert['rule_id'] or 'unknown'}")

            for key in keys:
                clusters.setdefault(key, []).append(alert)

        # Also cluster by time-proximity: alerts within 5 minutes of each other from same source
        time_window_seconds = 300
        sorted_alerts = sorted(alerts, key=lambda a: a.get("timestamp") or "")
        for i, alert in enumerate(sorted_alerts):
            if not alert["srcip"]:
                continue
            ts_str = alert.get("timestamp")
            if not ts_str:
                continue
            for j in range(i + 1, min(i + 20, len(sorted_alerts))):
                other = sorted_alerts[j]
                if other["srcip"] != alert["srcip"]:
                    continue
                other_ts = other.get("timestamp")
                if not other_ts:
                    continue
                key = f"time_cluster:{alert['srcip']}"
                clusters.setdefault(key, []).extend([alert, other])

        incidents: list[dict[str, Any]] = []
        seen_alerts = set()
        for key, cluster_alerts in clusters.items():
            if len(cluster_alerts) < min_cluster_size:
                continue
            # Deduplicate alerts within cluster
            unique = []
            for a in cluster_alerts:
                aid = f"{a['timestamp']}:{a['rule_id']}:{a.get('srcip', '')}"
                if aid not in seen_alerts:
                    seen_alerts.add(aid)
                    unique.append(a)
            if len(unique) < min_cluster_size:
                continue

            max_level = max(a["level"] for a in unique)
            avg_level = sum(a["level"] for a in unique) / len(unique)
            # Severity escalation: if max level much higher than avg, it's escalating
            escalating = max_level > avg_level + 3
            if max_level >= 13:
                severity = "critical"
            elif max_level >= 10:
                severity = "high"
            elif max_level >= 4:
                severity = "medium"
            else:
                severity = "low"
            if escalating:
                severity = "critical" if severity in ("high", "medium") else severity

            srcips = list({a["srcip"] for a in unique if a["srcip"]})
            agents = list({a["agent_name"] for a in unique if a["agent_name"]})
            rules = list({a["rule_id"] for a in unique if a["rule_id"]})
            mitre_techniques = list({a["mitre_technique"] for a in unique if a["mitre_technique"]})
            timestamps = sorted([a["timestamp"] for a in unique if a["timestamp"]])

            # Extract GeoLocation for source IPs
            geo_locations = []
            for a in unique:
                raw = a.get("raw", {})
                geo = raw.get("GeoLocation", {})
                if geo and geo.get("country_name"):
                    geo_locations.append({
                        "ip": a["srcip"],
                        "country": geo.get("country_name"),
                        "city": geo.get("city_name"),
                        "lat": geo.get("location", {}).get("lat") if isinstance(geo.get("location"), dict) else None,
                        "lon": geo.get("location", {}).get("lon") if isinstance(geo.get("location"), dict) else None,
                    })

            incidents.append({
                "cluster_key": key,
                "name": f"Correlated: {unique[0]['rule_description'][:60]}",
                "severity": severity,
                "status": "open",
                "alert_count": len(unique),
                "max_severity": max_level,
                "avg_severity": round(avg_level, 1),
                "escalating": escalating,
                "source_ips": srcips,
                "agent_names": agents,
                "rule_ids": rules,
                "rule_description": unique[0]["rule_description"],
                "mitre_techniques": mitre_techniques,
                "first_seen": timestamps[0] if timestamps else None,
                "last_seen": timestamps[-1] if timestamps else None,
                "timeline": [{"timestamp": a["timestamp"], "event": a["rule_description"], "level": a["level"]} for a in unique],
                "geo_locations": geo_locations[:10],
                "alerts": unique,
            })

        incidents.sort(key=lambda x: x["alert_count"], reverse=True)
        return incidents

    async def global_search(self, query: str, limit: int = 50) -> dict[str, Any]:
        """Search across alerts, agents, vulnerabilities, and MITRE techniques in OpenSearch."""
        client = self.alerts_client._get_client()
        results: dict[str, list[dict[str, Any]]] = {"alerts": [], "agents": [], "vulnerabilities": [], "techniques": []}

        if not query or len(query) < 2:
            return {"results": results, "total": 0, "query": query}

        # Search alerts
        alert_body = {
            "size": limit,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["rule.description", "data.srcip", "data.dstip", "agent.name", "rule.id", "rule.mitre.id"],
                    "fuzziness": "AUTO",
                }
            },
        }
        try:
            resp = await asyncio.to_thread(client.search, index="wazuh-alerts-*", body=alert_body)
            for hit in resp.get("hits", {}).get("hits", []):
                src = hit.get("_source", {})
                results["alerts"].append({
                    "id": hit.get("_id", ""),
                    "title": src.get("rule", {}).get("description", ""),
                    "severity": src.get("rule", {}).get("level", 1),
                    "timestamp": src.get("timestamp"),
                    "source_ip": src.get("data", {}).get("srcip"),
                    "agent": src.get("agent", {}).get("name"),
                    "type": "alert",
                })
        except Exception as exc:
            logger.error("Search alerts failed: %s", exc)

        # Search vulnerabilities
        vuln_body = {
            "size": limit,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["vulnerability.id", "vulnerability.description", "package.name", "agent.name"],
                    "fuzziness": "AUTO",
                }
            },
        }
        try:
            resp = await asyncio.to_thread(client.search, index="wazuh-states-vulnerabilities-*", body=vuln_body)
            for hit in resp.get("hits", {}).get("hits", []):
                src = hit.get("_source", {})
                results["vulnerabilities"].append({
                    "id": hit.get("_id", ""),
                    "cve": src.get("vulnerability", {}).get("id", ""),
                    "package": src.get("package", {}).get("name", ""),
                    "agent": src.get("agent", {}).get("name", ""),
                    "type": "vulnerability",
                })
        except Exception as exc:
            logger.error("Search vulnerabilities failed: %s", exc)

        # Search agents via Wazuh API
        try:
            agents_resp = await self.get_agents(limit=500)
            agent_items = agents_resp.get("data", {}).get("affected_items", [])
            q_lower = query.lower()
            for agent in agent_items:
                name = (agent.get("name") or "").lower()
                ip = (agent.get("ip") or "").lower()
                if q_lower in name or q_lower in ip:
                    results["agents"].append({
                        "id": agent.get("id"),
                        "name": agent.get("name"),
                        "ip": agent.get("ip"),
                        "status": agent.get("status"),
                        "type": "agent",
                    })
        except Exception as exc:
            logger.error("Search agents failed: %s", exc)

        total = sum(len(v) for v in results.values())
        return {"results": results, "total": total, "query": query}

    async def normalize_alert(self, raw_alert: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw Wazuh/OpenSearch alert into the platform schema."""
        rule = raw_alert.get("rule", {}) or {}
        agent = raw_alert.get("agent", {}) or {}
        data = raw_alert.get("data", {}) or {}
        source = data.get("srcip") or raw_alert.get("srcip") or agent.get("ip")
        destination = data.get("dstip") or raw_alert.get("dstip")

        mitre = rule.get("mitre", {}) or {}
        techniques = mitre.get("id", [])
        if isinstance(techniques, str):
            techniques = [techniques]
        tactics = mitre.get("tactic", [])
        if isinstance(tactics, str):
            tactics = [tactics]

        return {
            "wazuh_alert_id": str(raw_alert.get("id", "")) or str(hash(json.dumps(raw_alert, sort_keys=True))),
            "title": rule.get("description", "Wazuh Alert"),
            "description": rule.get("comment", ""),
            "severity": int(rule.get("level", 1)),
            "source_ip": source,
            "destination_ip": destination,
            "rule_id": str(rule.get("id", "")),
            "mitre_technique": techniques[0] if techniques else None,
            "mitre_tactic": tactics[0] if tactics else None,
            "status": "new",
            "raw_log": json.dumps(raw_alert),
            "timestamp": raw_alert.get("timestamp"),
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
        }
