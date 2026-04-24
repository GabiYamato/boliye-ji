# Tree-RAG Eligibility Pipeline

This module implements a voice-first eligibility system with local inference.

## Flow

1. Speech or text input arrives.
2. STT returns transcript + confidence.
3. Query structuring removes fillers and normalizes number phrases (for example, `three lakh`).
4. Profile inference extracts age, income, location, category hints.
5. Tree-RAG retrieves candidate schemes from hierarchical dataset (`backend/data/schemes_tree.json`).
6. Eligibility engine applies hard filters and computes hybrid scores.
7. Ollama generates spoken-friendly response.
8. TTS optimizer rewrites output for natural speech pauses.

## API surfaces

- `POST /api/eligibility/query`
- `POST /api/voice/transcribe`
- `POST /api/voice/process`
- `POST /api/chat/message` (now uses same eligibility pipeline)

## Notes

- Local vector retrieval uses Chroma when installed and available.
- If vector store is unavailable, retrieval falls back to lexical hashed similarity.
- Ollama failures fall back to deterministic spoken templates.
