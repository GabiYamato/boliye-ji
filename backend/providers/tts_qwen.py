"""Qwen3-TTS provider via OpenAI-compatible local server."""
from __future__ import annotations

import httpx

import config
from providers.tts_provider import TTSProvider


class QwenTTSProvider(TTSProvider):
    """Calls a locally-hosted Qwen3-TTS OpenAI-compatible server.

    Expects the server to expose ``POST /v1/audio/speech`` in the standard
    OpenAI format.  See https://github.com/QwenLM/Qwen3-TTS
    """

    def __init__(self) -> None:
        base = (config.TTS_QWEN_BASE_URL or "").rstrip("/")
        if not base:
            raise RuntimeError(
                "TTS_QWEN_BASE_URL must be set when using the Qwen TTS provider"
            )
        self._url = f"{base}/v1/audio/speech"
        self._model = config.TTS_QWEN_MODEL or "qwen3-tts"
        self._voice = config.TTS_QWEN_VOICE or "Vivian"
        self._api_key = config.TTS_QWEN_API_KEY or "not-needed"

    # ------------------------------------------------------------------
    def synthesize(self, text: str) -> bytes:
        text = text.strip()
        if not text:
            raise ValueError("Cannot synthesize empty text")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload = {
            "model": self._model,
            "input": text,
            "voice": self._voice,
            "response_format": "wav",
        }

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(self._url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.content

    # ------------------------------------------------------------------
    def name(self) -> str:
        return f"Qwen3-TTS ({self._model})"
