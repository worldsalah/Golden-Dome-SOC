"""Security posture management API."""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import DBDependency, AnalystUser, ViewerUser
from app.services.posture import PostureManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/posture", tags=["Security Posture"])


@router.get("")
async def get_posture(
    current_user: ViewerUser,
    db: DBDependency,
):
    """Get comprehensive security posture for the current organization."""
    manager = PostureManager(db, tenant_id=current_user.organization_id)
    return await manager.get_posture()
