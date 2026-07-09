"""LiveKit voice agent — standalone mode (run separately from Streamlit).

Usage:
  Terminal 1:  "%TEMP%\livekit\livekit-server.exe" --dev
  Terminal 2:  python -m core.livekit.adapter

Requires livekit-server running on localhost:7880.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
from core.llm import call_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("livekit-adapter")


class InterviewAILLM:
    """LLM adapter for LiveKit that routes to InterviewAI's Gemini/Ollama."""

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


async def entrypoint(ctx):
    from livekit.agents import AutoSubscribe, AgentSession, Agent
    from livekit.agents.llm import FunctionTool
    from livekit.plugins import silero

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    session = AgentSession(
        vad=silero.VAD.load(),
        llm=InterviewAILLM(),
    )

    agent = Agent(
        instructions=(
            "You are a friendly technical interviewer. "
            "Ask one question at a time. Wait for the answer. "
            "Keep responses brief and conversational."
        ),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="Greet the candidate and introduce yourself")
    await session.wait_for_idle()


async def main():
    from livekit.agents import WorkerOptions, cli

    logger.info(f"Starting LiveKit agent — connecting to {LIVEKIT_URL}")
    await cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
