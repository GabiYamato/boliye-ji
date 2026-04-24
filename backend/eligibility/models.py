from __future__ import annotations

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    age: int | None = None
    income: int | None = None
    location: str = "india"
    category: str = "general"


class StructuredQuery(BaseModel):
    raw_transcript: str
    cleaned_query: str
    confidence: float = 0.0


class SchemeCandidate(BaseModel):
    id: str
    name: str
    description: str
    category_path: list[str] = Field(default_factory=list)
    rule_match_score: float = 0.0
    semantic_relevance_score: float = 0.0
    final_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class EligibilityResult(BaseModel):
    eligible_schemes: list[SchemeCandidate] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)


class EligibilityRequest(BaseModel):
    query: str
    user_profile: UserProfile


class RetrievedContextNode(BaseModel):
    id: str
    name: str
    description: str
    category_path: list[str] = Field(default_factory=list)
    attributes: dict = Field(default_factory=dict)


class EligibilityResponse(BaseModel):
    raw_transcript: str
    cleaned_query: str
    confidence: float
    eligibility: EligibilityResult
    retrieved_context: list[RetrievedContextNode] = Field(default_factory=list)
    response_text: str
    tts_text: str
