import logging
from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DetectionRule, MITRETechnique
from app.schemas.detection_rule import DetectionRuleCreate, DetectionRuleUpdate
from app.security.tenant import tenant_filter

logger = logging.getLogger(__name__)


class DetectionRuleService:
    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        self.db = db
        self.tenant_id = tenant_id

    async def get_rules(
        self,
        page: int = 1,
        limit: int = 100,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[DetectionRule], int]:
        query = select(DetectionRule)
        filt = tenant_filter(DetectionRule, self.tenant_id)
        if filt is not None:
            query = query.where(filt)

        if category:
            query = query.where(DetectionRule.category == category)
        if status:
            query = query.where(DetectionRule.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                DetectionRule.name.ilike(pattern)
                | DetectionRule.description.ilike(pattern)
                | DetectionRule.mitre_attack_id.ilike(pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(desc(DetectionRule.updated_at)).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_rule(self, rule_id: int, tenant_id: int | None = None) -> DetectionRule | None:
        tenant_id = tenant_id or self.tenant_id
        query = select(DetectionRule).where(DetectionRule.id == rule_id)
        filt = tenant_filter(DetectionRule, tenant_id)
        if filt is not None:
            query = query.where(filt)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_rule(self, data: DetectionRuleCreate, created_by: int | None = None, tenant_id: int | None = None) -> DetectionRule:
        rule = DetectionRule(**data.model_dump(), created_by=created_by, tenant_id=tenant_id or self.tenant_id)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        logger.info("Created detection rule %s (id=%d)", rule.name, rule.id)
        return rule

    async def update_rule(self, rule_id: int, data: DetectionRuleUpdate, tenant_id: int | None = None) -> DetectionRule | None:
        rule = await self.get_rule(rule_id, tenant_id=tenant_id)
        if not rule:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)

        await self.db.commit()
        await self.db.refresh(rule)
        logger.info("Updated detection rule %d", rule.id)
        return rule

    async def delete_rule(self, rule_id: int, tenant_id: int | None = None) -> bool:
        rule = await self.get_rule(rule_id, tenant_id=tenant_id)
        if not rule:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        logger.info("Deleted detection rule %d", rule_id)
        return True

    async def test_rule(self, rule: DetectionRule, event: dict) -> dict:
        try:
            code = compile(rule.logic, "<rule_logic>", "eval")
            result = eval(code, {"__builtins__": {}}, {"event": event})
            matched = bool(result)
            reason = f"Rule {'matched' if matched else 'did not match'}"
            return {"matched": matched, "reason": reason, "extracted_fields": {"result": result}}
        except SyntaxError as exc:
            return {"matched": False, "reason": f"Syntax error in rule logic: {exc}", "extracted_fields": {}}
        except Exception as exc:
            return {"matched": False, "reason": f"Evaluation error: {exc}", "extracted_fields": {}}

    async def get_coverage(self) -> dict:
        total_result = await self.db.execute(select(func.count(MITRETechnique.id)))
        total = total_result.scalar_one()

        detected_result = await self.db.execute(
            select(func.count(MITRETechnique.id)).where(
                MITRETechnique.detection_status.in_(["detected", "partial"])
            )
        )
        detected = detected_result.scalar_one()

        tactics_result = await self.db.execute(
            select(MITRETechnique.tactic, func.count(MITRETechnique.id))
            .group_by(MITRETechnique.tactic)
        )
        tactic_coverage = {tactic: count for tactic, count in tactics_result.all()}

        return {
            "total_techniques": total,
            "detected_techniques": detected,
            "coverage_percentage": round((detected / total * 100), 2) if total else 0.0,
            "tactic_coverage": tactic_coverage,
        }

    def to_sigma(self, rule: DetectionRule) -> str:
        lines = [
            "title: " + rule.name,
            "status: " + ("stable" if rule.status == "active" else "experimental"),
            "description: " + (rule.description or "No description"),
            "logsource:",
            "    product: " + (rule.source.lower() if rule.source else "wazuh"),
            "    service: " + (rule.source.lower() if rule.source else "wazuh"),
            "detection:",
            "    condition: see logic in GoldenDome SOC rule #" + str(rule.id),
            "level: " + ("critical" if rule.severity >= 13 else "high" if rule.severity >= 10 else "medium" if rule.severity >= 7 else "low"),
        ]
        if rule.mitre_attack_id:
            lines.append("tags:")
            lines.append("    - attack." + rule.mitre_attack_id.lower().replace(".", ""))
        return "\n".join(lines)

    async def evaluate_scenarios(self, rule: DetectionRule, scenarios: list[dict]) -> dict:
        """Evaluate a rule against multiple labelled scenarios and produce false-positive analysis."""
        results = []
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        for scenario in scenarios:
            event = scenario.get("event", {})
            expected = scenario.get("expected_match", False)
            matched = await self.test_rule(rule, event)
            actual = matched["matched"]
            if actual and expected:
                true_positives += 1
            elif actual and not expected:
                false_positives += 1
            elif not actual and expected:
                false_negatives += 1
            results.append({
                "name": scenario.get("name", "unnamed"),
                "expected": expected,
                "actual": actual,
                "matched": matched,
            })

        total = len(scenarios)
        precision = (true_positives / (true_positives + false_positives)) if (true_positives + false_positives) else 1.0
        recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) else 1.0
        return {
            "total_scenarios": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "recommendation": self._recommendation(false_positives, false_negatives, total),
            "results": results,
        }

    def _recommendation(self, fp: int, fn: int, total: int) -> str:
        if total == 0:
            return "Add detection scenarios to validate rule accuracy."
        if fp == 0 and fn == 0:
            return "Rule performs perfectly across provided scenarios. Monitor production telemetry for drift."
        if fp > fn:
            return "High false-positive rate. Add stricter logic or exclusion conditions."
        if fn > fp:
            return "High false-negative rate. Broaden detection logic or remove overly restrictive checks."
        return "Balanced tuning needed. Review both false positives and false negatives."
