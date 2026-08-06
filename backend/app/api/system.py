"""System information API — powers the first-launch deployment wizard scan."""

from fastapi import APIRouter

from app.api.deps import DeploymentWizardAllowed
from app.services import system_info

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info")
async def system_info_endpoint(current_user: DeploymentWizardAllowed):
    """Return a full snapshot of OS, hardware, Docker, network, and service info."""
    return await system_info.get_full_system_info()
