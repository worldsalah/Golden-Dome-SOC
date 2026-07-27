import logging
from collections import deque
from datetime import datetime, timedelta

from app.utils.datetime_helper import utc_now
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AnalystUser, DBDependency
from app.schemas.ai import (
    AlertAnalysisRequest,
    AlertAnalysisResponse,
    AnomalyDetectionResponse,
    ChatRequest,
    ChatResponse,
    DailyReportResponse,
    FeedbackListResponse,
    FeedbackRequest,
    FeedbackResponse,
    HistoryResponse,
    IncidentInvestigationRequest,
    IncidentInvestigationResponse,
    PlaybookGenerationRequest,
    PlaybookGenerationResponse,
    QueryLogResponse,
    ThreatHuntRequest,
    ThreatHuntResponse,
)
from app.services.ai_engine.analysis import SentinelAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["Sentinel AI"])

_AI_RATE_LIMIT_PER_MINUTE = 60
_rate_buckets: dict[str, deque[float]] = {}


def get_analysis_service(db: DBDependency) -> SentinelAnalysisService:
    return SentinelAnalysisService(db)


AnalysisService = Annotated[SentinelAnalysisService, Depends(get_analysis_service)]


async def ai_rate_limit(current_user: AnalystUser) -> None:
    """Simple per-user sliding-window rate limit for AI endpoints."""
    key = f"ai:user:{current_user.id}"
    now = utc_now().timestamp()
    window = _rate_buckets.setdefault(key, deque())
    cutoff = now - 60
    while window and window[0] < cutoff:
        window.popleft()
    if len(window) >= _AI_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI rate limit exceeded. Please slow down.",
        )
    window.append(now)


RateLimit = Depends(ai_rate_limit)


@router.post("/analyze-alert", response_model=AlertAnalysisResponse, dependencies=[RateLimit])
async def analyze_alert(
    payload: AlertAnalysisRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.analyze_alert(payload.alert_id, persist=True, user_id=current_user.id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("AI analysis failed for alert %s", payload.alert_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis engine error: {exc}",
        )


@router.post("/chat", response_model=ChatResponse, dependencies=[RateLimit])
async def chat(
    payload: ChatRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.chat(payload.question, alert_id=payload.alert_id, user_id=current_user.id)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("AI chat failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat engine error: {exc}",
        )


@router.get("/health")
async def ai_health(service: AnalysisService):
    health = await service.model.health()
    return {"ollama": health}


@router.post("/investigate-incident", response_model=IncidentInvestigationResponse, dependencies=[RateLimit])
async def investigate_incident(
    payload: IncidentInvestigationRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.investigate_incident(payload.incident_id, user_id=current_user.id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Incident investigation failed for incident %s", payload.incident_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation engine error: {exc}",
        )


@router.post("/threat-hunt", response_model=ThreatHuntResponse, dependencies=[RateLimit])
async def threat_hunt(
    payload: ThreatHuntRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.threat_hunt(payload.query, user_id=current_user.id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Threat hunt query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat hunt engine error: {exc}",
        )


@router.post("/generate-playbook", response_model=PlaybookGenerationResponse, dependencies=[RateLimit])
async def generate_playbook(
    payload: PlaybookGenerationRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.generate_playbook(
            payload.alert_description, payload.mitre_technique, payload.severity, user_id=current_user.id
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Playbook generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Playbook generation error: {exc}",
        )


@router.post("/generate-report", response_model=DailyReportResponse, dependencies=[RateLimit])
async def generate_report(
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        result = await service.generate_daily_report(user_id=current_user.id)
        return result
    except Exception as exc:
        logger.exception("Daily report generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {exc}",
        )


@router.post("/feedback", response_model=FeedbackResponse, dependencies=[RateLimit])
async def submit_feedback(
    payload: FeedbackRequest,
    current_user: AnalystUser,
    service: AnalysisService,
):
    try:
        feedback = await service.submit_feedback(
            payload.analysis_id,
            current_user.id,
            payload.helpful,
            payload.incorrect,
            payload.comment,
        )
        return {"feedback_id": feedback.id, "status": "recorded"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Feedback submission failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback error: {exc}",
        )


@router.get("/feedback", response_model=FeedbackListResponse)
async def ai_feedback(
    current_user: AnalystUser,
    service: AnalysisService,
    limit: int = 100,
):
    try:
        return {"data": await service.get_feedback(limit=min(limit, 1000))}
    except Exception as exc:
        logger.exception("Failed to retrieve AI feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback retrieval error: {exc}",
        )


@router.get("/history", response_model=HistoryResponse)
async def ai_history(
    current_user: AnalystUser,
    service: AnalysisService,
    limit: int = 100,
):
    return {"data": await service.get_history(limit=min(limit, 1000))}


@router.get("/audit-logs", response_model=QueryLogResponse)
async def ai_audit_logs(
    current_user: AnalystUser,
    service: AnalysisService,
    limit: int = 100,
):
    return {"data": await service.get_query_logs(limit=min(limit, 1000))}


@router.get("/anomalies", response_model=AnomalyDetectionResponse)
async def ai_anomalies(
    current_user: AnalystUser,
    service: AnalysisService,
    hours: int = 168,
):
    try:
        return await service.detect_anomalies(hours=max(1, min(hours, 720)))
    except Exception as exc:
        logger.exception("Anomaly detection failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection error: {exc}",
        )
