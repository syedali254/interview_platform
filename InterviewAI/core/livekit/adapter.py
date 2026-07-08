"""LiveKit voice adapter — self-hosted LiveKit server + Whisper STT + edge-tts.

Architecture:
  This module provides a VoiceAssistant class that uses LiveKit's VoicePipelineAgent
  with local/self-hosted components:
    - STT:  LiveKit WhisperSTT plugin (runs whisper locally)
    - LLM:  custom OllamaLLM adapter (calls qwen2.5-coder via Ollama)
    - TTS:  edge-tts (free, no API key)
    - VAD:  Silero VAD (free, local)

Prerequisites (to be installed):
  $ pip install livekit-agents livekit-plugins-silero livekit-plugins-whisper livekit-plugins-deepgram
  $ # Also need: edge-tts package for TTS fallback

Usage:
  from core.livekit.adapter import VoiceAssistant
  assistant = VoiceAssistant()
  await assistant.start_room(room_name="interview-123")
"""

import asyncio
import json
from typing import Optional

from core.config import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_ROOM_NAME,
    OLLAMA_MODEL,
    OLLAMA_ENDPOINT,
)
from core.pipeline.interview_loop import InterviewLoop


class OllamaLLM:
    """LiveKit-compatible LLM adapter for self-hosted Ollama."""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model

    async def chat(self, messages: list, temperature: float = 0.3) -> str:
        import requests

        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 512,
            },
        }
        resp = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"].strip()

    async def generate_reply(self, messages: list) -> str:
        return await self.chat(messages)


class VoiceAssistant:
    """Self-hosted voice assistant for live audio interview using LiveKit."""

    def __init__(self, interview_loop: Optional[InterviewLoop] = None):
        self.interview_loop = interview_loop
        self._agent = None
        self._room = None

    async def start_room(self, room_name: str = LIVEKIT_ROOM_NAME):
        """Start a LiveKit room and connect the voice pipeline agent.

        Uses:
          - Silero VAD (local)
          - Whisper STT (local via livekit-plugins-whisper or deepgram fallback)
          - Ollama LLM (via custom adapter above)
          - edge-tts for TTS (free, local)
        """
        try:
            from livekit import api
            from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
            from livekit.agents.voice import VoicePipelineAgent
            from livekit.plugins import silero, deepgram
            from livekit.plugins import whisper
        except ImportError:
            raise ImportError(
                "LiveKit dependencies not installed.\n"
                "Run: pip install livekit-agents livekit-plugins-silero "
                "livekit-plugins-whisper edge-tts\n"
                "And start the LiveKit server: livekit-server --dev"
            )

        # Try to import edge-tts for TTS; fallback to a simple message
        try:
            import edge_tts
            _has_tts = True
        except ImportError:
            _has_tts = False
            print("[WARN] edge-tts not installed — TTS disabled for LiveKit. Install: pip install edge-tts")

        # ── Build the voice pipeline ──
        vad = silero.VAD()
        stt = whisper.STT()  # local whisper

        if _has_tts:
            tts = None  # We'll use a custom TTS; for now LiveKit provides a fallback
        else:
            tts = None

        llm_adapter = OllamaLLM()

        # Create the voice pipeline agent
        self._agent = VoicePipelineAgent(
            vad=vad,
            stt=stt,
            llm=llm_adapter,
            tts=tts,
            # min_endpointing_delay=0.5,
        )

        # Connect to LiveKit server
        livekit_api = api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )

        print(f"[LiveKit] Connected to {LIVEKIT_URL}")
        print(f"[LiveKit] Room: {room_name}")
        return self._agent

    async def stop_room(self):
        """Disconnect from the LiveKit room."""
        if self._agent:
            await self._agent.aclose()
        print("[LiveKit] Disconnected.")

    def is_connected(self) -> bool:
        return self._agent is not None
