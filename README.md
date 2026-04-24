# Boliye

Voice-enabled AI assistant MVP: React (Vite) UI, FastAPI backend, local **Ollama** LLM + embeddings, **Qdrant** RAG, **Whisper** STT, Hugging Face **VITS** TTS, optional **Google OAuth**.

Now includes a voice-first **Tree-RAG eligibility engine** with local vector retrieval and spoken-response optimization.

## Quick links

- [Setup](SETUP.md) — run backend and frontend locally  
- [Requirements](docs/requirements.md) — tools, models, and dependencies  

## Repo layout

```
backend/   FastAPI — auth, chat, voice
frontend/  React + Vite — chat UI, voice capture
docs/      project documentation
```

## API (local)

- `POST /api/auth/register` · `POST /api/auth/login` · `POST /api/auth/google`
- `POST /api/chat/message`
- `POST /api/eligibility/query`
- `POST /api/voice/process` (multipart audio + optional message history)
- `POST /api/voice/transcribe` (streaming chunk transcript + cleaned query metadata)
- `GET /api/health`

## Voice-first eligibility pipeline

Primary path (real-time chunked voice input):

1. `POST /api/voice/transcribe` receives audio chunks and returns `raw_transcript`, `cleaned_query`, and `confidence`.
2. `POST /api/voice/process` runs full eligibility flow:
	- STT transcript extraction
	- Query cleaning and profile inference
	- Tree-RAG top-down retrieval
	- Rule + semantic eligibility scoring
	- Local Ollama spoken response generation
	- TTS-ready text formatting and WAV synthesis

`POST /api/eligibility/query` supports text-first invocation using the same Tree-RAG + Ollama pipeline.

## License

Add a license if you open-source the project.
