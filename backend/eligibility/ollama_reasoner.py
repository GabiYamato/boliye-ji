from __future__ import annotations

import json

import config
from langchain_ollama import ChatOllama

from eligibility.models import EligibilityResult, UserProfile

_llm: ChatOllama | None = None


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


def _get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.2,
        )
    return _llm


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
        ("system", SYSTEM_PROMPT),
        ("human", json.dumps(payload, ensure_ascii=False)),
    ]

    try:
        out = _get_llm().invoke(messages)
        text = str(out.content or "").strip()
        if text:
            return text
    except Exception:
        pass

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
