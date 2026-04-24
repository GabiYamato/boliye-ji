import os
import tempfile


def _confidence_from_segments(segments) -> float:
    vals: list[float] = []
    for seg in segments or []:
        if isinstance(seg, dict):
            if "confidence" in seg:
                try:
                    vals.append(float(seg["confidence"]))
                    continue
                except Exception:
                    pass
            if "avg_logprob" in seg:
                try:
                    # Convert rough logprob into 0..1 heuristic.
                    score = max(0.0, min(1.0, 1.0 + float(seg["avg_logprob"]) / 5.0))
                    vals.append(score)
                    continue
                except Exception:
                    pass
    if not vals:
        return 0.85
    return max(0.0, min(1.0, sum(vals) / len(vals)))


def _run_transcribe(model, path: str) -> tuple[str, float]:
    out = model.transcribe(path)

    # openai-whisper style dict
    if isinstance(out, dict):
        text = str(out.get("text", "")).strip()
        confidence = _confidence_from_segments(out.get("segments"))
        return text, confidence

    # faster-whisper style: (segments_generator, info)
    if isinstance(out, tuple) and len(out) == 2:
        segments_iter, info = out
        segments = list(segments_iter)
        text = " ".join((getattr(s, "text", "") or "").strip() for s in segments).strip()
        confidence = 0.88
        lang_prob = getattr(info, "language_probability", None)
        if isinstance(lang_prob, (int, float)):
            confidence = max(0.0, min(1.0, float(lang_prob)))
        return text, confidence

    # Fallback
    return "", 0.0


def transcribe_file(model, data: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        text, _ = _run_transcribe(model, path)
        return text
    finally:
        os.unlink(path)


def transcribe_with_meta(model, data: bytes, suffix: str) -> dict:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        text, confidence = _run_transcribe(model, path)
        return {
            "text": text,
            "confidence": confidence,
        }
    finally:
        os.unlink(path)
