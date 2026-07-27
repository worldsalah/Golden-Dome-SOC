import logging
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.database.database import get_db
from app.database.models import Alert, MITRETechnique
from app.schemas.mitre import MitreCoverage, MitreTechniqueRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mitre", tags=["MITRE ATT&CK"])

# Minimal static mapping for known techniques. Sprint 5 can expand this.
_TECHNIQUE_CATALOG = {
    "T1046": ("Network Service Discovery", "Discovery"),
    "T1190": ("Exploit Public-Facing Application", "Initial Access"),
    "T1071.004": ("Application Layer Protocol: DNS", "Command and Control"),
    "T1110": ("Brute Force", "Credential Access"),
    "T1003": ("OS Credential Dumping", "Credential Access"),
    "T1059": ("Command and Scripting Interpreter", "Execution"),
    "T1083": ("File and Directory Discovery", "Discovery"),
    "T1021": ("Remote Services", "Lateral Movement"),
    "T1078": ("Valid Accounts", "Initial Access"),
}


@router.get("/techniques", response_model=dict)
async def list_techniques(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert.mitre_technique, func.count(Alert.id))
        .where(Alert.mitre_technique.isnot(None))
        .group_by(Alert.mitre_technique)
    )
    counts = defaultdict(int)
    for technique, count in result.all():
        counts[technique] = count

    db_result = await db.execute(select(MITRETechnique))
    db_techniques = {t.technique_id: t for t in db_result.scalars().all()}

    techniques = []
    for tid, info in _TECHNIQUE_CATALOG.items():
        name, tactic = info
        techniques.append(
            MitreTechniqueRead(
                technique_id=tid,
                name=name,
                tactic=tactic,
                alert_count=counts.get(tid, 0),
            )
        )

    for tid, tech in db_techniques.items():
        if tid not in _TECHNIQUE_CATALOG:
            techniques.append(
                MitreTechniqueRead(
                    technique_id=tech.technique_id,
                    name=tech.name,
                    tactic=tech.tactic,
                    alert_count=counts.get(tid, 0),
                )
            )

    return {"data": techniques}


@router.get("/matrix", response_model=dict)
async def get_matrix(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return all MITRE techniques grouped by tactic for the interactive matrix."""
    result = await db.execute(select(MITRETechnique))
    techniques = result.scalars().all()

    result = await db.execute(
        select(Alert.mitre_technique, func.count(Alert.id))
        .where(Alert.mitre_technique.isnot(None))
        .group_by(Alert.mitre_technique)
    )
    counts = {tid: count for tid, count in result.all()}

    by_tactic: dict[str, list[dict]] = defaultdict(list)
    for tech in techniques:
        for tactic in [t.strip() for t in tech.tactic.split(",")]:
            by_tactic[tactic].append({
                "technique_id": tech.technique_id,
                "name": tech.name,
                "detection_status": tech.detection_status,
                "description": tech.description,
                "alert_count": counts.get(tech.technique_id, 0),
                "associated_rules": tech.associated_rules,
            })

    return {
        "tactics": sorted(by_tactic.keys()),
        "matrix": dict(by_tactic),
        "total_techniques": len(techniques),
        "detected_techniques": len([t for t in techniques if t.detection_status in ("detected", "partial")]),
    }


@router.get("/coverage", response_model=MitreCoverage)
async def get_coverage(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MITRETechnique))
    techniques = result.scalars().all()
    total = len(techniques)
    detected = [t for t in techniques if t.detection_status in ("detected", "partial")]
    tactics = {t.strip() for tech in techniques for t in tech.tactic.split(",")}
    coverage = (len(detected) / total * 100) if total else 0.0
    return MitreCoverage(
        total_techniques=total,
        detected_techniques=len(detected),
        coverage_percentage=round(coverage, 2),
        tactics=sorted(tactics),
    )
