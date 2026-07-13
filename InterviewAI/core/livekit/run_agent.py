"""LiveKit voice agent — pre-generated question mode.

Speaks 5 pre-generated questions from Step 4, listens to answers via STT,
and saves the transcript.  No LLM call inside the agent — llm_node is
overridden to return the next question string directly.

Pipeline:  Deepgram STT  →  (questions list)  →  ElevenLabs TTS
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from livekit.agents import llm as lk_llm, utils as agent_utils
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, elevenlabs, google

MAX_QUESTIONS = 5

# ── Load questions from env ──────────────────────────────────────────────────

def _load_questions() -> list[str]:
    """Parse INTERVIEW_QUESTIONS env var (JSON list of strings)."""
    raw = os.environ.get("INTERVIEW_QUESTIONS", "")
    if raw:
        try:
            qs = json.loads(raw)
            if isinstance(qs, list):
                return [str(q) for q in qs[:MAX_QUESTIONS]]
        except json.JSONDecodeError:
            pass
    # Fallback questions if none provided
    return [
        "Can you walk me through your most recent project and your role in it?",
        "What programming languages and frameworks are you most comfortable with?",
        "Describe a challenging technical problem you solved recently.",
        "How do you approach learning new technologies or tools?",
        "Where do you see yourself professionally in the next two to three years?",
    ]


# ── Agent ────────────────────────────────────────────────────────────────────

class InterviewAgent(Agent):
    """Speaks pre-generated questions; no LLM needed."""

    def __init__(self, questions: list[str], **kwargs):
        super().__init__(**kwargs)
        self._questions = questions
        self._q_index = 0
        self._transcript: list[dict] = []
        self._done = False

    # -- Override llm_node: return next question string (no LLM call) --------
    def llm_node(self, chat_ctx, tools, model_settings):
        if self._q_index == 0:
            # Greeting + first question
            text = (
                "Hello! I'm your AI interviewer today. "
                "I'll be asking you five questions. Take your time to answer each one. "
                f"Let's begin. {self._questions[0]}"
            )
            self._transcript.append({"role": "agent", "text": text})
            self._q_index = 1
            print(f"[Agent] Speaking greeting + Q1")
            return text

        if self._q_index < len(self._questions):
            q = self._questions[self._q_index]
            self._q_index += 1
            text = f"Thank you. Question {self._q_index} of {len(self._questions)}: {q}"
            self._transcript.append({"role": "agent", "text": text})
            print(f"[Agent] Speaking Q{self._q_index}")
            return text

        # All questions asked — closing
        self._done = True
        text = (
            "That concludes the interview. Thank you for your time and your answers. "
            "You'll receive your evaluation shortly. Have a great day!"
        )
        self._transcript.append({"role": "agent", "text": text})
        print("[Agent] Speaking closing")
        return text

    # -- Lifecycle -----------------------------------------------------------
    async def on_enter(self):
        await asyncio.sleep(1.5)
        if self.session:
            print("[Agent] on_enter -> generate_reply (greeting)")
            self.session.generate_reply()

    async def on_user_turn_completed(self, turn_ctx, new_message):
        text = (new_message.text_content or "").strip()
        if text:
            self._transcript.append({"role": "candidate", "text": text})
            print(f"[Agent] Candidate said: {text[:80]}")
            # Send transcript to client UI
            try:
                room = self.session.room_io.room
                await room.local_participant.publish_data(
                    json.dumps({"type": "transcript", "text": text, "is_final": True}).encode(),
                )
            except Exception:
                pass


# ── Token helper ─────────────────────────────────────────────────────────────

def _generate_agent_token(room_name: str) -> str:
    api_key = os.environ.get("LIVEKIT_API_KEY", "devkey")
    api_secret = os.environ.get("LIVEKIT_API_SECRET", "secret")
    grants = VideoGrants(
        room_join=True, room=room_name,
        can_publish=True, can_subscribe=True, can_publish_data=True,
    )
    return (
        AccessToken(api_key, api_secret)
        .with_identity("ai-interviewer")
        .with_name("AI Interviewer")
        .with_grants(grants)
        .with_ttl(datetime.timedelta(hours=1))
        .to_jwt()
    )


# ── Main loop ────────────────────────────────────────────────────────────────

async def run_interview(room_name: str):
    ws_url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY", "")
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "") or os.environ.get("ELEVEN_API_KEY", "")
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    questions = _load_questions()
    print(f"[Agent] Room: {room_name} | Questions: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"  Q{i}: {q[:70]}")

    async with agent_utils.http_context.open():
        token = _generate_agent_token(room_name)
        room = rtc.Room()
        await room.connect(ws_url, token)
        print(f"[Agent] Connected to room '{room_name}'")

        # LLM instance required by pipeline (never actually called — llm_node is overridden)
        llm_placeholder = google.LLM(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=gemini_api_key,
        )

        stt = deepgram.STT(
            model="nova-3", language="en-US",
            interim_results=True, api_key=deepgram_key,
        )
        tts = elevenlabs.TTS(
            model="eleven_turbo_v2_5",
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            api_key=elevenlabs_key,
        )

        agent = InterviewAgent(
            questions=questions,
            instructions="You are a professional AI interviewer.",
            stt=stt,
            llm=llm_placeholder,
            tts=tts,
        )

        session = AgentSession()

        @session.on("conversation_item_added")
        def _on_item(ev):
            item = ev.item
            if isinstance(item, lk_llm.ChatMessage) and item.role == "assistant":
                text = item.text_content
                if text:
                    print(f"[Agent] TTS queued: {text[:80]}")
                    asyncio.ensure_future(
                        room.local_participant.publish_data(
                            json.dumps({"type": "question", "text": text}).encode()
                        )
                    )

        @session.on("agent_speech_committed")
        def _on_speech_done(ev):
            if agent._done:
                print("[Agent] Interview complete — saving transcript")
                _save_transcript(room_name, agent._transcript, questions)
                # Disconnect after a short delay so TTS finishes playing
                asyncio.ensure_future(_delayed_disconnect(room, 5.0))

        await session.start(agent=agent, room=room)
        print("[Agent] Session started — interview running")

        disconnect_event = asyncio.Event()
        room.on("disconnected", lambda *_: disconnect_event.set())
        await disconnect_event.wait()
        print("[Agent] Disconnected — shutting down")


async def _delayed_disconnect(room, delay: float):
    await asyncio.sleep(delay)
    await room.disconnect()


def _save_transcript(room_name: str, transcript: list[dict], questions: list[str]):
    out_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    out_dir.mkdir(exist_ok=True)
    data = {
        "session": room_name,
        "questions_asked": questions,
        "conversation": transcript,
    }
    fp = out_dir / f"{room_name}.json"
    fp.write_text(json.dumps(data, indent=2))
    print(f"[Agent] Transcript saved: {fp}")


if __name__ == "__main__":
    room_name = sys.argv[1] if len(sys.argv) > 1 else "interview-test"
    asyncio.run(run_interview(room_name))
