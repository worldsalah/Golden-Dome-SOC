import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert, AlertStatus, Incident, IncidentStatus, MITRETechnique, WorkflowEvidence, incident_alert_association
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

    def __init__(self, db: AsyncSession, wazuh_service: WazuhService | None = None, tenant_id: int | None = None):
        self.db = db
        self.wazuh = wazuh_service or WazuhService()
        self.tenant_id = tenant_id

    def _tenant_filter(self, model):
        if self.tenant_id is None:
            return None
        if hasattr(model, "tenant_id"):
            return model.tenant_id == self.tenant_id
        return None

    async def _local_disposition_stats(self) -> dict[str, dict[str, int]]:
        """Real false-positive/total counts per rule_id, from analyst-triaged alerts."""
        stmt = (
            select(Alert.rule_id, Alert.status, func.count(Alert.id))
            .where(Alert.rule_id.isnot(None))
            .group_by(Alert.rule_id, Alert.status)
        )
        filt = self._tenant_filter(Alert)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        stats: dict[str, dict[str, int]] = {}
        for rule_id, status, count in result.all():
            entry = stats.setdefault(str(rule_id), {"total": 0, "false_positive": 0})
            entry["total"] += count
            if status == AlertStatus.FALSE_POSITIVE.value:
                entry["false_positive"] += count
        return stats

    async def _mitre_status_by_technique(self) -> dict[str, str]:
        stmt = select(MITRETechnique.technique_id, MITRETechnique.detection_status)
        filt = self._tenant_filter(MITRETechnique)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
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

    async def _repeated_alert_counts(self) -> dict[str, int]:
        """Real duplicate-noise volume: alerts beyond the first per (rule_id, source_ip) pair."""
        stmt = (
            select(Alert.rule_id, Alert.source_ip, func.count(Alert.id))
            .where(Alert.rule_id.isnot(None), Alert.source_ip.isnot(None))
            .group_by(Alert.rule_id, Alert.source_ip)
        )
        filt = self._tenant_filter(Alert)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        repeated: dict[str, int] = {}
        for rule_id, _source_ip, count in result.all():
            if count > 1:
                repeated[rule_id] = repeated.get(rule_id, 0) + (count - 1)
        return repeated

    async def _open_alert_count(self) -> int:
        """Number of alerts that are still actionable (new/acknowledged/investigating)."""
        stmt = select(func.count(Alert.id)).where(
            Alert.status.notin_([
                AlertStatus.RESOLVED.value,
                AlertStatus.FALSE_POSITIVE.value,
            ])
        )
        filt = self._tenant_filter(Alert)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _open_incident_count(self) -> int:
        """Number of incidents that are not resolved or closed."""
        stmt = select(func.count(Incident.id)).where(
            Incident.status.notin_([
                IncidentStatus.RESOLVED.value,
                IncidentStatus.CLOSED.value,
            ])
        )
        filt = self._tenant_filter(Incident)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _real_incident_counts(self) -> dict[str, int]:
        """Real count of distinct incidents that were actually opened from alerts of each rule."""
        stmt = (
            select(Alert.rule_id, func.count(func.distinct(incident_alert_association.c.incident_id)))
            .join(incident_alert_association, incident_alert_association.c.alert_id == Alert.id)
            .where(Alert.rule_id.isnot(None))
            .group_by(Alert.rule_id)
        )
        filt = self._tenant_filter(Alert)
        if filt is not None:
            stmt = stmt.where(filt)
        result = await self.db.execute(stmt)
        return {rule_id: count for rule_id, count in result.all()}

    def _fp_suggestions(
        self,
        alert_count: int,
        fp_rate: float | None,
        fp_sample: int,
        repeated: int,
        real_incidents: int,
    ) -> list[str]:
        suggestions: list[str] = []
        if fp_rate is not None and fp_sample >= 3:
            if fp_rate >= 50:
                suggestions.append("High false-positive rate — whitelist known-benign source IPs or services generating this noise.")
                suggestions.append("Improve rule regex/decoder field extraction to reduce mismatches.")
            elif fp_rate >= 25:
                suggestions.append("Moderate false-positive rate — consider increasing the alert threshold or frequency count.")
        if alert_count > 0 and repeated / alert_count >= 0.5:
            suggestions.append("High duplicate volume from repeat sources — reduce frequency or widen the correlation timeframe.")
        if alert_count >= 20 and real_incidents == 0:
            suggestions.append("Rule fires frequently but has never produced a confirmed incident — optimize correlation logic or review relevance.")
        if not suggestions and alert_count > 0:
            suggestions.append("No optimization needed — detection is performing within healthy thresholds.")
        return suggestions

    async def get_false_positive_analysis(self, group: str = CUSTOM_RULE_GROUP) -> dict[str, Any]:
        """Part 6: analyze real alert history per rule and generate tuning suggestions."""
        validation = await self.get_validation_center(group=group)
        repeated_counts = await self._repeated_alert_counts()
        incident_counts = await self._real_incident_counts()

        entries = []
        for d in validation["detections"]:
            rid = d["rule_id"]
            repeated = repeated_counts.get(rid, 0)
            real_incidents = incident_counts.get(rid, 0)
            suggestions = self._fp_suggestions(
                d["alert_count"], d["false_positive_rate"], d["false_positive_sample_size"], repeated, real_incidents
            )
            entries.append({
                "rule_id": rid,
                "detection_name": d["detection_name"],
                "alert_count": d["alert_count"],
                "real_incidents": real_incidents,
                "false_positive_count": round(d["false_positive_sample_size"] * (d["false_positive_rate"] or 0) / 100) if d["false_positive_rate"] is not None else 0,
                "false_positive_rate": d["false_positive_rate"],
                "repeated_alerts": repeated,
                "confidence": d["detection_confidence"],
                "suggestions": suggestions,
            })

        entries.sort(key=lambda e: (e["false_positive_rate"] or 0), reverse=True)
        analyzed = [e for e in entries if e["false_positive_rate"] is not None]
        return {
            "rules": entries,
            "total_rules_analyzed": len(entries),
            "rules_with_disposition_data": len(analyzed),
            "avg_false_positive_rate": round(sum(e["false_positive_rate"] for e in analyzed) / len(analyzed), 1) if analyzed else None,
            "data_source": validation["summary"]["data_source"] + " + analyst dispositions + incident linkage",
            "generated_at": validation["summary"]["generated_at"],
        }

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

    async def get_detection_performance(self) -> dict[str, Any]:
        """Real latency and throughput for the Wazuh Manager API, Indexer, and pipeline."""

        async def _timed(coro):
            start = time.perf_counter()
            result = await coro
            return result, (time.perf_counter() - start) * 1000.0
        try:
            _, api_latency_ms = await _timed(self.wazuh.get_rules(limit=1))
        except WazuhServiceError as exc:
            logger.error("Performance probe could not reach Wazuh Manager: %s", exc)
            raise

        try:
            indexer_volume, indexer_latency_ms = await _timed(self.wazuh.get_alert_count(hours=24))
        except WazuhServiceError as exc:
            logger.error("Performance probe could not reach Wazuh Indexer: %s", exc)
            raise

        manager_status = await self.wazuh.get_manager_status()
        manager_stats = await self.wazuh.get_manager_stats()

        items = manager_stats.get("data", {}).get("affected_items", []) if isinstance(manager_stats.get("data"), dict) else []
        latest = items[-1] if isinstance(items, list) and items else {}

        def _int(value: Any) -> int | None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        events_decoded = _int(latest.get("events_decoded"))
        events_dropped = _int(latest.get("events_dropped"))
        alerts_written = _int(latest.get("alerts_written"))

        # /manager/stats/hourly returns hourly aggregates
        events_per_second = round(events_decoded / 3600, 2) if events_decoded is not None else None
        alerts_per_hour = round(alerts_written / 3600, 2) if alerts_written is not None else None
        drop_percentage = round(events_dropped / events_decoded * 100, 2) if (events_decoded and events_dropped is not None) else None

        daemon_health = []
        status_items = manager_status.get("data", {}).get("affected_items", []) if isinstance(manager_status.get("data"), dict) else []
        for item in status_items:
            if isinstance(item, dict):
                for name, status in item.items():
                    daemon_health.append({"name": name, "status": str(status)})

        return {
            "api_latency_ms": round(api_latency_ms, 2),
            "indexer_latency_ms": round(indexer_latency_ms, 2),
            "events_per_second": events_per_second,
            "events_dropped_per_hour": events_dropped,
            "drop_percentage": drop_percentage,
            "alerts_per_hour": alerts_per_hour,
            "alerts_written_24h": alerts_written,
            "indexer_alert_volume_24h": indexer_volume,
            "daemon_health": daemon_health,
            "manager_stats_raw": latest,
            "data_source": "Wazuh Manager API /manager/status + /manager/stats/hourly + Wazuh Indexer wazuh-alerts-*",
            "generated_at": datetime.now(timezone.utc),
        }

    async def get_rule_optimizer(self, group: str = CUSTOM_RULE_GROUP) -> dict[str, Any]:
        """Part 8: identify never/rarely/frequently triggered rules and duplicates for tuning."""
        validation = await self.get_validation_center(group=group)
        repeated_counts = await self._repeated_alert_counts()
        incident_counts = await self._real_incident_counts()

        never_triggered: list[dict[str, Any]] = []
        rarely_triggered: list[dict[str, Any]] = []
        frequently_triggered: list[dict[str, Any]] = []
        inefficient: list[dict[str, Any]] = []
        by_name: dict[str, list[str]] = {}
        by_mitre: dict[str, list[str]] = {}

        for d in validation["detections"]:
            rid = d["rule_id"]
            name = d["detection_name"].strip().lower()
            by_name.setdefault(name, []).append(rid)
            if d["mitre_technique"]:
                by_mitre.setdefault(d["mitre_technique"], []).append(rid)

            count = d["alert_count"]
            if count == 0:
                never_triggered.append({
                    "rule_id": rid,
                    "detection_name": d["detection_name"],
                    "alert_count": 0,
                    "suggestion": "No observed triggers in the analysis window — validate rule logic or retire if no longer relevant.",
                })
            elif count <= 10:
                rarely_triggered.append({
                    "rule_id": rid,
                    "detection_name": d["detection_name"],
                    "alert_count": count,
                    "suggestion": "Low trigger volume — ensure the expected event source is still active and the rule is not too narrow.",
                })
            elif count >= 100:
                frequently_triggered.append({
                    "rule_id": rid,
                    "detection_name": d["detection_name"],
                    "alert_count": count,
                    "repeated_alerts": repeated_counts.get(rid, 0),
                    "suggestion": "High trigger volume — add aggregation, thresholding, or correlation to reduce noise.",
                })

            if count >= 50 and incident_counts.get(rid, 0) == 0:
                inefficient.append({
                    "rule_id": rid,
                    "detection_name": d["detection_name"],
                    "alert_count": count,
                    "suggestion": "Fires frequently but produced no confirmed incidents — tune logic or consider disabling.",
                })

        duplicate_groups: list[dict[str, Any]] = []
        for key, ids in by_name.items():
            if len(ids) > 1:
                duplicate_groups.append({
                    "key": key,
                    "type": "name",
                    "rule_ids": ids,
                    "suggestion": "Duplicate descriptions detected — merge or consolidate overlapping rules.",
                })
        for key, ids in by_mitre.items():
            if len(ids) > 1:
                duplicate_groups.append({
                    "key": key,
                    "type": "mitre",
                    "rule_ids": ids,
                    "suggestion": "Multiple rules map to the same MITRE technique — verify coverage is intentional and not redundant.",
                })

        return {
            "never_triggered": never_triggered,
            "rarely_triggered": rarely_triggered,
            "frequently_triggered": frequently_triggered,
            "inefficient": inefficient,
            "duplicate_groups": duplicate_groups,
            "total_rules": len(validation["detections"]),
            "data_source": validation["summary"]["data_source"],
            "generated_at": validation["summary"]["generated_at"],
        }

    async def get_soc_health_score(self, group: str = CUSTOM_RULE_GROUP) -> dict[str, Any]:
        """Part 10: compute a single A+ to D SOC health grade from real telemetry and backlog."""
        validation = await self.get_validation_center(group=group)
        coverage = await self.get_attack_coverage(group=group)

        total_detections = validation["summary"]["total_detections"]
        validated = validation["summary"]["validated"]
        detection_score = (validated / total_detections * 100) if total_detections else 0.0

        total_techniques = coverage["total_techniques"]
        validated_techniques = coverage["validated_techniques"]
        coverage_score = (validated_techniques / total_techniques * 100) if total_techniques else 0.0

        avg_fp = validation["summary"]["avg_false_positive_rate"]
        fp_score = max(0.0, 100.0 - (avg_fp or 0.0))

        open_alerts = await self._open_alert_count()
        open_incidents = await self._open_incident_count()
        backlog_penalty = min(100.0, open_alerts * 0.5 + open_incidents * 5.0)
        backlog_score = max(0.0, 100.0 - backlog_penalty)

        performance_score = 100.0
        try:
            perf = await self.get_detection_performance()
            daemon_health = perf.get("daemon_health", [])
            unhealthy = sum(1 for d in daemon_health if d.get("status", "").lower() != "running")
            performance_score = max(0.0, 100.0 - unhealthy * 25.0 - min(50.0, perf["api_latency_ms"] / 20.0))
        except WazuhServiceError:
            performance_score = 0.0

        overall = round(
            detection_score * 0.25
            + coverage_score * 0.25
            + fp_score * 0.20
            + backlog_score * 0.15
            + performance_score * 0.15,
            1,
        )

        if overall >= 90:
            grade = "A+"
        elif overall >= 80:
            grade = "A"
        elif overall >= 70:
            grade = "B"
        elif overall >= 60:
            grade = "C"
        else:
            grade = "D"

        return {
            "grade": grade,
            "overall_score": overall,
            "components": {
                "detection_validation": round(detection_score, 1),
                "attack_coverage": round(coverage_score, 1),
                "false_positive_control": round(fp_score, 1),
                "backlog": round(backlog_score, 1),
                "platform_performance": round(performance_score, 1),
            },
            "open_alerts": open_alerts,
            "open_incidents": open_incidents,
            "data_source": "Wazuh Manager API, Wazuh Indexer, and local analyst dispositions",
            "generated_at": datetime.now(timezone.utc),
        }

    async def generate_validation_report(self, group: str = CUSTOM_RULE_GROUP) -> bytes:
        """Part 9: generate a PDF report from real validation, coverage, and health data."""
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        validation = await self.get_validation_center(group=group)
        coverage = await self.get_attack_coverage(group=group)
        fp_analysis = await self.get_false_positive_analysis(group=group)
        perf = None
        try:
            perf = await self.get_detection_performance()
        except WazuhServiceError:
            perf = None
        health = await self.get_soc_health_score(group=group)

        def _table(data, col_widths):
            t = Table(data, colWidths=col_widths)
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c1917")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f4")),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("WORDWRAP", (0, 0), (-1, -1), True),
                    ]
                )
            )
            return t

        styles = getSampleStyleSheet()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, title="Golden Dome SOC - Detection Validation Report")
        story: list[Any] = []

        story.append(Paragraph("Golden Dome SOC - Detection Validation Report", styles["Title"]))
        story.append(Paragraph(f"Generated at {health['generated_at']:%Y-%m-%d %H:%M:%S UTC}", styles["Normal"]))
        story.append(Paragraph(f"Data source: {health['data_source']}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(f"SOC Health Grade: {health['grade']} ({health['overall_score']}/100)", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        comp_data = [["Component", "Score"]] + [
            [k.replace("_", " ").title(), f"{v:.1f}"] for k, v in health["components"].items()
        ]
        story.append(Paragraph("Component Scores", styles["Heading3"]))
        story.append(_table(comp_data, [3.5 * inch, 1.5 * inch]))
        story.append(Spacer(1, 0.1 * inch))

        summary = validation["summary"]
        sum_data = [
            ["Metric", "Value"],
            ["Total detections", str(summary["total_detections"])],
            ["Validated", str(summary["validated"])],
            ["Pending", str(summary["pending"])],
            ["No data / stale / failed", str(summary["no_data"])],
            ["Avg false positive rate", f"{summary['avg_false_positive_rate'] or 'n/a'}%"],
            ["Avg confidence", f"{summary['avg_confidence']:.1f}"],
            ["Total alerts observed", str(summary["total_alerts_observed"])],
        ]
        story.append(Paragraph("Validation Summary", styles["Heading3"]))
        story.append(_table(sum_data, [3.5 * inch, 1.5 * inch]))
        story.append(Spacer(1, 0.1 * inch))

        top = validation["detections"][:15]
        det_data = [["Rule", "Status", "Alerts", "Last Trigger", "FP%", "Confidence"]]
        for d in top:
            det_data.append([
                f"{d['detection_name']} ({d['rule_id']})",
                d["validation_status"],
                str(d["alert_count"]),
                d["last_trigger"].strftime("%Y-%m-%d %H:%M") if d["last_trigger"] else "N/A",
                f"{d['false_positive_rate'] or 'n/a'}",
                f"{d['detection_confidence']:.1f}",
            ])
        story.append(Paragraph("Top Detections", styles["Heading3"]))
        story.append(_table(det_data, [2.4 * inch, 0.8 * inch, 0.7 * inch, 1.2 * inch, 0.6 * inch, 0.9 * inch]))
        story.append(Spacer(1, 0.1 * inch))

        tactic_summary = coverage["tactic_summary"]
        cov_data = [["Tactic", "Total", "Validated", "Implemented", "Failed", "Missing"]]
        for tactic, counts in tactic_summary.items():
            cov_data.append(
                [
                    tactic,
                    str(counts["total"]),
                    str(counts["validated"]),
                    str(counts["implemented"]),
                    str(counts["failed"]),
                    str(counts["missing_detection"]),
                ]
            )
        story.append(Paragraph("ATT&CK Coverage by Tactic", styles["Heading3"]))
        story.append(_table(cov_data, [2.0 * inch, 0.8 * inch, 0.9 * inch, 1.0 * inch, 0.7 * inch, 0.9 * inch]))
        story.append(Spacer(1, 0.1 * inch))

        fp_rules = fp_analysis["rules"][:10]
        fp_data = [["Rule", "Alerts", "FP Rate", "Repeated", "Suggestions"]]
        for r in fp_rules:
            fp_data.append(
                [
                    f"{r['detection_name']} ({r['rule_id']})",
                    str(r["alert_count"]),
                    f"{r['false_positive_rate'] or 'n/a'}%",
                    str(r["repeated_alerts"]),
                    "; ".join(r["suggestions"][:2]),
                ]
            )
        story.append(Paragraph("False Positive Reduction Candidates", styles["Heading3"]))
        story.append(_table(fp_data, [2.1 * inch, 0.6 * inch, 0.7 * inch, 0.7 * inch, 2.4 * inch]))

        if perf:
            perf_data = [
                ["Metric", "Value"],
                ["Manager API latency", f"{perf['api_latency_ms']:.1f} ms"],
                ["Indexer latency", f"{perf['indexer_latency_ms']:.1f} ms"],
                ["Events per second", str(perf["events_per_second"] or "n/a")],
                ["Alerts per hour", str(perf["alerts_per_hour"] or "n/a")],
                ["Indexer alert volume 24h", str(perf["indexer_alert_volume_24h"] or "n/a")],
            ]
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Detection Performance", styles["Heading3"]))
            story.append(_table(perf_data, [3.5 * inch, 1.5 * inch]))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    async def search_evidence(
        self,
        query: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Part 11: searchable evidence viewer across alert raw logs and workflow evidence."""
        results: list[dict[str, Any]] = []

        if source in (None, "alert"):
            stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
            filt = self._tenant_filter(Alert)
            if filt is not None:
                stmt = stmt.where(filt)
            if query:
                pattern = f"%{query}%"
                stmt = stmt.where(
                    or_(
                        Alert.title.ilike(pattern),
                        Alert.description.ilike(pattern),
                        Alert.raw_log.ilike(pattern),
                    )
                )
            alert_rows = await self.db.execute(stmt)
            for a in alert_rows.scalars().all():
                results.append({
                    "id": a.id,
                    "source": "alert",
                    "type": f"alert:{a.status}",
                    "title": a.title,
                    "timestamp": a.created_at,
                    "snippet": (a.description or "")[:200],
                    "rule_id": a.rule_id,
                    "severity": a.severity,
                    "raw": a.raw_log,
                })

        if source in (None, "workflow_evidence"):
            stmt = select(WorkflowEvidence).order_by(WorkflowEvidence.created_at.desc()).limit(limit)
            if query:
                pattern = f"%{query}%"
                stmt = stmt.where(
                    or_(
                        WorkflowEvidence.evidence_type.ilike(pattern),
                        WorkflowEvidence.source.ilike(pattern),
                        WorkflowEvidence.content.ilike(pattern),
                    )
                )
            evidence_rows = await self.db.execute(stmt)
            for e in evidence_rows.scalars().all():
                results.append({
                    "id": e.id,
                    "source": "workflow_evidence",
                    "type": e.evidence_type,
                    "title": e.source or f"Evidence {e.id}",
                    "timestamp": e.created_at,
                    "snippet": (e.content or "")[:200],
                    "file_path": e.file_path,
                    "raw": e.content,
                })

        results.sort(key=lambda x: x["timestamp"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return {
            "evidence": results[:limit],
            "query": query,
            "source": source,
            "total": len(results),
            "data_source": "local alert raw logs and workflow evidence",
            "generated_at": datetime.now(timezone.utc),
        }

    async def replay_alert(self, alert_id: int) -> dict[str, Any]:
        """Part 2: replay an existing Wazuh alert against the current rules loaded on the manager.

        No event is executed: the original raw log is compared to the current rule set and
        the latest indexer statistics to verify whether the detection would still fire today.
        """
        alert = await self.db.get(Alert, alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        raw_log: dict[str, Any] = {}
        if alert.raw_log:
            try:
                raw_log = json.loads(alert.raw_log)
            except json.JSONDecodeError:
                raw_log = {}

        original = raw_log.get("rule", {})
        original_rule_id = str(original.get("id") or alert.rule_id or "")

        now = datetime.now(timezone.utc)
        start_time = (now - timedelta(days=1)).isoformat()

        current_rule: dict[str, Any] | None = None
        stats: dict[str, Any] = {}
        if original_rule_id:
            try:
                rules_response = await self.wazuh.get_rules(limit=1, rule_ids=[original_rule_id])
                current_rules = rules_response.get("data", {}).get("affected_items", [])
                current_rule = current_rules[0] if current_rules else None
                stats = await self.wazuh.get_rule_stats(
                    rule_ids=[original_rule_id],
                    start_time=start_time,
                    end_time=now.isoformat(),
                )
            except WazuhServiceError:
                pass

        stat = stats.get(original_rule_id, {})
        last_trigger = _parse_timestamp(stat.get("last_trigger"))
        match_count_24h = int(stat.get("alert_count", 0))

        if not original_rule_id:
            verdict = "unknown"
            suggestion = "Original alert has no rule identifier; cannot replay against current rules."
        elif current_rule is None:
            verdict = "rule_missing"
            suggestion = "The original Wazuh rule is no longer loaded on the manager; review rule status."
        elif match_count_24h > 0:
            verdict = "still_fires"
            suggestion = "The original rule still fires in the current environment."
        else:
            verdict = "rule_present_no_recent_fire"
            suggestion = "The rule is loaded but has not triggered in the last 24h; verify event source and rule logic."

        return {
            "alert_id": alert.id,
            "original_event": {
                "title": alert.title,
                "rule_id": original_rule_id,
                "severity": alert.severity,
                "timestamp": alert.created_at,
                "raw_log": raw_log,
            },
            "current_rule": current_rule,
            "verdict": verdict,
            "match_count_24h": match_count_24h,
            "last_trigger": last_trigger,
            "suggestions": [suggestion],
            "data_source": "Wazuh Manager API /rules + Wazuh Indexer wazuh-alerts-*",
            "generated_at": now,
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
