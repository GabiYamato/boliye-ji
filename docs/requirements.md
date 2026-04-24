# Requirements (Boliye MVP)

## Runtime

| Component | Purpose | Notes |
|-----------|---------|--------|
| **Python** | 3.11+ recommended | Backend |
| **Node.js** | 20+ | Frontend build |
| **Ollama** | LLM + embeddings | Local `http://127.0.0.1:11434` |
| **Qdrant** | Vector store for RAG | Local `http://localhost:6333` |
| **ffmpeg** | Whisper audio decode | Often required for non-WAV browser uploads |

## Ollama models (pull before running)

- `ollama pull <OLLAMA_LLM_MODEL>` — e.g. `llama3.2`
- `ollama pull <OLLAMA_EMBED_MODEL>` — e.g. `nomic-embed-text` (768-dim vectors)

## Python packages

Declared in `backend/requirements.txt`, including:

- FastAPI, Uvicorn, SQLAlchemy, Pydantic
- LangChain + `langchain-ollama` + `langchain-qdrant`
- `qdrant-client`
- `openai-whisper` (install with `pip install openai-whisper --no-build-isolation` if the default install fails)
- `transformers`, `torch`, `scipy` — local Hugging Face TTS (`facebook/mms-tts-eng` by default)
- optional Qwen TTS endpoint via OpenAI-compatible `/audio/speech` API (`TTS_PROVIDER=qwen`)
- Auth: `python-jose`, `passlib[bcrypt]`, `google-auth` (Google OAuth optional)

## Frontend packages

Declared in `frontend/package.json`: React 19, Vite 8, React Router, `@react-oauth/google`, Tailwind v4 (`@tailwindcss/vite`).

## Hugging Face

- First TTS run downloads `TTS_HF_MODEL` (default `facebook/mms-tts-eng`). Disk space and network required.

## Qwen TTS (optional)

- Configure `TTS_PROVIDER=qwen` plus `TTS_QWEN_BASE_URL`, `TTS_QWEN_MODEL` and optional `TTS_QWEN_API_KEY`.
- `TTS_PROVIDER=auto` will attempt Qwen first (if configured) and fallback to local HF TTS.

## Optional

- **Google OAuth**: `GOOGLE_CLIENT_ID` (backend) and `VITE_GOOGLE_CLIENT_ID` (frontend `.env`)

## Env files

- Repo root: `.env` (see `.env.example`)
- Frontend optional: `frontend/.env` for `VITE_*`
