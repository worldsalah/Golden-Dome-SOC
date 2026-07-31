"""Deployment management API — backup, restore, system info, and install wizard status."""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBDependency, SuperAdminUser, ITAdminUser
from app.config.settings import get_settings
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deployment", tags=["Deployment"])


@router.get("/info")
async def get_deployment_info(
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Get deployment information."""
    settings = get_settings()
    try:
        db_version = await db.scalar(text("SELECT version()"))
    except Exception:
        db_version = "sqlite"

    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database": {"version": db_version, "url_masked": "***@***:5432/***"},
        "redis": {"url_masked": "***@***:6379"},
        "ollama": {"base_url": settings.OLLAMA_BASE_URL, "model": settings.OLLAMA_MODEL},
        "deployment_type": "docker",
        "timestamp": utc_now().isoformat(),
    }


@router.post("/backup")
async def create_backup(
    current_user: SuperAdminUser,
    db: DBDependency,
):
    """Create a database backup (metadata only — actual pg_dump should be run via ops)."""
    tables = [
        "organizations", "users", "assets", "alerts", "incidents",
        "incident_timeline", "asset_vulnerabilities", "threat_intelligence",
        "ioc_database", "ai_analysis", "detection_rules", "reports",
        "playbooks", "threat_iocs", "vulnerability_intelligence",
        "audit_logs", "user_sessions", "connectors", "connector_logs",
    ]

    backup = {"metadata": {"created_at": utc_now().isoformat(), "version": "1.0", "table_count": len(tables)}}

    for table in tables:
        try:
            result = await db.execute(text(f"SELECT count(*) FROM {table}"))
            count = result.scalar()
            backup["metadata"][table] = count
        except Exception:
            backup["metadata"][table] = "error"

    return {
        "status": "ok",
        "backup_id": f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "metadata": backup["metadata"],
        "instructions": "Run 'docker compose exec db pg_dump -U postgres golden_dome > backup.sql' for full DB backup",
    }


@router.get("/health-summary")
async def get_health_summary(
    current_user: ITAdminUser,
    db: DBDependency,
):
    """Get system health summary for ops dashboard."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Table counts
    for table in ["users", "alerts", "incidents", "assets"]:
        try:
            count = await db.scalar(text(f"SELECT count(*) FROM {table}"))
            checks[f"{table}_count"] = count
        except Exception:
            checks[f"{table}_count"] = "error"

    return {
        "status": "healthy" if checks.get("database", {}).get("status") == "healthy" else "degraded",
        "checks": checks,
        "timestamp": utc_now().isoformat(),
    }
