from contextlib import asynccontextmanager

import whisper
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
import state
from auth import models as auth_models  # noqa: F401
from auth.db import Base, engine
from auth.router import router as auth_router
from chat.rag import init_qdrant_collection
from chat.router import router as chat_router
from voice.router import router as voice_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        state.whisper_model = whisper.load_model(config.WHISPER_MODEL)
    except Exception:
        state.whisper_model = None
    Base.metadata.create_all(bind=engine)
    init_qdrant_collection()
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
app.include_router(voice_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True}
