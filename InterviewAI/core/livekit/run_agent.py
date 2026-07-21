"""LiveKit voice agent — dynamic Gemini-powered interview.

Uses Gemini AI to conduct a natural conversational interview:
- Warm welcome mentioning the job position
- Asks if candidate is ready
- Asks pre-generated questions dynamically
- Handles off-topic answers with warnings
- Auto-ends and saves full transcript
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

from core.llm import call_llm

MAX_QUESTIONS = 5

# ── Load context from env ─────────────────────────────────────────────────

def _load_questions() -> list[str]:
    raw = os.environ.get("INTERVIEW_QUESTIONS", "")
    if raw:
        try:
            qs = json.loads(raw)
            if isinstance(qs, list):
                return [str(q) for q in qs[:MAX_QUESTIONS]]
        except json.JSONDecodeError:
            pass
    return [
        "Can you walk me through your most recent project and your role in it?",
        "What programming languages and frameworks are you most comfortable with?",
        "Describe a challenging technical problem you solved recently.",
        "How do you approach learning new technologies or tools?",
        "Where do you see yourself professionally in the next two to three years?",
    ]


def _load_json_env(key: str, default: dict = None) -> dict:
    raw = os.environ.get(key, "")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return default or {}


# ── Agent ─────────────────────────────────────────────────────────────────

class InterviewAgent(Agent):
    """Dynamic interview agent powered by Gemini."""

    def __init__(self, questions: list[str], cv_data: dict, jd_data: dict, **kwargs):
        super().__init__(**kwargs)
        self._questions = questions
        self._cv_data = cv_data
        self._jd_data = jd_data
        self._q_index = 0
        self._transcript: list[dict] = []
        self._done = False
        self._greeted = False
        self._ready_confirmed = False
        self._warnings_given = 0
        self._all_questions_done = False

    def _build_conversation_text(self) -> str:
        lines = []
        for msg in self._transcript:
            role = "Interviewer" if msg["role"] == "agent" else "Candidate"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def llm_node(self, chat_ctx, tools, model_settings):
        if self._done:
            return ""

        position = self._jd_data.get("job_title", "the role")
        cv_skills = ", ".join(self._cv_data.get("skills", [])[:10])
        jd_skills = ", ".join(self._jd_data.get("required_skills", [])[:10])
        questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(self._questions))
        conversation = self._build_conversation_text()

        prompt = f"""You are a professional AI interviewer. Conduct a voice interview for the position: {position}.

Job requirements: {jd_skills}
Candidate's known skills: {cv_skills}

Your behavior rules:
1. Start warmly: greet the candidate, introduce yourself, mention the position.
2. After they respond to the greeting, ask: "Are you ready to begin the interview?"
3. Only when they say yes/ready, start asking questions one by one from the list below.
4. For each question, wait for their answer. If they go off-topic:
   - 1st time: politely say "Please answer the question directly so I can evaluate your response."
   - 2nd time: say "I need you to answer the question. Otherwise I'll move to the next one."
   - 3rd time: say "Let's move to the next question." and move on.
5. Keep responses short (2-3 sentences). Be natural and friendly but stay focused.
6. Do NOT answer questions yourself. Do NOT go off-topic.
7. After all questions are done, thank them and say the interview is complete.

Questions to ask (in order):
{questions_text}

Current conversation:
{conversation}

What do you say next? Return ONLY what you say — no labels, no quotes."""

        try:
            response = call_llm(prompt, temperature=0.3)
            # Clean response
            response = response.strip().strip('"').strip("'")
        except Exception as e:
            response = "I apologize, let me continue with the interview."

        # Track state
        self._transcript.append({"role": "agent", "text": response})

        resp_lower = response.lower()

        if not self._greeted:
            if "how are you" in resp_lower or "hello" in resp_lower or "hi" in resp_lower or "welcome" in resp_lower:
                self._greeted = True
                print("[Agent] Greeting done")
            else:
                self._greeted = True  # Assume greeted after first response

        if self._greeted and not self._ready_confirmed:
            if "ready" in resp_lower or "begin" in resp_lower or "start" in resp_lower:
                pass  # Waiting for candidate to confirm readiness
            if any(p in resp_lower for p in ["let's start", "let's begin", "first question", "question 1"]):
                self._ready_confirmed = True
                print("[Agent] Ready confirmed")

        # Track question progress from response references
        if "question" in resp_lower:
            for i in range(1, len(self._questions) + 1):
                if f"question {i}" in resp_lower or f"question{i}" in resp_lower:
                    if i > self._q_index:
                        self._q_index = i
                        print(f"[Agent] Advanced to Q{i}")

        # Detect off-topic warning
        if "please answer the question" in resp_lower:
            self._warnings_given += 1
            print(f"[Agent] Warning #{self._warnings_given}")

        # Detect closing
        if any(p in resp_lower for p in ["concludes", "thank you for your time", "interview is complete", "have a great day"]):
            self._all_questions_done = True
            self._done = True
            print("[Agent] Interview complete")

        print(f"[Agent] Says: {response[:80]}")
        return response

    async def on_enter(self):
        await asyncio.sleep(1.5)
        if self.session:
            print("[Agent] on_enter -> generate_reply")
            self.session.generate_reply()

    async def on_user_turn_completed(self, turn_ctx, new_message):
        text = (new_message.text_content or "").strip()
        if text:
            self._transcript.append({"role": "candidate", "text": text})
            print(f"[Agent] Candidate: {text[:80]}")

            # If candidate confirms readiness
            resp_lower = text.lower()
            if self._greeted and not self._ready_confirmed:
                if any(p in resp_lower for p in ["yes", "ready", "let's go", "sure", "ok", "start", "begin", "i'm ready", "i am ready"]):
                    self._ready_confirmed = True
                    print("[Agent] Candidate confirmed ready")

            # Publish transcript to client
            try:
                room = self.session.room_io.room
                await room.local_participant.publish_data(
                    json.dumps({"type": "transcript", "text": text, "is_final": True}).encode(),
                )
            except Exception:
                pass


# ── Token helper ───────────────────────────────────────────────────────────

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


# ── Main loop ─────────────────────────────────────────────────────────────

async def run_interview(room_name: str):
    ws_url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY", "")
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "") or os.environ.get("ELEVEN_API_KEY", "")
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    questions = _load_questions()
    cv_data = _load_json_env("CV_DATA")
    jd_data = _load_json_env("JD_DATA")

    position = jd_data.get("job_title", "the role")
    print(f"[Agent] Room: {room_name} | Position: {position} | Questions: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"  Q{i}: {q[:70]}")

    async with agent_utils.http_context.open():
        token = _generate_agent_token(room_name)
        room = rtc.Room()
        await room.connect(ws_url, token)
        print(f"[Agent] Connected to room '{room_name}'")

        # LLM instance required by pipeline (llm_node is overridden)
        llm_placeholder = google.LLM(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=gemini_api_key,
        )

        stt = deepgram.STT(
            model="nova-3", language="en-US",
            interim_results=True, api_key=deepgram_key,
        )
        tts = elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            api_key=elevenlabs_key,
            streaming_latency=4,
        )

        agent = InterviewAgent(
            questions=questions,
            cv_data=cv_data,
            jd_data=jd_data,
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
                asyncio.ensure_future(_delayed_disconnect(room, 5.0))

        await session.start(agent=agent, room=room)
        print("[Agent] Session started")

        disconnect_event = asyncio.Event()
        room.on("disconnected", lambda *_: disconnect_event.set())
        await disconnect_event.wait()
        print("[Agent] Disconnected")


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
