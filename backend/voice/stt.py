import os
import tempfile


def transcribe_file(model, data: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        result = model.transcribe(path)
        return str(result.get("text", "")).strip()
    finally:
        os.unlink(path)
