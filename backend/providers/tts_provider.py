"""Abstract base class for TTS providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Interface that every TTS backend must implement."""

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Convert text to speech and return WAV audio bytes."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging."""
