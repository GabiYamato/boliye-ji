"""Abstract base class for LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface that every LLM backend must implement."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        """Send a multi-turn conversation and return the assistant reply.

        ``messages`` follows the OpenAI format::

            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns the assistant's response text.
        """

    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging."""
