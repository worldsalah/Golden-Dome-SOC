import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.validation import ValidationCenterResponse
from app.services.validation_service import ValidationService
from app.services.wazuh_service import WazuhServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/validation", tags=["Detection Validation"])


def _service(db: AsyncSession = Depends(get_db)) -> ValidationService:
    return ValidationService(db)


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
