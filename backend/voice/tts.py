"""TTS synthesis using the pluggable provider system."""
from __future__ import annotations

from providers.registry import get_tts
from voice.formatting import tts_optimize


def synthesize_wav(text: str) -> bytes:
    """Convert text to WAV audio bytes using the configured TTS provider.

    The text is first optimized for spoken output (abbreviation expansion,
    sentence splitting, etc.) and then sent to the active TTS provider.
    """
    optimized = tts_optimize(text)
    if not optimized:
        raise ValueError("Cannot synthesize empty text")

    tts = get_tts()
    return tts.synthesize(optimized)
