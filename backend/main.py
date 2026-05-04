import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
import state
from auth import models as auth_models  # noqa: F401
from auth.db import Base, engine
from auth.router import router as auth_router
from chat.router import router as chat_router
from eligibility.router import router as eligibility_router
from eligibility.tree_rag import bootstrap_tree_rag
from voice.router import router as voice_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # ── STT (Whisper) ────────────────────────────────────────────────
    try:
        stt_backend = (config.STT_BACKEND or "whisper").lower()
        if stt_backend in {"faster-whisper", "faster_whisper", "faster"}:
            from faster_whisper import WhisperModel
            state.whisper_model = WhisperModel(config.WHISPER_MODEL, device="auto", compute_type="int8")
            log.info("STT: faster-whisper (%s)", config.WHISPER_MODEL)
        else:
            import whisper
            state.whisper_model = whisper.load_model(config.WHISPER_MODEL)
            log.info("STT: openai-whisper (%s)", config.WHISPER_MODEL)
    except Exception as exc:
        log.warning("Whisper failed to load: %s", exc)
        state.whisper_model = None

    # ── Database ─────────────────────────────────────────────────────
    Base.metadata.create_all(bind=engine)

    # Lightweight migration: add 'name' column if missing (SQLite doesn't
    # support IF NOT EXISTS on ALTER TABLE, so we check first).
    from sqlalchemy import inspect as sa_inspect, text
    insp = sa_inspect(engine)
    if "users" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("users")]
        if "name" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN name TEXT DEFAULT ''"))
            log.info("Migrated: added 'name' column to users table")

    # ── Scheme data (Tree-RAG cache) ─────────────────────────────────
    try:
        bootstrap_tree_rag()
        log.info("Scheme data loaded")
    except Exception as exc:
        log.warning("Scheme data bootstrap failed: %s", exc)

    # ── Eagerly init LLM and TTS providers (optional, for fast first request)
    try:
        from providers.registry import get_llm
        llm = get_llm()
        log.info("LLM ready: %s", llm.name())
    except Exception as exc:
        log.warning("LLM provider not ready at startup: %s (will retry on first request)", exc)

    try:
        from providers.registry import get_tts
        tts = get_tts()
        log.info("TTS ready: %s", tts.name())
    except Exception as exc:
        log.warning("TTS provider not ready at startup: %s (will retry on first request)", exc)

    yield


app = FastAPI(title="Boliye", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(eligibility_router, prefix="/api")
app.include_router(voice_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True}
