from __future__ import annotations

from eligibility.engine import evaluate_eligibility
from eligibility.models import EligibilityResponse, UserProfile
from eligibility.ollama_reasoner import generate_spoken_eligibility_response
from eligibility.query import structure_query
from eligibility.tree_rag import tree_top_down_retrieve
from voice.formatting import tts_optimize


def run_eligibility_pipeline(raw_text: str, profile: UserProfile, confidence: float = 0.0) -> EligibilityResponse:
    structured = structure_query(raw_text, confidence=confidence)
    eligibility = evaluate_eligibility(profile, structured.cleaned_query)
    retrieved = tree_top_down_retrieve(structured.cleaned_query, k=4, profile=profile.model_dump())
    response_text = generate_spoken_eligibility_response(profile, structured.cleaned_query, eligibility)
    tts_text = tts_optimize(response_text)

    return EligibilityResponse(
        raw_transcript=structured.raw_transcript,
        cleaned_query=structured.cleaned_query,
        confidence=structured.confidence,
        eligibility=eligibility,
        retrieved_context=[
            {
                "id": x.id,
                "name": x.name,
                "description": x.description,
                "category_path": x.category_path,
                "attributes": x.attributes,
            }
            for x in retrieved
        ],
        response_text=response_text,
        tts_text=tts_text,
    )
