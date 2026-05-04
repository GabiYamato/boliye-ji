"""HuggingFace VITS TTS provider — kept as a fallback."""
from __future__ import annotations

import io

import numpy as np
import torch
from scipy.io import wavfile

import config
from providers.tts_provider import TTSProvider


class HuggingFaceTTSProvider(TTSProvider):
    """Local HuggingFace VITS model (lightweight CPU fallback)."""

    def __init__(self) -> None:
        from transformers import AutoTokenizer, VitsModel

        device = self._pick_device()
        self._tokenizer = AutoTokenizer.from_pretrained(config.TTS_HF_MODEL)
        self._model = VitsModel.from_pretrained(config.TTS_HF_MODEL)
        self._model.to(device)
        self._model.eval()
        self._device = device

    @staticmethod
    def _pick_device() -> torch.device:
        d = (config.TTS_DEVICE or "auto").lower()
        if d == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(d)

    # ------------------------------------------------------------------
    def synthesize(self, text: str) -> bytes:
        text = text.strip()
        if not text:
            raise ValueError("Cannot synthesize empty text")

        inputs = self._tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            out = self._model(**inputs)

        w = out.waveform
        arr = w.detach().cpu().numpy() if hasattr(w, "detach") else np.asarray(w)
        arr = np.asarray(arr).squeeze().astype(np.float32).flatten()
        sr = int(getattr(self._model.config, "sampling_rate", 16000))
        arr = np.clip(arr, -1.0, 1.0)
        pcm = (arr * 32767.0).astype(np.int16)

        buf = io.BytesIO()
        wavfile.write(buf, sr, pcm)
        return buf.getvalue()

    # ------------------------------------------------------------------
    def name(self) -> str:
        return f"HuggingFace VITS ({config.TTS_HF_MODEL})"
