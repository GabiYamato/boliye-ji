# Boliye

Voice-enabled AI assistant MVP: React (Vite) UI, FastAPI backend, local **Ollama** LLM + embeddings, **Qdrant** RAG, **Whisper** STT, Hugging Face **VITS** TTS, optional **Google OAuth**.

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
- `POST /api/voice/process` (multipart audio + optional message history)
- `GET /api/health`

## License

Add a license if you open-source the project.
