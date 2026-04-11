# Setup Guide - Hindi Voice Agent

Complete setup instructions for running the Hindi Voice Agent.

## Prerequisites

### Hardware
- NVIDIA GPU with 8GB VRAM (e.g., RTX 4060)
- CUDA 11.8+ installed

### Software
- Python 3.11
- ffmpeg system package
- Git

## Installation Steps

### 1. Install System Dependencies

**Windows (with Chocolatey):**
```powershell
choco install ffmpeg
```

**Or download from:** https://ffmpeg.org/download.html

### 2. Install Python Packages

```bash
pip install -r requirements.txt
```

This installs:
- bentoml - Service framework
- fastapi - Web framework
- faster-whisper - Speech-to-text
- pipecat-ai - Voice pipeline
- torch - ML framework
- aiohttp, loguru, resampy - Supporting libraries

### 3. Set Up External Services

You need two external services running:

#### A. LLM Service (Llama 3.1 8B)

**Option 1: Using Ollama (Easiest)**
```powershell
# Download from https://ollama.ai/
ollama pull llama3.1:8b
ollama serve
```

**Option 2: Using BentoVLLM**
```bash
git clone https://github.com/bentoml/BentoVLLM
cd BentoVLLM/llama3.1-8b-instruct
bentoml serve
```

#### B. XTTS Service (Text-to-Speech)

```bash
git clone https://github.com/bentoml/BentoXTTSStreaming
cd BentoXTTSStreaming
pip install -r requirements.txt
bentoml serve
```

### 4. Configure Environment Variables

```powershell
# Set service URLs
$env:XTTS_SERVICE_URL = "http://localhost:8001"
$env:OPENAI_SERVICE_URL = "http://localhost:8000/v1"
$env:OPENAI_API_KEY = "n/a"
$env:LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
```

For Ollama, use:
```powershell
$env:OPENAI_SERVICE_URL = "http://localhost:11434/v1"
```

### 5. Test Functions (Optional but Recommended)

```bash
python test_functions.py
```

This tests all 3 function calling capabilities and shows Hindi responses without needing external services.

### 6. Run the Service

```bash
bentoml serve hindi_voice_service:HindiSchemeBot
```

Service will start at: http://localhost:3000

Endpoints:
- Health check: http://localhost:3000/
- Twilio webhook: http://localhost:3000/voice/start_call
- WebSocket: ws://localhost:3000/voice/ws

## Twilio Configuration

### 1. Get a Twilio Account
- Sign up at https://www.twilio.com/
- Get a phone number with voice capabilities

### 2. Configure Webhook

Go to: Twilio Console → Phone Numbers → Active Numbers → [Your Number]

Set voice configuration:
- When a call comes in: **Webhook**
- URL: `https://your-deployment.bentoml.ai/voice/start_call`
- HTTP Method: **POST**

### 3. Test the Call

Call your Twilio number and speak in Hindi!

## Deployment to BentoCloud

### 1. Login to BentoCloud

```bash
bentoml login
```

Sign up at: https://www.bentoml.com/

### 2. Deploy

```bash
bentoml deploy . \
  --env XTTS_SERVICE_URL=https://your-xtts.bentoml.ai \
  --env OPENAI_SERVICE_URL=https://your-llm.bentoml.ai/v1
```

### 3. Update Twilio Webhook

Update the webhook URL to your BentoCloud deployment URL.

## GPU Memory Optimization

If you encounter GPU memory issues on 8GB:

### Reduce Whisper Model Size

Edit `hindi_voice_service.py`:
```python
# Change from "large-v3" to:
self.whisper_model = WhisperModel("medium", self.device, compute_type=compute_type)
# or
self.whisper_model = WhisperModel("small", self.device, compute_type=compute_type)
```

### Use Smaller LLM

Alternative models for 8GB GPU:
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (1.1B parameters)
- `microsoft/phi-2` (2.7B parameters)
- `mistralai/Mistral-7B-Instruct-v0.2` (7B parameters)

Update in environment:
```powershell
$env:LLM_MODEL = "microsoft/phi-2"
```

## Testing Without Phone

### 1. Test Functions Only
```bash
python test_functions.py
```

Shows all Hindi responses from the 3 functions.

### 2. Test WebSocket (Advanced)

Create a WebSocket client to simulate Twilio connection:
```python
import asyncio
import websockets

async def test():
    uri = "ws://localhost:3000/voice/ws"
    async with websockets.connect(uri) as websocket:
        # Send test audio frames
        pass

asyncio.run(test())
```

## Sample Conversation Flow

1. **Bot**: "नमस्कार, मैं प्रिया हूं। मैं आपको सरकारी योजनाओं के बारे में बता सकती हूं।"

2. **User**: "मैं बारहवीं में पढ़ता हूं और एससी कैटेगरी से हूं"

3. **Bot** calls `check_eligibility()`:
   "आपकी पात्रता के अनुसार, आप प्री-मैट्रिक और एससीएसटी छात्रवृत्ति योजना के लिए आवेदन कर सकते हैं।"

4. **User**: "पोस्ट मैट्रिक स्कॉलरशिप के बारे में बताइए"

5. **Bot** calls `get_scheme_details()`:
   "पोस्ट-मैट्रिक स्कॉलरशिप योजना दसवीं के बाद की पढ़ाई के लिए है..."

## Adding More Schemes

Edit `hindi_bot_logic.py` and add to `scheme_database`:

```python
scheme_database = {
    "योजना का नाम": {
        "general": "सामान्य जानकारी हिंदी में",
        "eligibility": "पात्रता की शर्तें",
        "documents": "आवश्यक दस्तावेज़",
        "amount": "छात्रवृत्ति की राशि"
    },
    # Add more schemes...
}
```

## Troubleshooting

### GPU Out of Memory
- Use smaller Whisper model (`medium` or `small`)
- Use smaller LLM (phi-2, TinyLlama)
- Close other GPU applications

### Import Errors
```bash
pip install -r requirements.txt
```

### XTTS Service Not Responding
- Verify XTTS service is running: http://localhost:8001
- Check `XTTS_SERVICE_URL` environment variable
- Ensure Hindi language is supported in XTTS config

### LLM Not Calling Functions
- Verify LLM service supports function calling
- Check that `tools` parameter is passed to LLM context
- Test with `test_functions.py` first

### Poor Audio Quality
- Test with clear audio input
- Verify XTTS Hindi voice model is loaded
- Check network connection for WebSocket

### Hindi Text Issues
- Avoid special characters in function responses
- Use simple, clear Hindi words
- Test responses with `test_functions.py`

## Configuration Files

### bentofile.yaml
Defines the BentoML service configuration:
- Python version (3.11)
- System packages (ffmpeg)
- Environment variables
- GPU requirements

### requirements.txt
Lists all Python dependencies (without versions for flexibility)

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `XTTS_SERVICE_URL` | XTTS TTS service endpoint | `http://localhost:8001` |
| `OPENAI_SERVICE_URL` | LLM service endpoint | `http://localhost:8000/v1` |
| `OPENAI_API_KEY` | API key (unused for local) | `n/a` |
| `LLM_MODEL` | Model name | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| `BENTOCLOUD_DEPLOYMENT_URL` | Deployment URL for webhooks | - |

## Performance Tips

1. **Use smaller models for faster response**: phi-2 or TinyLlama
2. **Reduce Whisper model size**: `small` or `medium` for faster STT
3. **Enable GPU**: Ensure CUDA is properly configured
4. **Cache frequently used responses**: Add response caching layer

## Security Notes

- Don't store sensitive user data
- Use secure environment variable management
- Implement rate limiting in production
- Add authentication for admin endpoints
- Use HTTPS in production

## Support & Resources

- **BentoML**: https://docs.bentoml.com
- **Pipecat**: https://docs.pipecat.ai
- **XTTS**: https://github.com/bentoml/BentoXTTSStreaming
- **BentoVLLM**: https://github.com/bentoml/BentoVLLM
- **Twilio**: https://www.twilio.com/docs/voice

## Next Steps

1. Test functions with `python test_functions.py`
2. Set up external LLM and XTTS services
3. Run the full voice agent
4. Configure Twilio webhook
5. Test with phone calls
6. Deploy to production

For more examples and updates, see the project repository.