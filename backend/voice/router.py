import asyncio
import base64
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
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


from fastapi.responses import StreamingResponse

@router.post("/process_stream")
async def voice_process_stream(
    request: Request,
    audio: UploadFile = File(...),
    messages: str | None = Form(None),
    session_id: str = Form("default"),
    override_text: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from chat.rag import chat_reply_stream
    import re
    whisper_model = _require_whisper()
    raw = await audio.read()
    suf = _suffix_from_filename(audio.filename or "")
    meta = transcribe_with_meta(whisper_model, raw, suf)
    
    user_text = override_text.strip() if override_text and override_text.strip() else str(meta["text"]).strip()
    
    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    db_user_msg = ChatMessage(user_id=user.id, session_id=session_id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    db_msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user.id, ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc()).all()
    history = [{"role": m.role, "content": m.content} for m in db_msgs]

    async def event_generator():
        yield f"data: {json.dumps({'type': 'transcript', 'text': user_text})}\n\n"
        
        lower_text = user_text.lower()
        if "what can you do" in lower_text or "what do you do" in lower_text or "who are you" in lower_text:
            text_intro = "I am an AI assistant designed to help you discover and apply for government welfare schemes. I can check your eligibility based on your profile, explain scheme details, and guide you through the application process."
            try:
                audio_bytes = await asyncio.to_thread(synthesize_wav, text_intro)
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            except Exception:
                audio_b64 = ""
            yield f"data: {json.dumps({'type': 'audio', 'text': text_intro, 'audio_base64': audio_b64})}\n\n"
            
            with SessionLocal() as local_db:
                db_asst_msg = ChatMessage(user_id=user.id, session_id=session_id, role="assistant", content=text_intro)
                local_db.add(db_asst_msg)
                local_db.commit()
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
            
        sentence_buffer = ""
        full_reply = ""
        
        for chunk in chat_reply_stream(history):
            if await request.is_disconnected():
                return
            full_reply += chunk
            sentence_buffer += chunk
            
            # Simple sentence boundary detection
            match = re.search(r'([.?!])\s', sentence_buffer)
            if match:
                split_idx = match.end()
                sentence = sentence_buffer[:split_idx].strip()
                sentence_buffer = sentence_buffer[split_idx:]
                
                if sentence:
                    if await request.is_disconnected():
                        return
                    try:
                        audio_bytes = await asyncio.to_thread(synthesize_wav, sentence)
                        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                    except Exception as e:
                        log.error("TTS failed: %s", e)
                        audio_b64 = ""
                    
                    yield f"data: {json.dumps({'type': 'audio', 'text': sentence, 'audio_base64': audio_b64})}\n\n"
                
        if sentence_buffer.strip():
            if await request.is_disconnected():
                return
            sentence = sentence_buffer.strip()
            try:
                audio_bytes = await asyncio.to_thread(synthesize_wav, sentence)
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            except Exception:
                audio_b64 = ""
            yield f"data: {json.dumps({'type': 'audio', 'text': sentence, 'audio_base64': audio_b64})}\n\n"
            
        with SessionLocal() as local_db:
            db_asst_msg = ChatMessage(user_id=user.id, session_id=session_id, role="assistant", content=full_reply)
            local_db.add(db_asst_msg)
            local_db.commit()
            
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str

@router.post("/tts")
async def voice_tts(req: TTSRequest):
    """Generate TTS for a single sentence."""
    text = req.text.strip()
    if not text:
        return {"audio_base64": "", "audio_mime": "audio/wav"}
        
    try:
        audio_bytes = await asyncio.to_thread(synthesize_wav, text)
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        return {"audio_base64": audio_b64, "audio_mime": "audio/wav"}
    except Exception as exc:
        log.error("TTS synthesis failed for chunk: %s", exc, exc_info=True)
        return {"audio_base64": "", "audio_mime": "audio/wav"}
