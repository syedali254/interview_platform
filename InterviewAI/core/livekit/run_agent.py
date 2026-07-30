"""LiveKit voice agent — adaptive AI interviewer.

Conducts a truly adaptive voice interview:
- Greets candidate, waits for readiness confirmation
- Generates follow-up questions based on each answer using LLM
- Ends based on topic coverage / time budget (not a fixed count)
- Publishes real-time data (questions, transcripts, emotion/distraction events) to client
- Saves full session transcript with metadata on completion
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import tempfile
import time
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

# Configurable via env
MAX_QUESTIONS = int(os.environ.get("MAX_INTERVIEW_QUESTIONS", "15"))
MIN_QUESTIONS = int(os.environ.get("MIN_INTERVIEW_QUESTIONS", "5"))
TIME_BUDGET_MINS = int(os.environ.get("INTERVIEW_TIME_BUDGET_MINS", "30"))


def _load_json_env(key: str, default=None):
    raw = os.environ.get(key, "")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return default if default is not None else {}


def _load_seed_questions() -> list[str]:
    raw = os.environ.get("INTERVIEW_QUESTIONS", "")
    if raw:
        try:
            qs = json.loads(raw)
            if isinstance(qs, list):
                return [str(q) for q in qs]
        except json.JSONDecodeError:
            pass
    return []


# ── Adaptive Agent ────────────────────────────────────────────────────────

class AdaptiveInterviewAgent(Agent):
    """Fully adaptive interviewer — generates next question based on prior answers."""

    def __init__(self, seed_questions: list[str], cv_data: dict, jd_data: dict, **kwargs):
        super().__init__(**kwargs)
        self._seed_questions = seed_questions
        self._cv_data = cv_data
        self._jd_data = jd_data
        self._transcript: list[dict] = []
        self._questions_asked: list[str] = []
        self._done = False
        self._phase = "greeting"  # greeting -> readiness -> interviewing -> closing
        self._q_count = 0
        self._start_time: float = 0.0
        self._topics_covered: set = set()
        self._distraction_events: list[dict] = []
        self._emotion_timeline: list[dict] = []
        self._off_topic_count = 0

    @property
    def _elapsed_mins(self) -> float:
        if self._start_time == 0:
            return 0
        return (time.time() - self._start_time) / 60.0

    def _should_end(self) -> bool:
        if self._q_count >= MAX_QUESTIONS:
            return True
        if self._elapsed_mins >= TIME_BUDGET_MINS:
            return True
        # End if we've asked minimum questions AND covered all seed topics
        if self._q_count >= MIN_QUESTIONS and len(self._seed_questions) > 0:
            if self._q_count >= len(self._seed_questions):
                return True
        return False

    def _build_context(self) -> str:
        lines = []
        for msg in self._transcript[-20:]:  # Last 20 messages for context window
            role = "Interviewer" if msg["role"] == "agent" else "Candidate"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def llm_node(self, chat_ctx, tools, model_settings):
        if self._done:
            return ""

        position = self._jd_data.get("job_title", "the role")
        cv_skills = ", ".join(self._cv_data.get("skills", [])[:10])
        jd_skills = ", ".join(self._jd_data.get("required_skills", [])[:10])
        conversation = self._build_context()

        if self._phase == "greeting":
            prompt = f"""You are a professional AI interviewer for the position: {position}.
Required skills: {jd_skills}
Candidate skills: {cv_skills}

This is the very start of the interview. Greet the candidate warmly:
- Introduce yourself as their AI interviewer
- Mention the position they're interviewing for
- Briefly explain the format (you'll ask technical and behavioral questions, they should take their time)
- Ask if they're ready to begin

Keep it to 3-4 sentences. Be warm and professional.
Return ONLY what you say — no labels, no quotes."""
            self._phase = "readiness"

        elif self._phase == "readiness":
            # Check if candidate said yes in last message
            last_candidate = ""
            for msg in reversed(self._transcript):
                if msg["role"] == "candidate":
                    last_candidate = msg["text"].lower()
                    break
            if any(w in last_candidate for w in ["yes", "ready", "sure", "let's", "go ahead", "ok", "start", "begin", "i am", "i'm"]):
                self._phase = "interviewing"
                self._start_time = time.time()
                # Fall through to interviewing
            else:
                prompt = f"""You are a professional AI interviewer. The candidate hasn't confirmed readiness yet.

Conversation so far:
{conversation}

Politely ask again if they're ready, or address their concern briefly.
Keep it to 1-2 sentences. Return ONLY what you say."""

        if self._phase == "interviewing":
            if self._should_end():
                self._phase = "closing"
                prompt = f"""You are a professional AI interviewer wrapping up.

Conversation so far:
{conversation}

Thank the candidate sincerely for their time and answers. Tell them:
- The interview is now complete
- They'll receive a detailed evaluation report shortly
- Wish them well

Keep it to 3 sentences. Be warm. Return ONLY what you say."""
                self._done = True
            else:
                # Build adaptive next-question prompt
                seed_text = ""
                if self._seed_questions:
                    remaining = [q for q in self._seed_questions if q not in self._questions_asked]
                    if remaining:
                        seed_text = f"\nSuggested topics/questions to draw from (adapt based on answers):\n" + "\n".join(f"- {q}" for q in remaining[:5])

                last_answer = ""
                for msg in reversed(self._transcript):
                    if msg["role"] == "candidate":
                        last_answer = msg["text"]
                        break

                prompt = f"""You are a professional AI interviewer for: {position}.
Required skills: {jd_skills}
Candidate skills: {cv_skills}

Questions asked so far: {self._q_count}
Time elapsed: {self._elapsed_mins:.1f} minutes

Conversation (recent):
{conversation}
{seed_text}

RULES:
1. Ask the NEXT interview question. It must be ADAPTIVE:
   - If the candidate's last answer was strong, probe deeper or move to a harder topic
   - If the answer was weak or vague, ask a simpler follow-up or clarifying question
   - If they went off-topic, redirect firmly but politely
   - Don't repeat questions already asked
2. Mix technical and behavioral questions naturally
3. Keep your response to 1-3 sentences — just the question, maybe a brief transition
4. Be conversational, not robotic
5. If the candidate's answer was off-topic or irrelevant, note it briefly before asking next question

Return ONLY what you say — no labels, no quotes, no preamble."""
                self._q_count += 1

        try:
            response = call_llm(prompt, temperature=0.4)
            response = response.strip().strip('"').strip("'")
        except Exception as e:
            print(f"[Agent] LLM error: {e}")
            # Fallback: use a seed question
            if self._seed_questions and self._q_count <= len(self._seed_questions):
                response = self._seed_questions[self._q_count - 1]
            else:
                response = "Could you tell me more about your experience with that?"

        self._transcript.append({"role": "agent", "text": response})
        if self._phase == "interviewing" or self._phase == "closing":
            self._questions_asked.append(response)

        print(f"[Agent] [{self._phase}] Q{self._q_count}: {response[:80]}")
        return response

    async def on_enter(self):
        await asyncio.sleep(1.5)
        if self.session:
            print("[Agent] on_enter -> greeting")
            self.session.generate_reply()

    async def on_user_turn_completed(self, turn_ctx, new_message):
        text = (new_message.text_content or "").strip()
        if not text:
            return

        self._transcript.append({"role": "candidate", "text": text})
        print(f"[Agent] Candidate: {text[:80]}")

        # Publish transcript to client
        try:
            room = self.session.room_io.room
            await room.local_participant.publish_data(
                json.dumps({
                    "type": "transcript",
                    "role": "candidate",
                    "text": text,
                    "is_final": True,
                    "q_count": self._q_count,
                    "elapsed_mins": round(self._elapsed_mins, 1),
                }).encode(),
            )
        except Exception:
            pass

    def record_distraction(self, event: dict):
        """Called when client reports distraction via data channel."""
        event["timestamp"] = time.time()
        event["question_number"] = self._q_count
        self._distraction_events.append(event)
        print(f"[Agent] Distraction: {event.get('type', 'unknown')} at Q{self._q_count}")

    def record_emotion(self, event: dict):
        """Called when client reports emotion snapshot."""
        event["timestamp"] = time.time()
        event["question_number"] = self._q_count
        self._emotion_timeline.append(event)


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

    seed_questions = _load_seed_questions()
    cv_data = _load_json_env("CV_DATA")
    jd_data = _load_json_env("JD_DATA")

    position = jd_data.get("job_title", "the role")
    print(f"[Agent] Room: {room_name} | Position: {position}")
    print(f"[Agent] Config: max_q={MAX_QUESTIONS}, min_q={MIN_QUESTIONS}, time={TIME_BUDGET_MINS}min")
    print(f"[Agent] Seed questions: {len(seed_questions)}")

    async with agent_utils.http_context.open():
        token = _generate_agent_token(room_name)
        room = rtc.Room()
        await room.connect(ws_url, token)
        print(f"[Agent] Connected to room '{room_name}'")

        llm_instance = google.LLM(
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
        )

        agent = AdaptiveInterviewAgent(
            seed_questions=seed_questions,
            cv_data=cv_data,
            jd_data=jd_data,
            instructions="You are a professional AI interviewer.",
            stt=stt,
            llm=llm_instance,
            tts=tts,
        )

        session = AgentSession()

        @session.on("conversation_item_added")
        def _on_item(ev):
            item = ev.item
            if isinstance(item, lk_llm.ChatMessage) and item.role == "assistant":
                text = item.text_content
                if text:
                    print(f"[Agent] Publishing to client: {text[:60]}")
                    asyncio.ensure_future(
                        room.local_participant.publish_data(
                            json.dumps({
                                "type": "agent_speech",
                                "text": text,
                                "phase": agent._phase,
                                "q_count": agent._q_count,
                                "elapsed_mins": round(agent._elapsed_mins, 1),
                            }).encode()
                        )
                    )

        @session.on("agent_speech_committed")
        def _on_speech_done(ev):
            if agent._done:
                print("[Agent] Interview complete - saving transcript")
                _save_transcript(room_name, agent)
                asyncio.ensure_future(_delayed_disconnect(room, 6.0))

        # Handle data from client (distraction/emotion events)
        @room.on("data_received")
        def _on_data(data_packet):
            try:
                payload = json.loads(data_packet.data.decode())
                msg_type = payload.get("type", "")
                if msg_type == "distraction":
                    agent.record_distraction(payload)
                    # Echo warning back to client
                    asyncio.ensure_future(
                        room.local_participant.publish_data(
                            json.dumps({
                                "type": "warning",
                                "text": f"Attention: {payload.get('detail', 'Please focus on the interview.')}",
                                "severity": payload.get("severity", "medium"),
                            }).encode()
                        )
                    )
                elif msg_type == "emotion":
                    agent.record_emotion(payload)
            except Exception:
                pass

        await session.start(agent=agent, room=room)
        print("[Agent] Session started - waiting for candidate")

        disconnect_event = asyncio.Event()
        room.on("disconnected", lambda *_: disconnect_event.set())
        await disconnect_event.wait()

        # Save on disconnect even if not done
        if not agent._done:
            _save_transcript(room_name, agent)
        print("[Agent] Disconnected")


async def _delayed_disconnect(room, delay: float):
    await asyncio.sleep(delay)
    await room.disconnect()


def _save_transcript(room_name: str, agent: 'AdaptiveInterviewAgent'):
    out_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    out_dir.mkdir(exist_ok=True)
    data = {
        "session": room_name,
        "completed": agent._done,
        "phase": agent._phase,
        "questions_count": agent._q_count,
        "elapsed_mins": round(agent._elapsed_mins, 1),
        "conversation": agent._transcript,
        "questions_asked": agent._questions_asked,
        "distraction_events": agent._distraction_events,
        "emotion_timeline": agent._emotion_timeline,
        "config": {
            "max_questions": MAX_QUESTIONS,
            "min_questions": MIN_QUESTIONS,
            "time_budget_mins": TIME_BUDGET_MINS,
        },
        "cv_data_summary": {
            "name": agent._cv_data.get("name", ""),
            "skills": agent._cv_data.get("skills", [])[:10],
        },
        "jd_data_summary": {
            "job_title": agent._jd_data.get("job_title", ""),
            "required_skills": agent._jd_data.get("required_skills", [])[:10],
        },
    }
    fp = out_dir / f"{room_name}.json"
    fp.write_text(json.dumps(data, indent=2))
    print(f"[Agent] Transcript saved: {fp}")


if __name__ == "__main__":
    room_name = sys.argv[1] if len(sys.argv) > 1 else "interview-test"
    asyncio.run(run_interview(room_name))
