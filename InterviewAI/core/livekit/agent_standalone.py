"""Standalone LiveKit voice agent — run with: python core/livekit/agent_standalone.py

Requires:
  1. livekit-server running (downloaded to temp, or installed globally)
  2. pip install livekit-agents livekit-plugins-silero edge-tts faster-whisper

Architecture:
  livekit-server.exe (signaling) ─── browser/device (WebRTC)
                                      │
                                   agent_standalone.py (VoicePipelineAgent)
                                      │
                          ┌───────────┼───────────┐
                          │           │           │
                       Silero VAD  faster-whisper  edge-tts
                                      │
                                   Gemini/Ollama
                                      │
                               InterviewLoop (core)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ── Add project root to path ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_ROOM_NAME,
    OLLAMA_MODEL,
    OLLAMA_ENDPOINT,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_ENDPOINT,
    LLM_PROVIDER,
)
from core.llm import call_llm
from core.pipeline.interview_loop import InterviewLoop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("livekit-agent")


# ── Custom LiveKit-compatible LLM ─────────────────────────────────────────
class InterviewLLM:
    """LLM adapter that uses InterviewAI's LLM (Gemini or Ollama)."""

    def __init__(self, interview_loop: InterviewLoop = None):
        self.interview_loop = interview_loop

    async def chat(self, messages: list, temperature: float = 0.3) -> str:
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        return call_llm(prompt, temperature=temperature)

    async def generate_reply(self, messages: list) -> str:
        return await self.chat(messages)


# ── Custom STT: faster-whisper ──────────────────────────────────────────
class FasterWhisperSTT:
    """Local STT using faster-whisper (free, no API key)."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading faster-whisper ({self.model_size})...")
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            logger.info("Whisper model loaded.")

    async def transcribe(self, audio_data: bytes) -> str:
        self._load_model()
        import io
        import soundfile as sf
        import numpy as np

        audio_arr, sample_rate = sf.read(io.BytesIO(audio_data))
        segments, info = self._model.transcribe(audio_arr, beam_size=5)
        text = " ".join(seg.text for seg in segments)
        return text.strip()


# ── Custom TTS: edge-tts ─────────────────────────────────────────────────
class EdgeTTS:
    """Local TTS using edge-tts (free, no API key)."""

    async def synthesize(self, text: str) -> bytes:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice="en-GB-SoniaNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data


# ── LiveKit Voice Agent ──────────────────────────────────────────────────
class LiveKitVoiceAgent:
    """Full-duplex voice agent for live interviews via LiveKit."""

    def __init__(self, topics: list, cv_data: dict, jd_data: dict):
        self.interview_loop = InterviewLoop(topics, cv_data, jd_data)
        self.llm = InterviewLLM(self.interview_loop)
        self.stt = FasterWhisperSTT()
        self.tts = EdgeTTS()
        self._server_process = None
        self._agent = None

    def start_server(self):
        """Start the LiveKit server as a subprocess."""
        server_path = Path(temp_dir) / "livekit-server.exe" if "temp_dir" in dir() else None
        if not server_path or not server_path.exists():
            server_path = Path(tempfile.gettempdir()) / "livekit" / "livekit-server.exe"
            if not server_path.exists():
                logger.error("livekit-server.exe not found. Download it from GitHub releases.")
                logger.error("Or run: scoop install livekit")
                return False

        logger.info(f"Starting LiveKit server from: {server_path}")
        self._server_process = subprocess.Popen(
            [str(server_path), "--dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)
        logger.info("LiveKit server started (dev mode).")
        return True

    def stop_server(self):
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None
            logger.info("LiveKit server stopped.")

    async def run(self, room_name: str = LIVEKIT_ROOM_NAME):
        """Connect the voice pipeline agent to a LiveKit room."""
        try:
            from livekit.agents import AutoSubscribe, WorkerOptions, cli
            from livekit.agents.voice import VoicePipelineAgent
            from livekit.plugins import silero
        except ImportError:
            logger.error("LiveKit dependencies missing. Run: pip install livekit-agents livekit-plugins-silero")
            return

        vad = silero.VAD()

        async def entrypoint(ctx):
            logger.info(f"Connecting to room {ctx.room.name}")
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
            participant = await ctx.wait_for_participant()
            logger.info(f"Participant joined: {participant.identity}")

            agent = VoicePipelineAgent(
                vad=vad,
                stt=self.stt,
                llm=self.llm,
                tts=self.tts,
            )

            self._agent = agent
            agent.start(ctx.room, participant)

            # Interview loop — ask next question after each answer
            while not self.interview_loop.is_complete:
                q_data = self.interview_loop.get_next_question()
                if not q_data:
                    break

                question_text = q_data["question"]
                logger.info(f"Q{q_data['question_number']}: {question_text[:60]}...")

                # Speak the question
                audio = await self.tts.synthesize(question_text)
                # Play audio through LiveKit
                # (simplified — real impl uses agent.say())

                # Wait for voice answer (LiveKit handles this internally)
                # The answer is transcribed by STT and processed by the LLM
                # We intercept the user's response via the LLM callback

                # For now, log the state
                logger.info(f"State: {self.interview_loop.state.summary()['verified_strong']} strong, "
                           f"{self.interview_loop.state.summary()['confirmed_gaps']} gaps")

            logger.info("Interview complete!")
            await agent.say("The interview is now complete. Thank you!")

        # Run the agent
        logger.info(f"Starting LiveKit agent for room: {room_name}")
        await cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
                api_url=LIVEKIT_URL,
                api_key=LIVEKIT_API_KEY,
                api_secret=LIVEKIT_API_SECRET,
            )
        )


# ── CLI Entry Point ──────────────────────────────────────────────────────
def main():
    """Start LiveKit server + voice agent."""
    agent = LiveKitVoiceAgent(
        topics=[],
        cv_data={},
        jd_data={},
    )

    try:
        if agent.start_server():
            asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        agent.stop_server()


if __name__ == "__main__":
    main()
