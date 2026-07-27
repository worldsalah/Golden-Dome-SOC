import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnalystUser, CurrentUser, get_db
from app.schemas.detection_rule import (
    DetectionRuleCreate,
    DetectionRuleRead,
    DetectionRuleScenarioEvaluation,
    DetectionRuleScenarioRequest,
    DetectionRuleTestRequest,
    DetectionRuleTestResult,
    DetectionRuleUpdate,
)
from app.services.detection_rule_service import DetectionRuleService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/detection-rules", tags=["Detection Rules"])


def _service(db: AsyncSession = Depends(get_db)) -> DetectionRuleService:
    return DetectionRuleService(db)


ServiceDep = Annotated[DetectionRuleService, Depends(_service)]


@router.get("", response_model=dict)
async def list_rules(
    current_user: CurrentUser,
    service: ServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
):
    rules, total = await service.get_rules(page=page, limit=limit, category=category, status=status, search=search)
    return {
        "data": [DetectionRuleRead.model_validate(r) for r in rules],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("", response_model=DetectionRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: DetectionRuleCreate,
    current_user: AnalystUser,
    service: ServiceDep,
):
    return DetectionRuleRead.model_validate(
        await service.create_rule(data, created_by=current_user.id)
    )


@router.get("/{rule_id}", response_model=DetectionRuleRead)
async def get_rule(
    rule_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return DetectionRuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=DetectionRuleRead)
async def update_rule(
    rule_id: int,
    data: DetectionRuleUpdate,
    current_user: AnalystUser,
    service: ServiceDep,
):
    rule = await service.update_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return DetectionRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    current_user: AnalystUser,
    service: ServiceDep,
):
    deleted = await service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@router.post("/{rule_id}/test", response_model=DetectionRuleTestResult)
async def test_rule(
    rule_id: int,
    payload: DetectionRuleTestRequest,
    current_user: CurrentUser,
    service: ServiceDep,
):
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    result = await service.test_rule(rule, payload.event)
    return DetectionRuleTestResult(**result)


@router.patch("/{rule_id}/toggle", response_model=DetectionRuleRead)
async def toggle_rule_status(
    rule_id: int,
    current_user: AnalystUser,
    service: ServiceDep,
):
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    new_status = "disabled" if rule.status == "active" else "active"
    updated = await service.update_rule(rule_id, DetectionRuleUpdate(status=new_status))
    return DetectionRuleRead.model_validate(updated)


@router.get("/coverage/summary")
async def coverage_summary(
    current_user: CurrentUser,
    service: ServiceDep,
):
    return await service.get_coverage()


@router.get("/{rule_id}/sigma")
async def export_rule_to_sigma(
    rule_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return {"rule_id": rule_id, "sigma_yaml": service.to_sigma(rule)}


@router.post("/{rule_id}/evaluate-scenarios", response_model=DetectionRuleScenarioEvaluation)
async def evaluate_rule_scenarios(
    rule_id: int,
    payload: DetectionRuleScenarioRequest,
    current_user: CurrentUser,
    service: ServiceDep,
):
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    scenarios = [s.model_dump() for s in payload.scenarios]
    result = await service.evaluate_scenarios(rule, scenarios)
    return DetectionRuleScenarioEvaluation(**result)
