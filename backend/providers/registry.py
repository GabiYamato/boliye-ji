"""Provider registry — lazy-initialized singletons for LLM and TTS."""
from __future__ import annotations

import logging

import config
from providers.llm_provider import LLMProvider
from providers.tts_provider import TTSProvider

log = logging.getLogger(__name__)

_llm: LLMProvider | None = None
_tts: TTSProvider | None = None


# ── LLM ──────────────────────────────────────────────────────────────
def get_llm() -> LLMProvider:
    """Return the configured LLM provider (singleton)."""
    global _llm
    if _llm is not None:
        return _llm

    backend = (config.LLM_PROVIDER or "auto").lower().strip()

    if backend in ("gemini", "auto"):
        if config.GEMINI_API_KEY:
            try:
                from providers.llm_gemini import GeminiProvider
                _llm = GeminiProvider()
                log.info("LLM provider: %s", _llm.name())
                return _llm
            except Exception as exc:
                log.warning("Gemini init failed: %s", exc)
                if backend == "gemini":
                    raise

    if backend in ("ollama", "auto"):
        try:
            from providers.llm_ollama import OllamaProvider
            _llm = OllamaProvider()
            log.info("LLM provider: %s", _llm.name())
            return _llm
        except Exception as exc:
            log.warning("Ollama init failed: %s", exc)
            if backend == "ollama":
                raise

    raise RuntimeError(
        f"No LLM provider available (LLM_PROVIDER={config.LLM_PROVIDER}). "
        "Set GEMINI_API_KEY for Gemini or ensure Ollama is running."
    )


# ── TTS ──────────────────────────────────────────────────────────────
def get_tts() -> TTSProvider:
    """Return the configured TTS provider (singleton)."""
    global _tts
    if _tts is not None:
        return _tts

    backend = (config.TTS_PROVIDER or "auto").lower().strip()

    if backend in ("qwen", "auto"):
        if config.TTS_QWEN_BASE_URL:
            try:
                from providers.tts_qwen import QwenTTSProvider
                _tts = QwenTTSProvider()
                log.info("TTS provider: %s", _tts.name())
                return _tts
            except Exception as exc:
                log.warning("Qwen TTS init failed: %s", exc)
                if backend == "qwen":
                    raise

    if backend in ("hf", "vits", "auto"):
        try:
            from providers.tts_hf import HuggingFaceTTSProvider
            _tts = HuggingFaceTTSProvider()
            log.info("TTS provider: %s", _tts.name())
            return _tts
        except Exception as exc:
            log.warning("HuggingFace TTS init failed: %s", exc)
            if backend in ("hf", "vits"):
                raise

    raise RuntimeError(
        f"No TTS provider available (TTS_PROVIDER={config.TTS_PROVIDER}). "
        "Set TTS_QWEN_BASE_URL for Qwen3-TTS or install transformers for HF."
    )
