from __future__ import annotations

from fastapi import APIRouter

from eligibility.models import EligibilityRequest, EligibilityResponse
from eligibility.service import run_eligibility_pipeline

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


@router.post("/query", response_model=EligibilityResponse)
def eligibility_query(body: EligibilityRequest):
    return run_eligibility_pipeline(
        raw_text=body.query,
        profile=body.user_profile,
        confidence=0.9,
    )
