"""
Hindi Voice Agent Service for Government Scheme Information
BentoML service that handles Twilio integration and WebSocket connections
"""

import bentoml
import json
import os
import typing as t

from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

LANGUAGE_CODE = "hi"  # Hindi language code

app = FastAPI()

# Add CORS middleware for web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@bentoml.service(
    traffic={"timeout": 30},
    resources={
        "gpu": 1,
        "gpu_type": "nvidia-tesla-t4",
    },
)
@bentoml.mount_asgi_app(app, path="/voice")
class HindiSchemeBot:
    """Hindi Voice Agent for Government Schemes and Scholarships"""

    def __init__(self):
        import torch
        from faster_whisper import WhisperModel
        
        print("🚀 Initializing Hindi Voice Agent...")
        
        self.batch_size = 16
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if torch.cuda.is_available() else "int8"
        
        # Load Whisper model for Hindi transcription
        print(f"📡 Loading Whisper model on {self.device}...")
        self.whisper_model = WhisperModel(
            "large-v3", 
            self.device, 
            compute_type=compute_type
        )
        
        print("✅ Hindi Voice Agent initialized successfully!")

    @app.get("/")
    async def home(self):
        """Health check endpoint"""
        return {
            "service": "Hindi Voice Agent for Government Schemes",
            "status": "active",
            "language": "Hindi",
            "endpoints": {
                "/voice/start_call": "Twilio webhook to start calls",
                "/voice/ws": "WebSocket for voice streaming"
            }
        }

    @app.post("/start_call")
    async def start_call(self):
        """
        Twilio webhook endpoint that returns TwiML to start WebSocket connection
        """
        service_url = os.environ.get("BENTOCLOUD_DEPLOYMENT_URL") or os.environ.get("SERVICE_URL") or "localhost:3000"
        
        # Remove http/https prefix if present
        if service_url.startswith("http"):
            from urllib.parse import urlparse
            service_url = urlparse(service_url).netloc
        
        # TwiML response to connect call to WebSocket
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{service_url}/voice/ws"></Stream>
    </Connect>
    <Pause length="40"/>
</Response>
"""
        return HTMLResponse(content=twiml_response, media_type="application/xml")

    @app.websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket):
        """
        WebSocket endpoint for real-time voice streaming
        Receives audio from Twilio, processes it, and sends back responses
        """
        from hindi_bot_logic import run_hindi_bot
        
        await websocket.accept()
        print("🔌 WebSocket connection established")
        
        # Get initial connection data from Twilio
        start_data = websocket.iter_text()
        await start_data.__anext__()
        call_data = json.loads(await start_data.__anext__())
        stream_sid = call_data["start"]["streamSid"]
        
        print(f"📞 Call started with Stream SID: {stream_sid}")
        
        # Run the bot logic
        await run_hindi_bot(websocket, stream_sid, whisper_model=self.whisper_model)
        
        print("📞 Call ended")


if __name__ == "__main__":
    # For local testing without BentoML
    import uvicorn
    print("⚠️  Running in standalone mode (without BentoML)")
    print("🌐 Service will be available at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
