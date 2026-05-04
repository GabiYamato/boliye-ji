"""Qwen3-TTS provider via OpenAI-compatible local server."""
from __future__ import annotations

import logging
import time
import httpx

import config
from providers.tts_provider import TTSProvider

log = logging.getLogger(__name__)

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
        self._base = base
        self._url = f"{base}/v1/audio/speech"
        self._model = config.TTS_QWEN_MODEL or "qwen3-tts"
        self._voice = config.TTS_QWEN_VOICE or "Vivian"
        self._api_key = config.TTS_QWEN_API_KEY or "not-needed"

        # Probe the server -- fail fast so the registry can fall back
        self._probe()

    def _probe(self) -> None:
        """Quick connectivity check during init."""
        try:
            with httpx.Client(timeout=3.0) as client:
                # Try common endpoints
                for ep in ["/v1/models", "/health", "/"]:
                    try:
                        r = client.get(f"{self._base}{ep}")
                        if r.status_code < 500:
                            return  # Server is reachable
                    except httpx.HTTPError:
                        continue
                # If we get here, nothing worked but no connection error
                return
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise RuntimeError(
                f"Qwen3-TTS server not reachable at {self._base} -- "
                "is it running? See docs/qwen-tts-setup.md"
            ) from exc

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

        log.info(f"====== TTS REQUEST (Voice: {self._voice}) ======")
        log.info(f"Text snippet: {text[:60]}{'...' if len(text) > 60 else ''}")
        
        start_t = time.time()
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(self._url, json=payload, headers=headers)
            resp.raise_for_status()
            audio_bytes = resp.content
            
        elapsed = time.time() - start_t
        log.info(f"====== TTS RESPONSE ({elapsed:.2f}s) ======")
        log.info(f"Generated {len(audio_bytes)} bytes of audio data")
        log.info("==========================================")
        
        return audio_bytes

    # ------------------------------------------------------------------
    def name(self) -> str:
        return f"Qwen3-TTS ({self._model})"
