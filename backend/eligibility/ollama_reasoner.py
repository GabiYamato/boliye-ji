"""Spoken eligibility response generator using the pluggable LLM provider.

Replaces the old ollama_reasoner.py that was hardcoded to Ollama.
"""
from __future__ import annotations

import json

from providers.registry import get_llm
from eligibility.models import EligibilityResult, UserProfile


SYSTEM_PROMPT = """
You are a voice-first eligibility assistant for Indian public schemes.
Rules:
- Use short spoken sentences.
- Do not use abbreviations.
- Keep wording simple and natural for text to speech.
- Add clear pauses using commas and periods.
- Mention eligibility reasons and next steps.
- If no scheme is eligible, explain why and suggest what information is missing.
- Return plain text only. No bullet symbols, no markdown, no code fences.
- Keep each sentence short. Prefer one idea per sentence.
""".strip()


def generate_spoken_eligibility_response(
    profile: UserProfile,
    query: str,
    eligibility: EligibilityResult,
) -> str:
    payload = {
        "user_profile": profile.model_dump(),
        "query": query,
        "retrieved_context": [s.model_dump() for s in eligibility.eligible_schemes],
        "instructions": "Generate a spoken response",
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        llm = get_llm()
        text = llm.chat(messages)
        if text:
            return text
    except Exception:
        pass

    # Fallback if LLM fails
    if not eligibility.eligible_schemes:
        return (
            "I could not find a matching scheme right now. "
            "Please share your age, annual income, location, and category. "
            "Then I can check the right options for you."
        )

    top = eligibility.eligible_schemes[0]
    reasons = " ".join(top.reasons[:2])
    steps = " ".join(f"Step {i + 1}, {s}." for i, s in enumerate(top.next_steps[:3]))

    alternatives = ""
    if len(eligibility.eligible_schemes) > 1:
        alt_names = ", ".join(s.name for s in eligibility.eligible_schemes[1:3])
        if alt_names:
            alternatives = f" Other suitable options are, {alt_names}."

    return (
        f"You are likely eligible for {top.name}. "
        f"Reason. {reasons} "
        f"Next steps. {steps}"
        f"{alternatives}"
    )
