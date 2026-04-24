from __future__ import annotations

import re


_ABBREVIATIONS = {
    "govt": "government",
    "yrs": "years",
    "docs": "documents",
    "app": "application",
    "sch": "scheme",
}


def tts_optimize(text: str) -> str:
    t = text.strip()
    if not t:
        return t

    for short, full in _ABBREVIATIONS.items():
        t = re.sub(rf"\b{short}\b", full, t, flags=re.IGNORECASE)

    t = re.sub(r"[|/\\]+", ", ", t)
    t = re.sub(r"\s+", " ", t)

    # Encourage short spoken phrases.
    t = re.sub(r"\s*;\s*", ". ", t)
    t = re.sub(r"\s*:\s*", ". ", t)

    # Break very long sentences.
    chunks = []
    for sentence in re.split(r"(?<=[.!?])\s+", t):
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        if len(words) <= 16:
            chunks.append(sentence)
            continue
        while words:
            part = words[:12]
            words = words[12:]
            piece = " ".join(part).strip()
            if piece and piece[-1] not in ".!?":
                piece += "."
            chunks.append(piece)

    out = "\n".join(chunks)
    out = out.replace(",.", ",")
    out = re.sub(r"\.\.+", ".", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
