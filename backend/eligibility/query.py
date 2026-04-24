from __future__ import annotations

import re

from eligibility.models import StructuredQuery

_FILLERS = {
    "um",
    "uh",
    "like",
    "you know",
    "actually",
    "basically",
    "i mean",
    "kind of",
    "sort of",
}

_WORD_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def _strip_fillers(text: str) -> str:
    out = text
    for token in sorted(_FILLERS, key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(token)}\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _expand_indian_number_phrases(text: str) -> str:
    out = text

    # Example: "three lakh" -> "300000"
    for word, value in _WORD_NUMBERS.items():
        out = re.sub(
            rf"\b{word}\s+lakh\b",
            str(value * 100000),
            out,
            flags=re.IGNORECASE,
        )

    # Example: "3 lakh" -> "300000"
    out = re.sub(
        r"\b(\d+)\s*lakh\b",
        lambda m: str(int(m.group(1)) * 100000),
        out,
        flags=re.IGNORECASE,
    )

    return out


def _normalize_casing_and_punctuation(text: str) -> str:
    t = text.strip()
    if not t:
        return t
    t = re.sub(r"\s+", " ", t)
    t = t[0].upper() + t[1:]
    if t[-1] not in ".!?":
        t += "."
    return t


def structure_query(raw_text: str, confidence: float = 0.0) -> StructuredQuery:
    no_fillers = _strip_fillers(raw_text)
    normalized_numbers = _expand_indian_number_phrases(no_fillers)
    cleaned = _normalize_casing_and_punctuation(normalized_numbers)
    return StructuredQuery(
        raw_transcript=raw_text,
        cleaned_query=cleaned,
        confidence=max(0.0, min(confidence, 1.0)),
    )
