import asyncio
import base64
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from auth.deps import get_current_user
from auth.models import User
from chat.rag import chat_reply
from voice.stt import transcribe_file
from voice.tts import synthesize_wav

router = APIRouter(prefix="/voice", tags=["voice"])


def _suffix_from_filename(name: str) -> str:
    p = Path(name or "")
    return p.suffix if p.suffix else ".webm"


@router.post("/process")
async def voice_process(
    audio: UploadFile = File(...),
    messages: str | None = Form(None),
    user: User = Depends(get_current_user),
):
    import state

    if state.whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper not loaded")

    raw = await audio.read()
    suf = _suffix_from_filename(audio.filename or "")
    user_text = transcribe_file(state.whisper_model, raw, suf)
    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    hist: list[dict] = []
    if messages:
        try:
            hist = json.loads(messages)
            if not isinstance(hist, list):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid messages JSON")
    hist.append({"role": "user", "content": user_text})
    reply_text = chat_reply(hist)
    audio_bytes = await asyncio.to_thread(synthesize_wav, reply_text)

    return {
        "transcript": user_text,
        "reply": reply_text,
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "audio_mime": "audio/wav",
    }
