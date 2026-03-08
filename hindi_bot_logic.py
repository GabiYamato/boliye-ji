"""
Hindi Voice Bot Logic with Function Calling
Handles conversation flow, LLM integration, and function calling for scheme queries
"""

import os
import sys
import json
import aiohttp

from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai import OpenAILLMService, OpenAILLMContext
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.serializers.twilio import TwilioFrameSerializer

from openai.types.chat import ChatCompletionToolParam

from loguru import logger

# Import custom services from parent directory
import sys
sys.path.append("../BentoVoiceAgent")
from whisper_bento import BentoWhisperSTTService
from simple_xtts import SimpleXTTSService

# Import scheme functions
from scheme_functions import check_eligibility, collect_user_info, get_scheme_details

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


# ============================================================================
# MAIN BOT FUNCTION
# ============================================================================

async def run_hindi_bot(websocket_client, stream_sid, whisper_model):
    """
    Main bot function that sets up the pipeline and handles the conversation
    """
    
    # Setup WebSocket transport for Twilio
    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=TwilioFrameSerializer(stream_sid),
        ),
    )

    # Setup LLM - Using a small model that fits on 8GB GPU
    openai_base_url = os.getenv("OPENAI_SERVICE_URL", "http://localhost:8000/v1")
    llm = OpenAILLMService(
        base_url=openai_base_url,
        api_key=os.getenv("OPENAI_API_KEY", "n/a"),
        model=os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
    )

    # Setup Speech-to-Text (Whisper)
    stt = BentoWhisperSTTService(model=whisper_model)

    # Setup Text-to-Speech (XTTS for Hindi)
    xtts_base_url = os.getenv("XTTS_SERVICE_URL", "http://localhost:8001")
    client = aiohttp.ClientSession()
    tts = SimpleXTTSService(
        base_url=xtts_base_url,
        language="hi",  # Hindi language
        aiohttp_session=client,
    )

    # Define system message in Hindi context
    messages = [
        {
            "role": "system",
            "content": """आप एक सहायक हिंदी बोलने वाली वॉइस असिस्टेंट हैं। आपका नाम प्रिया है और आप सरकारी योजनाओं और छात्रवृत्ति के बारे में जानकारी देती हैं। 

आपका काम है:
1. छात्रों को सरकारी योजनाओं के बारे में बताना
2. उनकी पात्रता जांचना
3. आवेदन प्रक्रिया में मदद करना
4. योजनाओं की विस्तृत जानकारी देना

आप हमेशा विनम्र, स्पष्ट और संक्षिप्त हिंदी में बात करें। विशेष characters का उपयोग न करें क्योंकि आपका output audio में बदला जाएगा। 

पहली बार में कहें: नमस्कार, मैं प्रिया हूं। मैं आपको सरकारी योजनाओं और छात्रवृत्ति के बारे में जानकारी देने में मदद कर सकती हूं। आप मुझसे क्या जानना चाहते हैं?""",
        },
    ]

    # Define function calling tools
    tools = [
        ChatCompletionToolParam(
            type="function",
            function={
                "name": "check_eligibility",
                "description": "किसी छात्र की सरकारी योजनाओं के लिए पात्रता जांचें। यह फ़ंक्शन बताता है कि छात्र किन योजनाओं के लिए योग्य है।",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["सामान्य", "ओबीसी", "अनुसूचित जाति", "अनुसूचित जनजाति", "अन्य"],
                            "description": "छात्र की सामाजिक श्रेणी",
                        },
                        "annual_income": {
                            "type": "integer",
                            "description": "परिवार की वार्षिक आय रुपयों में",
                        },
                        "education_level": {
                            "type": "string",
                            "enum": ["प्राथमिक", "माध्यमिक", "उच्च माध्यमिक", "स्नातक", "स्नातकोत्तर"],
                            "description": "छात्र की शिक्षा का स्तर",
                        },
                    },
                    "required": ["category", "annual_income", "education_level"],
                },
            },
        ),
        ChatCompletionToolParam(
            type="function",
            function={
                "name": "collect_user_info",
                "description": "छात्र की व्यक्तिगत जानकारी एकत्र करें जैसे नाम, उम्र, राज्य और शिक्षा।",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "छात्र का पूरा नाम",
                        },
                        "age": {
                            "type": "integer",
                            "description": "छात्र की उम्र वर्षों में",
                        },
                        "state": {
                            "type": "string",
                            "description": "छात्र किस राज्य से है",
                        },
                        "education_level": {
                            "type": "string",
                            "description": "वर्तमान शिक्षा स्तर",
                        },
                    },
                    "required": ["name", "age", "state", "education_level"],
                },
            },
        ),
        ChatCompletionToolParam(
            type="function",
            function={
                "name": "get_scheme_details",
                "description": "किसी विशेष सरकारी योजना की विस्तृत जानकारी प्राप्त करें जैसे पात्रता, दस्तावेज़, राशि आदि।",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scheme_name": {
                            "type": "string",
                            "description": "योजना का नाम",
                        },
                        "detail_type": {
                            "type": "string",
                            "enum": ["general", "eligibility", "documents", "amount"],
                            "description": "किस प्रकार की जानकारी चाहिए - सामान्य, पात्रता, दस्तावेज़, या राशि",
                        },
                    },
                    "required": ["scheme_name"],
                },
            },
        ),
    ]

    # Register function callbacks
    llm.register_function("check_eligibility", check_eligibility)
    llm.register_function("collect_user_info", collect_user_info)
    llm.register_function("get_scheme_details", get_scheme_details)

    # Create LLM context with tools
    context = OpenAILLMContext(messages, tools)
    context_aggregator = llm.create_context_aggregator(context)
    
    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),              # Audio input from Twilio
            stt,                            # Speech-to-Text (Whisper)
            context_aggregator.user(),      # User message aggregator
            llm,                            # LLM with function calling
            tts,                            # Text-to-Speech (XTTS Hindi)
            transport.output(),             # Audio output to Twilio
            context_aggregator.assistant(), # Assistant message aggregator
        ]
    )

    # Create pipeline task
    task = PipelineTask(
        pipeline, 
        params=PipelineParams(allow_interruptions=True)
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """Handle client connection - start the conversation"""
        logger.info("👤 Client connected, starting conversation...")
        messages.append({
            "role": "system", 
            "content": "कृपया खुद को हिंदी में परिचय दें और उपयोगकर्ता का स्वागत करें।"
        })
        await task.queue_frames([LLMMessagesFrame(messages)])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """Handle client disconnection"""
        logger.info("👋 Client disconnected, ending conversation...")
        await task.queue_frames([EndFrame()])

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    
    # Cleanup
    await client.close()
    logger.info("✅ Bot session completed")
