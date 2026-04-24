import asyncio
import base64
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth.db import SessionLocal
from auth.deps import get_current_user
from auth.models import User, ChatMessage
from eligibility.profile_extract import infer_profile_from_query
from eligibility.service import run_eligibility_pipeline
from voice.stt import transcribe_with_meta
from voice.tts import synthesize_wav

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


def _load_history(messages: str | None) -> list[dict]:
    if not messages:
        return []
    try:
        hist = json.loads(messages)
        if not isinstance(hist, list):
            raise ValueError
        return hist
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid messages JSON") from exc


def _require_whisper():
    import state

    if state.whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper not loaded")
    return state.whisper_model


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
    pipeline = run_eligibility_pipeline(
        raw_text=text,
        profile=infer_profile_from_query(text),
        confidence=float(meta.get("confidence") or 0.0),
    )

    return {
        "transcript": pipeline.raw_transcript,
        "raw_transcript": pipeline.raw_transcript,
        "cleaned_query": pipeline.cleaned_query,
        "confidence": pipeline.confidence,
    }


@router.post("/process")
async def voice_process(
    audio: UploadFile = File(...),
    messages: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    whisper_model = _require_whisper()

    raw = await audio.read()
    suf = _suffix_from_filename(audio.filename or "")
    meta = transcribe_with_meta(whisper_model, raw, suf)
    user_text = str(meta["text"])
    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    _load_history(messages)

    # Store user message
    db_user_msg = ChatMessage(user_id=user.id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    profile = infer_profile_from_query(user_text)
    pipeline = run_eligibility_pipeline(
        raw_text=user_text,
        profile=profile,
        confidence=float(meta["confidence"]),
    )
    reply_text = pipeline.tts_text

    # Store assistant message
    db_asst_msg = ChatMessage(user_id=user.id, role="assistant", content=reply_text)
    db.add(db_asst_msg)
    db.commit()

    try:
        audio_bytes = await asyncio.to_thread(synthesize_wav, reply_text)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="TTS service unavailable") from exc

    return {
        "transcript": user_text,
        "reply": pipeline.response_text,
        "tts_text": pipeline.tts_text,
        "confidence": pipeline.confidence,
        "cleaned_query": pipeline.cleaned_query,
        "eligibility": pipeline.eligibility.model_dump(),
        "retrieved_context": pipeline.retrieved_context,
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "audio_mime": "audio/wav",
    }
