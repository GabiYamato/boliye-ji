"""Conversational agent powered by the pluggable LLM provider.

Instead of the old RAG pipeline that forgot context every turn, this module
sends the *full* conversation history (from the DB) to the LLM so it
naturally remembers income, age, name, and every other detail the user
already shared.

Scheme data is embedded directly in the system prompt — Gemini's context
window is large enough and this is far more reliable than the old hash-based
vector search.
"""
from __future__ import annotations

from providers.registry import get_llm
from eligibility.tree_rag import get_scheme_leaves


def _load_scheme_context() -> str:
    """Build a concise text block describing all available schemes."""
    leaves = get_scheme_leaves()
    if not leaves:
        return "(No scheme data loaded)"

    lines: list[str] = []
    for leaf in leaves:
        attrs = leaf.attributes or {}
        age_range = ""
        if attrs.get("min_age") is not None or attrs.get("max_age") is not None:
            lo = attrs.get("min_age", "any")
            hi = attrs.get("max_age", "any")
            age_range = f"  Age: {lo}–{hi}\n"

        income = ""
        if attrs.get("max_income") is not None:
            income = f"  Max annual income: ₹{attrs['max_income']:,}\n"

        categories = ", ".join(attrs.get("category") or [])
        steps = "\n".join(f"    • {s}" for s in (attrs.get("next_steps") or []))

        lines.append(
            f"### {leaf.name}\n"
            f"  {leaf.description}\n"
            f"{age_range}"
            f"{income}"
            f"  Categories: {categories}\n"
            f"  Next steps:\n{steps}"
        )

    return "\n\n".join(lines)


_SCHEME_CONTEXT: str | None = None


def _get_scheme_context() -> str:
    global _SCHEME_CONTEXT
    if _SCHEME_CONTEXT is None:
        _SCHEME_CONTEXT = _load_scheme_context()
    return _SCHEME_CONTEXT


SYSTEM_PROMPT = """\
You are **Boliye**, a voice-first assistant that helps Indian citizens discover government welfare schemes they may be eligible for.

## Your Tone
- Keep a steady, neutral, and consistent tone across all sentences.
- Avoid emotional shifts (no excited, sad, or overly casual phrasing).
- Sound clear, calm, and informative.
- Keep answers concise (2–4 sentences for voice, a bit more for text).
- NEVER repeat questions the user already answered. You have full conversation history.
- If you already know the user's age, income, location, or category from earlier in the conversation, use that — don't ask again.
- If you need more info to narrow down schemes, ask ONE specific question at a time.

## How to Help
1. When the user shares details (age, income, occupation, location, category like SC/ST/OBC/General), remember them.
2. Match their profile against the schemes below.
3. Recommend eligible schemes with a brief reason and clear next steps.
4. If multiple schemes match, mention the top 2-3 and offer to explain any in detail.
5. If no scheme matches, say so honestly and explain what would need to change.

## Important Rules
- FOCUS ON UX. Be helpful, not pedantic. If the user says "I'm 25, earning 2 lakh", immediately check schemes — don't interrogate them.
- For voice responses: keep sentences short, avoid bullet points and markdown, use natural spoken language.
- Make the output extremely TTS-friendly. NEVER use abbreviations like "e.g." or "i.e." (write "for example" or "that is"). Spell out large numbers cleanly (write "two lakh" instead of "2,00,000"). Do not use special characters or symbols.
- For text responses: you may use light formatting but keep it readable.
- Always respond in the same language the user speaks (English or Hindi).
- You CAN make reasonable assumptions (e.g., if someone says "I'm a farmer" → category is farmer, location is likely rural).

## Available Schemes Database
{schemes}
"""


def get_system_prompt() -> str:
    return SYSTEM_PROMPT.format(schemes=_get_scheme_context())


def chat_reply(messages: list[dict]) -> str:
    """Generate a reply given the full conversation history.

    ``messages`` should be a list of dicts with 'role' and 'content' keys,
    as stored in the DB. The system prompt is prepended automatically.
    """
    llm = get_llm()

    full_messages = [{"role": "system", "content": get_system_prompt()}]
    for m in messages:
        role = m.get("role", "user")
        content = str(m.get("content", ""))
        if role in ("user", "assistant") and content.strip():
            full_messages.append({"role": role, "content": content})

    try:
        return llm.chat(full_messages)
    except Exception as exc:
        # Fallback: give a useful response instead of crashing
        return (
            "I'm having trouble connecting right now. "
            "Could you try again in a moment? "
            "In the meantime, you can visit scholarships.gov.in or pmkisan.gov.in for scheme information."
        )

def chat_reply_stream(messages: list[dict]):
    """Generate a streaming reply given the full conversation history."""
    llm = get_llm()

    full_messages = [{"role": "system", "content": get_system_prompt()}]
    for m in messages:
        role = m.get("role", "user")
        content = str(m.get("content", ""))
        if role in ("user", "assistant") and content.strip():
            full_messages.append({"role": role, "content": content})

    try:
        yield from llm.chat_stream(full_messages)
    except Exception as exc:
        yield "I'm having trouble connecting right now."
