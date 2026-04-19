import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "boliye_local")
QDRANT_EMBED_DIM = int(os.getenv("QDRANT_EMBED_DIM", "768"))

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

TTS_HF_MODEL = os.getenv("TTS_HF_MODEL", "facebook/mms-tts-eng")
TTS_DEVICE = os.getenv("TTS_DEVICE", "auto")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./boliye.db")
