import io

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


def synthesize_wav(text: str) -> bytes:
    _load()
    t = text.strip()
    if not t:
        raise ValueError("empty text")
    assert _model is not None and _tokenizer is not None and _device is not None
    inputs = _tokenizer(t, return_tensors="pt")
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
