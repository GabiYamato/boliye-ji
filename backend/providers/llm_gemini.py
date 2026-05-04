"""Google Gemini LLM provider."""
from __future__ import annotations

from google import genai
from google.genai import types

import config
from providers.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    """Gemini API via the official google-genai SDK."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model = config.GEMINI_MODEL

    # ------------------------------------------------------------------
    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        """Send a multi-turn conversation and return the assistant reply."""
        system_instruction = None
        contents: list[types.Content] = []

        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")

            if role == "system":
                system_instruction = text
                continue

            # Gemini uses "user" and "model" (not "assistant")
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=text)],
                )
            )

        # Ensure conversation doesn't start with 'model' role
        if contents and contents[0].role == "model":
            contents.insert(
                0,
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello")],
                ),
            )

        generate_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )
        if system_instruction:
            generate_config.system_instruction = system_instruction

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=generate_config,
        )

        return (response.text or "").strip()

    # ------------------------------------------------------------------
    def name(self) -> str:
        return f"Gemini ({self._model})"
