# Setting up Qwen3-TTS Locally

Qwen3-TTS is a high-quality text-to-speech model from Alibaba. Boliye uses it via an
**OpenAI-compatible API server** that you run locally.

---

## Prerequisites

| Requirement | Details |
|------------|---------|
| **GPU** | NVIDIA GPU with **6 GB+ VRAM** (for 0.6B model) or **10 GB+** (for 1.7B model) |
| **CUDA** | CUDA 12.x with compatible NVIDIA drivers |
| **Python** | 3.10 or 3.11 recommended (3.12+ may have torch issues) |
| **Docker** | Optional but easiest approach |

> **No GPU?** You can skip Qwen3-TTS entirely. Boliye will fall back to HuggingFace VITS
> (lower quality but runs on CPU). Just set `TTS_PROVIDER=hf` in your `.env`.

---

## Option A: Docker (Recommended)

The fastest way to get running. Uses a community-built OpenAI-compatible wrapper.

### 1. Pull and run

```bash
# Clone the OpenAI-compatible server
git clone https://github.com/groxaxo/Qwen3-TTS-Openai-Fastapi.git
cd Qwen3-TTS-Openai-Fastapi

# Build the Docker image
docker build -t qwen3-tts-api .

# Run on port 8880 (must match TTS_QWEN_BASE_URL in your .env)
docker run --gpus all -p 8880:8880 qwen3-tts-api
```

### 2. Verify it works

```bash
curl http://localhost:8880/v1/models
```

You should see a JSON response listing the available model(s).

### 3. Test synthesis

```bash
curl http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-tts", "input": "Hello, this is a test.", "voice": "Vivian"}' \
  --output test.wav

# Play it
start test.wav
```

---

## Option B: Manual Python Setup

If you don't want Docker, you can run the server directly.

### 1. Create a separate venv

```bash
# Don't install this in Boliye's venv -- it has its own heavy deps
mkdir qwen3-tts-server && cd qwen3-tts-server
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install dependencies

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate fastapi uvicorn soundfile
pip install flash-attn --no-build-isolation   # optional, for faster inference
```

### 3. Download the model

```python
# Run this once to download -- it's ~1.2 GB for the 0.6B model
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen3-TTS-0.6B"  # or "Qwen/Qwen3-TTS-1.7B" for better quality
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
print("Download complete!")
```

### 4. Use the community FastAPI wrapper

```bash
git clone https://github.com/groxaxo/Qwen3-TTS-Openai-Fastapi.git
cd Qwen3-TTS-Openai-Fastapi

# Edit config.yaml to point to your model path or use the HuggingFace name
# Then run:
python main.py --port 8880
```

The server will start on `http://localhost:8880`.

---

## Option C: vLLM (Advanced, Best Performance)

For production-grade serving with automatic batching and optimizations:

```bash
pip install vllm

# Serve the model with OpenAI-compatible API
vllm serve Qwen/Qwen3-TTS-0.6B \
  --port 8880 \
  --dtype float16 \
  --max-model-len 4096
```

---

## Configuring Boliye

Once your TTS server is running, update `.env` in the Boliye project root:

```env
TTS_PROVIDER=qwen
TTS_QWEN_BASE_URL=http://localhost:8880
TTS_QWEN_MODEL=qwen3-tts
TTS_QWEN_VOICE=Vivian
```

### Available Voices

Depending on your server wrapper, common voice names include:

| Voice | Description |
|-------|-------------|
| `Vivian` | Clear female voice (default) |
| `Cherry` | Warm female voice |
| `Ethan` | Male voice |
| `Serena` | Soft female voice |

Check your specific server's docs for the full list of supported voices.

---

## Verifying Integration

After starting both Boliye backend and the TTS server:

```bash
python run_local.py --check-only
```

You should see:

```
[4/4] Services
  [OK] Qwen3-TTS reachable at http://localhost:8880
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **CUDA out of memory** | Use the 0.6B model instead of 1.7B, or add `--dtype float16` |
| **Server starts but audio sounds wrong** | Check the `response_format` is set to `wav` (Boliye expects WAV) |
| **Connection refused** | Make sure the server port matches `TTS_QWEN_BASE_URL` in `.env` |
| **Slow first request** | Normal -- the model needs to warm up. Subsequent requests are fast |
| **Want to skip TTS entirely** | Set `TTS_PROVIDER=hf` in `.env` for the lightweight CPU fallback |

---

## Model Sizes

| Model | VRAM Required | Quality | Speed |
|-------|--------------|---------|-------|
| `Qwen/Qwen3-TTS-0.6B` | ~3 GB | Good | Fast |
| `Qwen/Qwen3-TTS-1.7B` | ~7 GB | Better | Moderate |

For development, the **0.6B model** is recommended -- it's fast and sounds great.
