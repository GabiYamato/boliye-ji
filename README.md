# Boliye

Voice-first AI assistant that helps Indian citizens discover government welfare schemes they're eligible for.

**Architecture**: Modular provider system — plug in any LLM (Gemini, Ollama) or TTS (Qwen3-TTS, HuggingFace VITS) backend.

## Stack

| Layer | Default | Alternative |
|-------|---------|-------------|
| **LLM** | Google Gemini (cloud) | Ollama (local) |
| **TTS** | Qwen3-TTS (local server) | HuggingFace VITS (CPU) |
| **STT** | OpenAI Whisper (local) | faster-whisper |
| **Frontend** | React + Vite + TailwindCSS | — |
| **Backend** | FastAPI + SQLite | — |

## Quick Start

1. **Clone & install**
   ```bash
   cd backend
   pip install -r requirements.txt

   cd ../frontend
   npm install
   ```

2. **Configure** — Copy `.env.example` to `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your-key-here
   ```

3. **Start Qwen3-TTS** (optional, for high-quality voice):
   ```bash
   # See https://github.com/QwenLM/Qwen3-TTS
   # Run the OpenAI-compatible TTS server on port 8880
   ```

4. **Run**
   ```bash
   # Terminal 1: Backend
   cd backend
   uvicorn main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

5. Open http://localhost:5173

## API

- `POST /api/auth/register` · `POST /api/auth/login` · `POST /api/auth/google`
- `POST /api/chat/message` — text chat with full conversation memory
- `GET /api/chat/history` · `DELETE /api/chat/history`
- `POST /api/voice/process` — voice chat (STT → LLM → TTS)
- `POST /api/voice/transcribe` — transcription only
- `POST /api/eligibility/query` — direct eligibility check
- `GET /api/health`

## Provider System

All LLM and TTS calls go through abstract providers in `backend/providers/`:

```
providers/
├── llm_provider.py    # ABC
├── llm_gemini.py      # Google Gemini
├── llm_ollama.py      # Ollama (local)
├── tts_provider.py    # ABC
├── tts_qwen.py        # Qwen3-TTS (OpenAI-compatible)
├── tts_hf.py          # HuggingFace VITS
└── registry.py        # Factory with auto-fallback
```

To add a new provider: implement the ABC, add a case in `registry.py`.

## License

Add a license if you open-source the project.
