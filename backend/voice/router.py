import asyncio
import base64
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth.db import SessionLocal
from auth.deps import get_current_user
from auth.models import User, ChatMessage
from chat.rag import chat_reply
from voice.fillers import get_random_filler
from voice.stt import transcribe_with_meta
from voice.tts import synthesize_wav

log = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _suffix_from_filename(name: str) -> str:
    p = Path(name or "")
    return p.suffix if p.suffix else ".webm"


def _require_whisper():
    import state

    if state.whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper not loaded")
    return state.whisper_model


@router.get("/filler")
async def voice_filler(user: User = Depends(get_current_user)):
    """Return a random pre-generated filler audio clip.

    Played during the 'thinking' phase to keep the user engaged
    while the LLM generates a real response.
    """
    clip = get_random_filler()
    if clip is None:
        return {"text": "Please hold on a moment...", "audio_base64": "", "audio_mime": "audio/wav"}

    audio_b64 = base64.b64encode(clip["audio_bytes"]).decode("ascii")
    return {
        "text": clip["text"],
        "audio_base64": audio_b64,
        "audio_mime": "audio/wav",
    }


@router.post("/transcribe")
async def voice_transcribe_chunk(
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    whisper_model = _require_whisper()
    raw = await audio.read()
    suf = _suffix_from_filename(audio.filename or "")
    try:
        meta = transcribe_with_meta(whisper_model, raw, suf)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported audio payload") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Audio transcription failed") from exc

    text = str(meta.get("text") or "").strip()

    return {
        "transcript": text,
        "raw_transcript": text,
        "cleaned_query": text,
        "confidence": float(meta.get("confidence") or 0.0),
    }


@router.post("/process")
async def voice_process(
    audio: UploadFile = File(...),
    messages: str | None = Form(None),
    session_id: str = Form("default"),
    override_text: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Full voice pipeline: STT -> LLM (with history) -> TTS.

    The key improvement: we load full conversation history from the DB
    so the LLM remembers everything the user previously said.
    """
    whisper_model = _require_whisper()

    raw = await audio.read()
    suf = _suffix_from_filename(audio.filename or "")
    meta = transcribe_with_meta(whisper_model, raw, suf)
    
    # Use override_text if provided (user manually edited transcript), otherwise STT
    user_text = override_text.strip() if override_text and override_text.strip() else str(meta["text"]).strip()
    
    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    # Store user message
    db_user_msg = ChatMessage(user_id=user.id, session_id=session_id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    # Load FULL conversation history from DB
    db_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in db_msgs]

    # Generate reply with full conversation context
    reply_text = chat_reply(history)

    # Store assistant message
    db_asst_msg = ChatMessage(user_id=user.id, session_id=session_id, role="assistant", content=reply_text)
    db.add(db_asst_msg)
    db.commit()

    # Synthesize speech -- gracefully degrade if TTS fails
    audio_b64 = ""
    audio_mime = "audio/wav"
    try:
        audio_bytes = await asyncio.to_thread(synthesize_wav, reply_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    except Exception as exc:
        log.error("TTS synthesis failed: %s", exc, exc_info=True)
        # Don't crash the request -- return the text reply without audio

    return {
        "transcript": user_text,
        "reply": reply_text,
        "tts_text": reply_text,
        "confidence": float(meta.get("confidence", 0.0)),
        "cleaned_query": user_text,
        "audio_base64": audio_b64,
        "audio_mime": audio_mime,
    }
