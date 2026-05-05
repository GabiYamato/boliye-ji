"""Filler audio management for the thinking/loading phase.

Pre-generated WAV clips are served from backend/assets/fillers/ to give
the user something to listen to while the LLM is processing.
"""
from __future__ import annotations

import logging
import random
from pathlib import Path

log = logging.getLogger(__name__)

FILLERS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fillers"

# Filler metadata — text matches the generated audio
FILLER_CLIPS = [
    {"name": "hold_on", "text": "Please hold on for one moment, I'll browse through the available schemes."},
    {"name": "one_moment", "text": "One moment, I'm checking the schemes that fit you."},
    {"name": "searching", "text": "Searching through the available schemes for you."},
    {"name": "just_a_little_more", "text": "Just a little more—I'm almost done."},
    {"name": "almost_there", "text": "Almost there, finding the best match now."},
]

_cached_fillers: list[dict] | None = None


def _load_fillers() -> list[dict]:
    """Load filler clips that actually exist on disk."""
    global _cached_fillers
    if _cached_fillers is not None:
        return _cached_fillers

    available = []
    for clip in FILLER_CLIPS:
        path = FILLERS_DIR / f"{clip['name']}.wav"
        if path.exists():
            available.append({
                "name": clip["name"],
                "text": clip["text"],
                "path": path,
                "bytes": path.read_bytes(),
            })
        else:
            log.warning("Filler clip missing: %s", path)

    _cached_fillers = available
    log.info("Loaded %d filler clips from %s", len(available), FILLERS_DIR)
    return available


def get_random_filler() -> dict | None:
    """Return a random filler clip as {name, text, audio_bytes}.

    Returns None if no filler clips are available.
    """
    fillers = _load_fillers()
    if not fillers:
        return None

    clip = random.choice(fillers)
    return {
        "name": clip["name"],
        "text": clip["text"],
        "audio_bytes": clip["bytes"],
    }
