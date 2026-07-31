import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.validation import AttackCoverageResponse, DetectionPerformanceResponse, EvidenceSearchResponse, FalsePositiveAnalysisResponse, ReplayAlertResponse, RuleOptimizerResponse, SocHealthScoreResponse, ValidationCenterResponse
from app.security.jwt import get_current_user
from app.services.validation_service import ValidationService
from app.services.wazuh_service import WazuhServiceError
from app.security.tenant import ensure_tenant_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/validation", tags=["Detection Validation"])


def _service(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ValidationService:
    return ValidationService(db, tenant_id=current_user.organization_id)


ServiceDep = Annotated[ValidationService, Depends(_service)]


@router.get("/detections", response_model=ValidationCenterResponse)
async def get_validation_center(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to validate"),
):
    """Real-time detection validation data sourced from the Wazuh Manager API and Indexer."""
    try:
        result = await service.get_validation_center(group=group)
    except WazuhServiceError as exc:
        logger.exception("Validation center failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return ValidationCenterResponse(**result)


@router.get("/coverage", response_model=AttackCoverageResponse)
async def get_attack_coverage(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to validate"),
):
    """ATT&CK technique coverage cross-referenced against real Wazuh detections."""
    try:
        result = await service.get_attack_coverage(group=group)
    except WazuhServiceError as exc:
        logger.exception("Attack coverage failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return AttackCoverageResponse(**result)


@router.get("/false-positive-analysis", response_model=FalsePositiveAnalysisResponse)
async def get_false_positive_analysis(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to validate"),
):
    """Real false-positive analysis with automatically generated tuning suggestions."""
    try:
        result = await service.get_false_positive_analysis(group=group)
    except WazuhServiceError as exc:
        logger.exception("False positive analysis failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return FalsePositiveAnalysisResponse(**result)


@router.get("/performance", response_model=DetectionPerformanceResponse)
async def get_detection_performance(
    current_user: CurrentUser,
    service: ServiceDep,
):
    """Real detection pipeline latency and throughput from Wazuh Manager API and Indexer."""
    _ = current_user
    try:
        result = await service.get_detection_performance()
    except WazuhServiceError as exc:
        logger.exception("Detection performance probe failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return DetectionPerformanceResponse(**result)


@router.get("/rule-optimizer", response_model=RuleOptimizerResponse)
async def get_rule_optimizer(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to optimize"),
):
    """Identify rarely/frequently triggered rules and duplicate detection definitions."""
    try:
        result = await service.get_rule_optimizer(group=group)
    except WazuhServiceError as exc:
        logger.exception("Rule optimizer failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return RuleOptimizerResponse(**result)


@router.get("/health-score", response_model=SocHealthScoreResponse)
async def get_soc_health_score(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to score"),
):
    """SOC health grade (A+ to D) derived from real detection, coverage, backlog and performance metrics."""
    try:
        result = await service.get_soc_health_score(group=group)
    except WazuhServiceError as exc:
        logger.exception("SOC health score failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return SocHealthScoreResponse(**result)


@router.get("/reports/pdf")
async def get_validation_report(
    current_user: CurrentUser,
    service: ServiceDep,
    group: str = Query("goldendome", description="Wazuh rule group to include"),
):
    """Download a PDF validation report built from real Wazuh and platform data."""
    try:
        pdf_bytes = await service.generate_validation_report(group=group)
    except WazuhServiceError as exc:
        logger.exception("PDF validation report failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=validation_report.pdf"},
    )


@router.post("/replay/{alert_id}", response_model=ReplayAlertResponse)
async def replay_alert(
    alert_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
    db: AsyncSession = Depends(get_db),
):
    """Replay an existing alert against the current Wazuh rule set (no event is executed)."""
    from app.database.models import Alert
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await ensure_tenant_access(alert.tenant_id, current_user.organization_id)
    try:
        result = await service.replay_alert(alert_id=alert_id)
    except WazuhServiceError as exc:
        logger.exception("Replay failed to reach Wazuh")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wazuh API/Indexer unreachable: {exc}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ReplayAlertResponse(**result)


@router.get("/evidence", response_model=EvidenceSearchResponse)
async def search_evidence(
    current_user: CurrentUser,
    service: ServiceDep,
    q: str | None = Query(None, description="Search term"),
    source: str | None = Query(None, description="Filter by source: alert or workflow_evidence"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Searchable evidence viewer across alert raw logs and workflow evidence."""
    result = await service.search_evidence(query=q, source=source, limit=limit)
    return EvidenceSearchResponse(**result)
