import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, AnalystUser, CurrentUser
from app.database.database import get_db
from app.schemas.soar import (
    PlaybookCreate,
    PlaybookExecutionRead,
    PlaybookRead,
    PlaybookRunRequest,
    PlaybookUpdate,
    SOARStatistics,
    WorkflowActionLogRead,
    WorkflowApprovalCreate,
    WorkflowApprovalDecision,
    WorkflowApprovalRead,
    WorkflowEvidenceRead,
    WorkflowTimelineEventRead,
)
from app.services.soar_service import SoarService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/soar", tags=["SOAR"])


def _service(db: AsyncSession = Depends(get_db)) -> SoarService:
    return SoarService(db)


ServiceDep = Annotated[SoarService, Depends(_service)]


@router.get("/playbooks", response_model=dict)
async def list_playbooks(
    current_user: CurrentUser,
    service: ServiceDep,
    page: int = 1,
    limit: int = 100,
    status: str | None = None,
):
    playbooks, total = await service.get_playbooks(page=page, limit=limit, status=status)
    return {
        "data": [PlaybookRead.model_validate(p) for p in playbooks],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get("/playbooks/action-types", response_model=list[str])
async def list_action_types(
    current_user: CurrentUser,
    service: ServiceDep,
):
    return service.list_action_types()


@router.get("/playbooks/{playbook_id}/export", response_model=dict)
async def export_playbook(
    playbook_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    data = await service.export_playbook(playbook_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return data


@router.post("/playbooks/import", response_model=PlaybookRead, status_code=status.HTTP_201_CREATED)
async def import_playbook(
    payload: dict,
    current_user: AnalystUser,
    service: ServiceDep,
):
    playbook = await service.import_playbook(payload, created_by=current_user.id)
    return PlaybookRead.model_validate(playbook)


@router.post("/playbooks", response_model=PlaybookRead, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    data: PlaybookCreate,
    current_user: AnalystUser,
    service: ServiceDep,
):
    playbook = await service.create_playbook(data.model_dump(), created_by=current_user.id)
    return PlaybookRead.model_validate(playbook)


@router.get("/playbooks/{playbook_id}", response_model=PlaybookRead)
async def get_playbook(
    playbook_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    playbook = await service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return PlaybookRead.model_validate(playbook)


@router.patch("/playbooks/{playbook_id}", response_model=PlaybookRead)
async def update_playbook(
    playbook_id: int,
    data: PlaybookUpdate,
    current_user: AnalystUser,
    service: ServiceDep,
):
    try:
        playbook = await service.update_playbook(playbook_id, data.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not playbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return PlaybookRead.model_validate(playbook)


@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: int,
    current_user: AdminUser,
    service: ServiceDep,
):
    try:
        deleted = await service.delete_playbook(playbook_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")


@router.post("/playbooks/{playbook_id}/run", response_model=PlaybookExecutionRead)
async def run_playbook(
    playbook_id: int,
    payload: PlaybookRunRequest,
    current_user: AnalystUser,
    service: ServiceDep,
):
    playbook = await service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    if playbook.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Playbook is not active")
    execution = await service.execute_playbook(
        playbook,
        triggered_by=current_user.username,
        input_data=payload.input_data,
        trigger_event=payload.trigger_event,
    )
    return PlaybookExecutionRead.model_validate(execution)


@router.get("/executions", response_model=dict)
async def list_executions(
    current_user: CurrentUser,
    service: ServiceDep,
    playbook_id: int | None = None,
    limit: int = 100,
):
    executions = await service.get_executions(playbook_id=playbook_id, limit=limit)
    return {
        "data": [PlaybookExecutionRead.model_validate(e) for e in executions],
        "meta": {"total": len(executions)},
    }


@router.get("/executions/{execution_id}", response_model=PlaybookExecutionRead)
async def get_execution(
    execution_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    execution = await service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return PlaybookExecutionRead.model_validate(execution)


@router.get("/executions/{execution_id}/timeline", response_model=list[WorkflowTimelineEventRead])
async def get_execution_timeline(
    execution_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    events = await service.get_execution_timeline(execution_id)
    return [WorkflowTimelineEventRead.model_validate(e) for e in events]


@router.get("/executions/{execution_id}/evidence", response_model=list[WorkflowEvidenceRead])
async def get_execution_evidence(
    execution_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    evidence = await service.get_execution_evidence(execution_id)
    return [WorkflowEvidenceRead.model_validate(e) for e in evidence]


@router.get("/executions/{execution_id}/logs", response_model=list[WorkflowActionLogRead])
async def get_execution_logs(
    execution_id: int,
    current_user: CurrentUser,
    service: ServiceDep,
):
    logs = await service.get_execution_action_logs(execution_id)
    return [WorkflowActionLogRead.model_validate(lg) for lg in logs]


@router.get("/approvals", response_model=list[WorkflowApprovalRead])
async def list_approvals(
    current_user: CurrentUser,
    service: ServiceDep,
    status: str | None = Query(None),
    limit: int = 100,
):
    approvals = await service.get_pending_approvals(limit=limit) if status == "pending" else []
    return [WorkflowApprovalRead.model_validate(a) for a in approvals]


@router.post("/approvals/{approval_id}/decision", response_model=WorkflowApprovalRead)
async def approve_playbook_action(
    approval_id: int,
    decision: WorkflowApprovalDecision,
    current_user: AnalystUser,
    service: ServiceDep,
):
    approval = await service.approve_execution_node(
        approval_id, decision.decision, user=current_user.username
    )
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return WorkflowApprovalRead.model_validate(approval)


@router.get("/statistics", response_model=SOARStatistics)
async def soar_statistics(
    current_user: CurrentUser,
    service: ServiceDep,
):
    return SOARStatistics.model_validate(await service.get_statistics())
