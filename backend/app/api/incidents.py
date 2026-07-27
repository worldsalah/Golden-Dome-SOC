import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, AnalystUser, CurrentUser
from app.database.database import get_db
from app.database.models import Alert, Incident, IncidentStatus, IncidentTimeline
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate, TimelineNoteCreate
from app.schemas.report import IncidentReportRequest
from app.services.ai_engine.report_generator import IncidentReportGenerator


from app.utils.datetime_helper import utc_now
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=dict)
async def list_incidents(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 20,
):
    total_result = await db.execute(select(Incident))
    total = len(total_result.scalars().all())

    result = await db.execute(
        select(Incident)
        .offset((page - 1) * limit)
        .limit(limit)
        .order_by(Incident.created_at.desc())
    )
    incidents = result.scalars().all()
    return {
        "data": [IncidentRead.model_validate(i) for i in incidents],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await db.refresh(incident, ["timeline", "alerts"])
    return incident


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    incident = Incident(
        name=payload.name,
        severity=payload.severity,
        status=payload.status,
        description=payload.description,
        assigned_user_id=payload.assigned_user_id,
    )
    db.add(incident)
    await db.flush()

    if payload.alert_ids:
        alerts_result = await db.execute(select(Alert).where(Alert.id.in_(payload.alert_ids)))
        alerts = alerts_result.scalars().all()
        incident.alerts.extend(alerts)

    timeline_event = IncidentTimeline(
        incident_id=incident.id,
        actor_id=current_user.id,
        action="created",
        note=f"Incident created by {current_user.username}",
    )
    db.add(timeline_event)
    await db.commit()
    await db.refresh(incident)
    logger.info("Incident created: %s by user %s", incident.name, current_user.username)
    return incident


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    update_data = payload.model_dump(exclude_unset=True)
    old_status = incident.status

    for field, value in update_data.items():
        setattr(incident, field, value)

    if payload.status == IncidentStatus.RESOLVED.value and old_status != IncidentStatus.RESOLVED.value:
        incident.resolved_at = utc_now()
        timeline_note = f"Incident resolved by {current_user.username}"
    else:
        timeline_note = f"Incident updated by {current_user.username}"

    timeline_event = IncidentTimeline(
        incident_id=incident.id,
        actor_id=current_user.id,
        action="updated",
        note=timeline_note,
    )
    db.add(timeline_event)
    await db.commit()
    await db.refresh(incident)
    logger.info("Incident updated: %s by user %s", incident.name, current_user.username)
    return incident


@router.post("/{incident_id}/timeline", response_model=IncidentRead)
async def add_timeline_note(
    incident_id: int,
    payload: TimelineNoteCreate,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    note = IncidentTimeline(
        incident_id=incident.id,
        actor_id=current_user.id,
        action="note",
        note=payload.note,
    )
    db.add(note)
    await db.commit()
    await db.refresh(incident)
    await db.refresh(incident, ["timeline", "alerts"])
    logger.info("Timeline note added to incident %d by %s", incident.id, current_user.username)
    return incident


@router.post("/{incident_id}/assign", response_model=IncidentRead)
async def assign_incident(
    incident_id: int,
    user_id: int,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    from app.database.models import User
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    incident.assigned_user_id = user_id
    timeline_event = IncidentTimeline(
        incident_id=incident.id,
        actor_id=current_user.id,
        action="assigned",
        note=f"Assigned to {user.username} by {current_user.username}",
    )
    db.add(timeline_event)
    await db.commit()
    await db.refresh(incident)
    await db.refresh(incident, ["timeline", "alerts"])
    logger.info("Incident %d assigned to %s by %s", incident.id, user.username, current_user.username)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await db.delete(incident)
    await db.commit()
    logger.info("Incident deleted: %s by user %s", incident.name, current_user.username)
    return None


@router.post("/{incident_id}/generate-report")
async def generate_incident_report(
    incident_id: int,
    current_user: AnalystUser,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    generator = IncidentReportGenerator(db)
    report = await generator.generate(incident)
    markdown_report = generator.to_markdown(report["report"])
    pdf_bytes = generator.to_pdf(report["report"])

    return {
        "report": report["report"],
        "llm_source": report["llm_source"],
        "generated_at": report["generated_at"],
        "markdown": markdown_report,
        "pdf_base64": pdf_bytes.hex() if isinstance(pdf_bytes, bytes) else None,
    }
