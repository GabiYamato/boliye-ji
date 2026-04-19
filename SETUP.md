# Local setup

## 1. Prerequisites

Install: Python 3.11+, Node 20+, [Ollama](https://ollama.com), [Qdrant](https://qdrant.tech) (local), ffmpeg (recommended).

See [docs/requirements.md](docs/requirements.md) for the full list.

## 2. Ollama

```bash
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

Adjust names to match `.env` (`OLLAMA_LLM_MODEL`, `OLLAMA_EMBED_MODEL`).

## 3. Qdrant

Run Qdrant on port `6333` (default). If it is down, the API still starts; RAG runs with empty context.

If you change embedding model dimensions, use a new `QDRANT_COLLECTION` or delete the old collection.

## 4. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install openai-whisper --no-build-isolation
```

Copy `.env.example` to `.env` in the **repository root** and fill values.

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Whisper downloads a model on first run; SSL or network issues may require pre-downloading weights.

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens Vite on `http://localhost:5173` with `/api` proxied to `http://127.0.0.1:8000`.

Optional `frontend/.env`:

- `VITE_GOOGLE_CLIENT_ID` — Google sign-in button
- `VITE_API_URL` — leave empty for dev proxy; set for production builds

## 6. First login

Register via email/password on `/login`, or configure Google OAuth and use the Google button.
