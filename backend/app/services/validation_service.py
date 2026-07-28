import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, AlertStatus, MITRETechnique
from app.services.wazuh_service import WazuhService, WazuhServiceError

logger = logging.getLogger(__name__)

# Rules loaded from wazuh/custom_rules.xml are tagged with this group.
CUSTOM_RULE_GROUP = "goldendome"

RECENT_WINDOW_DAYS = 90
STALE_CONFIDENCE_DAYS = 30


def _extract_mitre_id(rule: dict[str, Any]) -> str | None:
    """Extract the first MITRE technique ID from a Wazuh Manager rule object.

    The Wazuh API returns MITRE data in slightly different shapes depending on
    version (e.g. rule['mitre']['id'] as a list, or nested under 'details').
    """
    mitre = rule.get("mitre")
    if mitre is None:
        details = rule.get("details") or {}
        mitre = details.get("mitre")
    if isinstance(mitre, dict):
        ids = mitre.get("id") or mitre.get("technique") or []
    elif isinstance(mitre, list):
        ids = mitre
    else:
        ids = []
    if isinstance(ids, str):
        ids = [ids]
    return ids[0] if ids else None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


class ValidationService:
    """Computes real Detection Validation metrics from live Wazuh data.

    No values are hardcoded or fabricated: rule definitions and trigger volume
    come from the Wazuh Manager API and Wazuh Indexer; false-positive rates
    come from analyst dispositions already recorded in the platform database.
    """

    def __init__(self, db: AsyncSession, wazuh_service: WazuhService | None = None):
        self.db = db
        self.wazuh = wazuh_service or WazuhService()

    async def _local_disposition_stats(self) -> dict[str, dict[str, int]]:
        """Real false-positive/total counts per rule_id, from analyst-triaged alerts."""
        result = await self.db.execute(
            select(Alert.rule_id, Alert.status, func.count(Alert.id))
            .where(Alert.rule_id.isnot(None))
            .group_by(Alert.rule_id, Alert.status)
        )
        stats: dict[str, dict[str, int]] = {}
        for rule_id, status, count in result.all():
            entry = stats.setdefault(str(rule_id), {"total": 0, "false_positive": 0})
            entry["total"] += count
            if status == AlertStatus.FALSE_POSITIVE.value:
                entry["false_positive"] += count
        return stats

    async def _mitre_status_by_technique(self) -> dict[str, str]:
        result = await self.db.execute(select(MITRETechnique.technique_id, MITRETechnique.detection_status))
        return {tid: status for tid, status in result.all()}

    def _coverage_percentage(self, mitre_id: str | None, alert_count: int, mitre_status: dict[str, str]) -> float:
        if not mitre_id:
            return 0.0
        if alert_count > 0:
            return 100.0
        if mitre_status.get(mitre_id) in ("detected", "partial"):
            return 50.0
        return 0.0

    def _confidence(
        self,
        alert_count: int,
        fp_rate: float | None,
        last_trigger: datetime | None,
        has_mitre: bool,
    ) -> float:
        score = 40.0 if alert_count > 0 else 10.0
        if fp_rate is None:
            score += 15.0
        else:
            score += 30.0 * max(0.0, 1 - fp_rate / 100.0)
        if last_trigger is not None:
            age_days = (datetime.now(timezone.utc) - last_trigger).days
            score += 20.0 if age_days <= STALE_CONFIDENCE_DAYS else 5.0
        if has_mitre:
            score += 10.0
        return round(min(100.0, max(0.0, score)), 1)

    def _validation_status(self, alert_count: int, fp_rate: float | None, last_trigger: datetime | None, rule_status: str) -> str:
        if alert_count == 0:
            return "pending" if rule_status == "enabled" else "no_data"
        age_days = (datetime.now(timezone.utc) - last_trigger).days if last_trigger else None
        if age_days is not None and age_days > RECENT_WINDOW_DAYS:
            return "stale"
        if fp_rate is not None and fp_rate >= 50.0:
            return "failed"
        return "validated"

    async def get_attack_coverage(self, group: str = CUSTOM_RULE_GROUP) -> dict[str, Any]:
        """Cross-reference real Wazuh detections against the real MITRE technique catalog.

        implemented: at least one enabled rule maps to the technique
        validated:   that technique has fired and matches with an acceptable FP rate
        failed:      the mapped rule(s) have a high false-positive rate
        missing:     no rule in the group maps to this technique at all
        """
        validation = await self.get_validation_center(group=group)
        detections = validation["detections"]

        by_technique: dict[str, list[dict[str, Any]]] = {}
        for d in detections:
            tid = d["mitre_technique"]
            if tid:
                by_technique.setdefault(tid, []).append(d)

        result = await self.db.execute(select(MITRETechnique))
        techniques = result.scalars().all()

        entries = []
        tactic_totals: dict[str, dict[str, int]] = {}
        for tech in techniques:
            mapped = by_technique.get(tech.technique_id, [])
            last_trigger = None
            for d in mapped:
                if d["last_trigger"] and (last_trigger is None or d["last_trigger"] > last_trigger):
                    last_trigger = d["last_trigger"]

            if not mapped:
                state = "missing_detection"
            elif any(d["validation_status"] == "failed" for d in mapped):
                state = "failed"
            elif any(d["validation_status"] == "validated" for d in mapped):
                state = "validated"
            else:
                state = "implemented"

            coverage_pct = max((d["coverage_percentage"] for d in mapped), default=0.0)

            entry = {
                "technique_id": tech.technique_id,
                "name": tech.name,
                "tactic": tech.tactic,
                "state": state,
                "mapped_rule_count": len(mapped),
                "mapped_rule_ids": [d["rule_id"] for d in mapped],
                "last_tested": last_trigger,
                "coverage_percentage": coverage_pct,
            }
            entries.append(entry)

            for tactic in [t.strip() for t in tech.tactic.split(",")]:
                bucket = tactic_totals.setdefault(tactic, {"total": 0, "validated": 0, "implemented": 0, "failed": 0, "missing_detection": 0})
                bucket["total"] += 1
                bucket[state] += 1

        total = len(entries)
        validated_count = sum(1 for e in entries if e["state"] == "validated")
        overall_coverage = round((validated_count / total * 100), 1) if total else 0.0

        return {
            "techniques": entries,
            "tactic_summary": tactic_totals,
            "total_techniques": total,
            "validated_techniques": validated_count,
            "overall_coverage_percentage": overall_coverage,
            "data_source": validation["summary"]["data_source"],
            "generated_at": validation["summary"]["generated_at"],
        }

    async def get_validation_center(self, group: str = CUSTOM_RULE_GROUP) -> dict[str, Any]:
        try:
            rules_response = await self.wazuh.get_rules(limit=500, group=group)
        except WazuhServiceError as exc:
            logger.error("Validation center could not reach Wazuh Manager: %s", exc)
            raise

        rules = rules_response.get("data", {}).get("affected_items", [])
        rule_ids = [str(r.get("id")) for r in rules if r.get("id") is not None]

        try:
            rule_stats = await self.wazuh.get_rule_stats(rule_ids=rule_ids) if rule_ids else {}
        except WazuhServiceError as exc:
            logger.error("Validation center could not reach Wazuh Indexer: %s", exc)
            raise

        local_disposition = await self._local_disposition_stats()
        mitre_status = await self._mitre_status_by_technique()

        detections = []
        total_alerts = 0
        fp_rates: list[float] = []
        confidences: list[float] = []
        status_counts = {"validated": 0, "pending": 0, "no_data": 0, "stale": 0, "failed": 0}

        for rule in rules:
            rid = str(rule.get("id"))
            stat = rule_stats.get(rid, {})
            alert_count = int(stat.get("alert_count", 0))
            last_trigger = _parse_timestamp(stat.get("last_trigger"))
            mitre_id = _extract_mitre_id(rule)

            disposition = local_disposition.get(rid)
            fp_rate = None
            fp_sample = 0
            if disposition and disposition["total"] > 0:
                fp_sample = disposition["total"]
                fp_rate = round(disposition["false_positive"] / disposition["total"] * 100, 1)
                fp_rates.append(fp_rate)

            rule_status = rule.get("status", "enabled")
            coverage = self._coverage_percentage(mitre_id, alert_count, mitre_status)
            confidence = self._confidence(alert_count, fp_rate, last_trigger, mitre_id is not None)
            v_status = self._validation_status(alert_count, fp_rate, last_trigger, rule_status)

            status_counts[v_status] = status_counts.get(v_status, 0) + 1
            total_alerts += alert_count
            confidences.append(confidence)

            detections.append({
                "rule_id": rid,
                "detection_name": rule.get("description", f"Rule {rid}"),
                "mitre_technique": mitre_id,
                "severity": int(rule.get("level", 0)),
                "alert_count": alert_count,
                "last_trigger": last_trigger,
                "status": rule_status,
                "validation_status": v_status,
                "coverage_percentage": coverage,
                "false_positive_rate": fp_rate,
                "false_positive_sample_size": fp_sample,
                "detection_confidence": confidence,
                "groups": rule.get("groups", []),
            })

        summary = {
            "total_detections": len(detections),
            "validated": status_counts.get("validated", 0),
            "pending": status_counts.get("pending", 0),
            "no_data": status_counts.get("no_data", 0) + status_counts.get("stale", 0) + status_counts.get("failed", 0),
            "avg_false_positive_rate": round(sum(fp_rates) / len(fp_rates), 1) if fp_rates else None,
            "avg_confidence": round(sum(confidences) / len(confidences), 1) if confidences else 0.0,
            "total_alerts_observed": total_alerts,
            "data_source": f"Wazuh Manager /rules (group={group}) + Wazuh Indexer wazuh-alerts-*",
            "generated_at": datetime.now(timezone.utc),
        }

        return {"summary": summary, "detections": detections}
