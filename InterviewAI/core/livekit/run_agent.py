"""LiveKit voice agent — adaptive AI interviewer.

Conducts a truly adaptive voice interview:
- Greets candidate, waits for readiness confirmation
- Uses Gemini LLM natively via LiveKit plugin for streaming responses
- Ends based on topic coverage / time budget
- Publishes real-time data to client
- Saves full session transcript on completion
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


def _build_system_prompt(cv_data: dict, jd_data: dict, seed_questions: list[str]) -> str:
    position = jd_data.get("job_title", "the role")
    company = jd_data.get("company", "our company")
    cv_skills = ", ".join(cv_data.get("skills", [])[:12])
    jd_skills = ", ".join(jd_data.get("required_skills", [])[:12])
    cv_name = cv_data.get("name", "the candidate")
    experience = cv_data.get("experience", [])
    exp_summary = ""
    if experience:
        latest = experience[0] if isinstance(experience[0], dict) else {}
        exp_summary = f"Most recent role: {latest.get('title', 'N/A')} at {latest.get('company', 'N/A')}"

    seed_text = ""
    if seed_questions:
        seed_text = "\n\nQUESTION BANK (use as starting points — rephrase naturally, adapt based on conversation):\n"
        seed_text += "\n".join(f"- {q}" for q in seed_questions[:10])

    return f"""You are a senior interviewer at {company}, conducting a real-time voice interview for: {position}.

You are warm, professional, and conversational — like a real human interviewer, not a quiz machine. Speak naturally. Use transitions like "That's interesting...", "Great, let me ask you about...", "Building on what you said...".

ABOUT THE CANDIDATE:
- Name: {cv_name}
- Key skills: {cv_skills}
- {exp_summary}

ROLE REQUIREMENTS:
- Must-have skills: {jd_skills}

YOUR APPROACH:
- Open with a warm greeting. Use the candidate's name. Mention the role. Briefly explain you'll cover technical and behavioral questions. Ask if they're ready.
- Ask ONE question at a time. Listen to their full answer before responding.
- Be genuinely adaptive:
  * Strong answer → acknowledge it ("That's a solid approach"), then probe deeper or move to a harder topic
  * Weak/vague answer → encourage ("Could you walk me through a specific example?") or simplify
  * Great insight → show interest ("That's a really interesting perspective. Tell me more about...")
- Vary your question style: scenario-based ("Imagine you're building..."), experience-based ("Tell me about a time when..."), knowledge checks ("How would you approach..."), opinion ("What's your take on...").
- Keep responses to 1-3 sentences. Don't lecture.

STAYING ON TRACK:
- If the candidate goes off-topic, gently redirect: "That's interesting, but let's focus back on [topic]. Can you tell me about..."
- If they go off-topic again, be direct: "I appreciate your thoughts, but we need to stay focused on the interview questions. Let's move on."
- If it happens a third time: "I need to flag this — staying on topic is part of the evaluation. Let's continue with the next question."

ENDING:
- If the candidate asks to end the interview, confirm: "Sure, are you certain? We've covered [X] questions so far."
- When you've covered enough topics, wrap up naturally: "I think we've covered great ground today. Thank you for your time, {cv_name}. We'll have your evaluation report ready shortly. Best of luck!"
- After closing, if they keep talking, simply say: "The interview has concluded. Thanks again!"
{seed_text}"""


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

class InterviewerAgent(Agent):
    """Agent that speaks first when entering the room."""

    async def on_enter(self):
        """Trigger the greeting immediately when agent enters the session."""
        await asyncio.sleep(1.0)
        if self.session:
            self.session.generate_reply()

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
    print(f"[Agent] API keys: gemini={'yes' if gemini_api_key else 'NO'}, deepgram={'yes' if deepgram_key else 'NO'}, elevenlabs={'yes' if elevenlabs_key else 'NO'}")

    system_prompt = _build_system_prompt(cv_data, jd_data, seed_questions)

    async with agent_utils.http_context.open():
        token = _generate_agent_token(room_name)
        room = rtc.Room()
        await room.connect(ws_url, token)
        print(f"[Agent] Connected to room '{room_name}'")

        llm_instance = google.LLM(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=gemini_api_key,
            temperature=0.4,
        )

        stt = deepgram.STT(
            model="nova-3",
            language="en-US",
            interim_results=True,
            api_key=deepgram_key,
            endpointing_ms=500,
        )
        tts = elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            api_key=elevenlabs_key,
            streaming_latency=4,
        )

        agent = InterviewerAgent(
            instructions=system_prompt,
            stt=stt,
            llm=llm_instance,
            tts=tts,
            allow_interruptions=False,
            min_endpointing_delay=1.2,
            max_endpointing_delay=5.0,
        )

        session = AgentSession(
            allow_interruptions=False,
            min_endpointing_delay=1.2,
            max_endpointing_delay=5.0,
        )

        # Track questions for client
        q_count = 0
        transcript = []
        distraction_events = []
        emotion_timeline = []
        start_time = time.time()

        @session.on("conversation_item_added")
        def _on_item(ev):
            nonlocal q_count
            item = ev.item
            if isinstance(item, lk_llm.ChatMessage):
                text = item.text_content
                if not text:
                    return
                if item.role == "assistant":
                    q_count += 1
                    transcript.append({"role": "agent", "text": text})
                    print(f"[Agent] Q{q_count}: {text[:80]}")
                    asyncio.ensure_future(
                        room.local_participant.publish_data(
                            json.dumps({
                                "type": "agent_speech",
                                "text": text,
                                "phase": "interviewing" if q_count > 1 else "greeting",
                                "q_count": q_count,
                                "elapsed_mins": round((time.time() - start_time) / 60, 1),
                            }).encode()
                        )
                    )
                elif item.role == "user":
                    transcript.append({"role": "candidate", "text": text})
                    print(f"[Agent] Candidate: {text[:80]}")
                    asyncio.ensure_future(
                        room.local_participant.publish_data(
                            json.dumps({
                                "type": "transcript",
                                "text": text,
                                "is_final": True,
                                "q_count": q_count,
                            }).encode()
                        )
                    )

        # Handle data from client (distraction/emotion events)
        @room.on("data_received")
        def _on_data(data_packet):
            try:
                payload = json.loads(data_packet.data.decode())
                msg_type = payload.get("type", "")
                if msg_type == "distraction":
                    payload["timestamp"] = time.time()
                    payload["question_number"] = q_count
                    distraction_events.append(payload)
                    print(f"[Agent] Distraction: {payload.get('detail', 'unknown')} at Q{q_count}")
                elif msg_type == "emotion":
                    payload["timestamp"] = time.time()
                    emotion_timeline.append(payload)
            except Exception:
                pass

        await session.start(agent=agent, room=room)
        print("[Agent] Session started - waiting for candidate")

        disconnect_event = asyncio.Event()
        room.on("disconnected", lambda *_: disconnect_event.set())
        await disconnect_event.wait()

        # Save transcript
        _save_transcript(room_name, transcript, distraction_events, emotion_timeline,
                        q_count, start_time, cv_data, jd_data)
        print("[Agent] Disconnected")


def _save_transcript(room_name, transcript, distraction_events, emotion_timeline,
                     q_count, start_time, cv_data, jd_data):
    out_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    out_dir.mkdir(exist_ok=True)
    data = {
        "session": room_name,
        "completed": True,
        "questions_count": q_count,
        "elapsed_mins": round((time.time() - start_time) / 60, 1),
        "conversation": transcript,
        "distraction_events": distraction_events,
        "emotion_timeline": emotion_timeline,
        "config": {
            "max_questions": MAX_QUESTIONS,
            "min_questions": MIN_QUESTIONS,
            "time_budget_mins": TIME_BUDGET_MINS,
        },
        "cv_data_summary": {
            "name": cv_data.get("name", ""),
            "skills": cv_data.get("skills", [])[:10],
        },
        "jd_data_summary": {
            "job_title": jd_data.get("job_title", ""),
            "required_skills": jd_data.get("required_skills", [])[:10],
        },
    }
    fp = out_dir / f"{room_name}.json"
    fp.write_text(json.dumps(data, indent=2))
    print(f"[Agent] Transcript saved: {fp}")


if __name__ == "__main__":
    room_name = sys.argv[1] if len(sys.argv) > 1 else "interview-test"
    asyncio.run(run_interview(room_name))
