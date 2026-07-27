from pydantic import BaseModel, Field


class RiskScoreResponse(BaseModel):
    target_type: str
    target_id: int
    score: int = Field(..., ge=0, le=100)
    classification: str
    reason: dict
