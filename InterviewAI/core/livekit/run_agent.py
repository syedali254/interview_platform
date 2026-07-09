"""LiveKit voice agent for the interview.

Runs as a worker alongside the LiveKit server.
Connects to a room, processes speech with Deepgram → Gemini → ElevenLabs.

Requires env vars:
  LIVEKIT_API_KEY, LIVEKIT_API_SECRET (from livekit-server config)
  DEEPGRAM_API_KEY (free at deepgram.com)
  ELEVENLABS_API_KEY (free at elevenlabs.io)
  GEMINI_API_KEY (already in .env)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from livekit.agents import WorkerOptions, AutoSubscribe, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, elevenlabs, openai, silero

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


async def entrypoint(ctx: JobContext):
    """Called by LiveKit worker when a new room/job is created."""
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    llm = openai.LLM(
        model=gemini_model,
        base_url=GEMINI_BASE_URL,
        api_key=gemini_api_key,
    )

    stt = deepgram.STT(
        model="nova-3",
        language="en-US",
        interim_results=True,
    )

    tts = elevenlabs.TTS(
        model="eleven_turbo_v2_5",
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George (British, natural)
    )

    agent = Agent(
        instructions=(
            "You are an interview assistant. Ask the candidate one question at a time. "
            "Wait for their answer before asking the next question. "
            "Keep responses concise. Start with a greeting."
        ),
        stt=stt,
        llm=llm,
        tts=tts,
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    # Auto-disconnect when done
    await ctx.wait_for_participant()
    await asyncio.sleep(300)  # max session 5 minutes
    await ctx.shutdown()


async def main():
    from livekit.agents.worker import run_worker

    ws_url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    api_key = os.environ.get("LIVEKIT_API_KEY", "devkey")
    api_secret = os.environ.get("LIVEKIT_API_SECRET", "secret")

    await run_worker(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=ws_url,
            api_key=api_key,
            api_secret=api_secret,
        )
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
