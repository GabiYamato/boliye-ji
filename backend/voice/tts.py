import io

import httpx
import numpy as np
import torch
from scipy.io import wavfile

import config

_model = None
_tokenizer = None
_device: torch.device | None = None


def _pick_device() -> torch.device:
    d = (config.TTS_DEVICE or "auto").lower()
    if d == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(d)


def _load() -> None:
    global _model, _tokenizer, _device
    if _model is not None:
        return
    from transformers import AutoTokenizer, VitsModel

    devices = [_pick_device(), torch.device("cpu")]
    tried = []
    for dev in devices:
        if dev in tried:
            continue
        tried.append(dev)
        try:
            tok = AutoTokenizer.from_pretrained(config.TTS_HF_MODEL)
            mod = VitsModel.from_pretrained(config.TTS_HF_MODEL)
            mod.to(dev)
            mod.eval()
            _tokenizer = tok
            _model = mod
            _device = dev
            return
        except Exception:
            continue
    raise RuntimeError("TTS model failed to load (try TTS_DEVICE=cpu)")


def _qwen_ready() -> bool:
    return bool((config.TTS_QWEN_BASE_URL or "").strip())


def _qwen_url() -> str:
    return config.TTS_QWEN_BASE_URL.rstrip("/") + "/audio/speech"


def _synthesize_qwen(text: str) -> bytes:
    headers = {"Content-Type": "application/json"}
    if config.TTS_QWEN_API_KEY:
        headers["Authorization"] = f"Bearer {config.TTS_QWEN_API_KEY}"

    payload = {
        "model": config.TTS_QWEN_MODEL,
        "input": text,
        "voice": config.TTS_QWEN_VOICE,
        "response_format": "wav",
    }

    with httpx.Client(timeout=90.0) as client:
        resp = client.post(_qwen_url(), json=payload, headers=headers)
        resp.raise_for_status()
        return resp.content


def _synthesize_hf(text: str) -> bytes:
    _load()
    assert _model is not None and _tokenizer is not None and _device is not None
    inputs = _tokenizer(text, return_tensors="pt")
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.no_grad():
        out = _model(**inputs)
    w = out.waveform
    arr = w.detach().cpu().numpy() if hasattr(w, "detach") else np.asarray(w)
    arr = np.asarray(arr).squeeze().astype(np.float32).flatten()
    sr = int(getattr(_model.config, "sampling_rate", 16000))
    arr = np.clip(arr, -1.0, 1.0)
    pcm = (arr * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    wavfile.write(buf, sr, pcm)
    return buf.getvalue()


def synthesize_wav(text: str) -> bytes:
    t = text.strip()
    if not t:
        raise ValueError("empty text")

    provider = (config.TTS_PROVIDER or "auto").lower().strip()
    if provider == "qwen":
        if not _qwen_ready():
            raise RuntimeError("Qwen TTS provider selected but TTS_QWEN_BASE_URL is not configured")
        return _synthesize_qwen(t)
    if provider in ("hf", "vits"):
        return _synthesize_hf(t)

    if _qwen_ready():
        try:
            return _synthesize_qwen(t)
        except Exception:
            pass
    return _synthesize_hf(t)
