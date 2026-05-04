"""Ollama LLM provider — kept as a fallback for local-only setups."""
from __future__ import annotations

import logging
import time
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

import config
from providers.llm_provider import LLMProvider

log = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Local Ollama LLM backend."""

    def __init__(self) -> None:
        self._llm = ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.3,
        )

    # ------------------------------------------------------------------
    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        lc_msgs = []
        for m in messages:
            role = m.get("role", "user")
            content = str(m.get("content", ""))
            if role == "system":
                lc_msgs.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            else:
                lc_msgs.append(HumanMessage(content=content))

        log.info(f"====== OLLAMA REQUEST ({config.OLLAMA_LLM_MODEL}) ======")
        log.info(f"Messages count: {len(lc_msgs)}")
        if messages:
            log.info(f"Latest input: {messages[-1].get('content', '')}")
            
        start_t = time.time()
        out = self._llm.invoke(lc_msgs)
        elapsed = time.time() - start_t
        
        reply = str(out.content or "").strip()
        
        log.info(f"====== OLLAMA RESPONSE ({elapsed:.2f}s) ======")
        log.info(reply)
        log.info("========================================")
        
        return reply

    # ------------------------------------------------------------------
    def name(self) -> str:
        return f"Ollama ({config.OLLAMA_LLM_MODEL})"
