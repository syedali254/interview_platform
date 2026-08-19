"""M5: LiveKit voice agent — the AI interviewer.

Conducts an adaptive voice interview:
  - Greets the candidate and waits for them to confirm they are ready
  - Streams questions through Gemini, Deepgram STT and ElevenLabs TTS
  - Publishes each question to the client *before* speaking it
  - Ends cleanly when the budget is spent or the candidate asks to stop
  - Saves the full transcript plus behavioural telemetry on completion

Speech handling note: the agent buffers each complete utterance before
synthesising it, rather than piping the LLM's token stream straight into the
TTS socket. Streaming partial tokens into ElevenLabs produced truncated
audio — the agent would speak a few words and fall silent while the full text
still appeared on screen. Buffering also gives us the ordering the interview
needs: the question is displayed first, then spoken.
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
from livekit.agents import APIConnectOptions, function_tool, RunContext
from livekit.agents import llm as lk_llm, utils as agent_utils
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, elevenlabs, google

from core.agents.interviewer_prompt import build_system_prompt

# Configurable via env
MAX_QUESTIONS = int(os.environ.get("MAX_INTERVIEW_QUESTIONS", "15"))
# The floor must never sit above the ceiling, or a short demo run configured
# with MAX_INTERVIEW_QUESTIONS=3 would never reach its own limit.
MIN_QUESTIONS = min(int(os.environ.get("MIN_INTERVIEW_QUESTIONS", "5")), MAX_QUESTIONS)
TIME_BUDGET_MINS = int(os.environ.get("INTERVIEW_TIME_BUDGET_MINS", "30"))

# How long the question stays on screen before the agent starts speaking it.
DISPLAY_LEAD_SECONDS = 0.45

# Grace period after the closing statement before the room is torn down.
CLOSING_GRACE_SECONDS = 12

# How long a prewarmed agent sits in the room waiting for the candidate.
CANDIDATE_WAIT_TIMEOUT = 600


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
    """Shared interviewer instructions, plus the voice-only tool contract."""
    base = build_system_prompt(cv_data, jd_data, seed_questions, mode="voice")
    return base + (
        "\n\nHOW TO END: when the rules above say to end the interview, call "
        "the end_interview tool. Use reason \"candidate_request\" when the "
        "candidate confirmed they want to stop, or \"completed\" when the "
        "interview has run its course. Always speak your closing sentence "
        "before calling it."
    )


async def _probe_tts(engine) -> bool:
    """Confirm a text-to-speech engine actually returns audio.

    A provider can accept the connection and then return nothing — an
    exhausted ElevenLabs quota behaves exactly like this, which is why the
    agent could appear to speak at the start of a session and fall silent
    later while the transcript kept scrolling. Two characters are cheap
    enough to spend on finding that out before the interview starts.
    """
    try:
        # No retries: a dead provider should cost a fraction of a second to
        # rule out, not the ~5s the default retry policy spends on it.
        async with engine.stream(
            conn_options=APIConnectOptions(max_retry=0, timeout=8)
        ) as stream:
            async def _feed():
                stream.push_text("Hi")
                stream.end_input()

            task = asyncio.create_task(_feed())
            try:
                async for ev in stream:
                    if ev.frame.samples_per_channel > 0:
                        return True
            finally:
                await agent_utils.aio.cancel_and_wait(task)
    except Exception as exc:
        print(f"[Agent] TTS probe error: {type(exc).__name__}: {str(exc)[:160]}")
    return False


async def _select_tts(elevenlabs_key: str, deepgram_key: str):
    """Pick the first voice provider that genuinely produces audio."""
    candidates = []

    if elevenlabs_key:
        candidates.append((
            "ElevenLabs",
            lambda: elevenlabs.TTS(
                model="eleven_turbo_v2_5",
                voice_id=os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
                api_key=elevenlabs_key,
                sync_alignment=False,
                enable_ssml_parsing=False,
            ),
        ))

    if deepgram_key:
        candidates.append((
            "Deepgram Aura",
            lambda: deepgram.TTS(
                model=os.environ.get("DEEPGRAM_TTS_MODEL", "aura-2-andromeda-en"),
                api_key=deepgram_key,
            ),
        ))

    for name, factory in candidates:
        try:
            engine = factory()
        except Exception as exc:
            print(f"[Agent] {name} could not be created: {exc}")
            continue

        if await _probe_tts(engine):
            print(f"[Agent] Voice provider: {name}")
            return engine, name

        print(f"[Agent] {name} returned no audio — falling back to the next provider")

    print("[Agent] WARNING: no working voice provider. The interview will run "
          "in text-only mode; questions will still be displayed.")
    return None, None


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


class InterviewerAgent(Agent):
    """Interviewer that displays each utterance before speaking it."""

    def __init__(self, instructions: str, hooks: "AgentHooks"):
        super().__init__(instructions=instructions)
        self._hooks = hooks

    async def on_enter(self):
        """Greet once the candidate is actually in the room.

        The agent process is started early — while the candidate is still on
        the device-setup screen — so that importing livekit-agents and its
        plugins (around 12 seconds) happens before they press Begin
        Interview. That means the agent is usually in the room first and must
        wait, rather than greeting an empty room.
        """
        waited = 0.0
        while not self._hooks.candidate_joined and waited < CANDIDATE_WAIT_TIMEOUT:
            await asyncio.sleep(0.25)
            waited += 0.25

        if not self._hooks.candidate_joined:
            print("[Agent] No candidate joined within the wait window")
            return

        await asyncio.sleep(0.6)
        if self.session:
            self.session.generate_reply()

    async def tts_node(self, text, model_settings):
        """Buffer the full utterance, publish it, then synthesise it.

        Feeding the LLM's token stream directly to ElevenLabs caused the
        socket to drop mid-utterance, so the agent spoke only the opening
        words. Synthesising one complete string fixes that and lets the UI
        render the question before the audio starts.
        """
        parts = []
        async for chunk in text:
            parts.append(chunk)
        utterance = "".join(parts).strip()

        if not utterance:
            return

        await self._hooks.publish_agent_speech(utterance)

        # No working voice provider: the question is still delivered, on
        # screen, rather than the interview failing outright.
        if not self._hooks.tts_provider:
            return

        await asyncio.sleep(DISPLAY_LEAD_SECONDS)

        async def _complete_text():
            yield utterance

        async for frame in Agent.default.tts_node(self, _complete_text(), model_settings):
            yield frame

    @function_tool
    async def end_interview(self, ctx: RunContext, reason: str = "completed") -> str:
        """End the interview session.

        Call this only after speaking a closing statement. Use reason
        "candidate_request" when the candidate confirmed they want to stop,
        or "completed" when the interview has run its course.
        """
        print(f"[Agent] end_interview tool called (reason={reason})")
        self._hooks.request_end(reason)
        return "The interview has been closed."


class AgentHooks:
    """Shared state and callbacks between the agent and the session loop."""

    def __init__(self, room: rtc.Room, start_time: float):
        self.room = room
        self.start_time = start_time
        self.transcript: list[dict] = []
        self.distraction_events: list[dict] = []
        self.emotion_timeline: list[dict] = []
        self.attention_events: list[dict] = []
        self.voice_samples: list[dict] = []
        self.turn_count = 0
        self.q_count = 0
        self.ending = False
        self.candidate_joined = False
        self.tts_provider: str | None = None
        self.end_reason: str | None = None
        self.end_event = asyncio.Event()
        self._published: set[str] = set()

    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    async def publish(self, payload: dict):
        try:
            await self.room.local_participant.publish_data(
                json.dumps(payload).encode()
            )
        except Exception as exc:
            print(f"[Agent] publish failed: {exc}")

    async def publish_agent_speech(self, text: str):
        """Send an interviewer utterance to the client before it is spoken."""
        self.turn_count += 1
        if "?" in text:
            self.q_count += 1

        self._published.add(text)
        self.transcript.append({"role": "agent", "text": text})
        print(f"[Agent] Turn {self.turn_count} (Q{self.q_count}): {text[:80]}")

        await self.publish({
            "type": "agent_speech",
            "text": text,
            "phase": "closing" if self.ending else
                     ("interviewing" if self.turn_count > 1 else "greeting"),
            "q_count": self.q_count,
            "turn_count": self.turn_count,
            "max_questions": MAX_QUESTIONS,
            "elapsed_mins": round(self.elapsed_seconds() / 60, 1),
        })

    def already_published(self, text: str) -> bool:
        return text in self._published

    def request_end(self, reason: str):
        self.ending = True
        self.end_reason = reason
        asyncio.get_event_loop().call_later(
            CLOSING_GRACE_SECONDS, self.end_event.set
        )


async def run_interview(room_name: str):
    ws_url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY", "")
    elevenlabs_key = (os.environ.get("ELEVENLABS_API_KEY", "")
                      or os.environ.get("ELEVEN_API_KEY", ""))
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    seed_questions = _load_seed_questions()
    cv_data = _load_json_env("CV_DATA")
    jd_data = _load_json_env("JD_DATA")

    print(f"[Agent] Room: {room_name} | Position: {jd_data.get('job_title', 'the role')}")
    print(f"[Agent] Config: max_q={MAX_QUESTIONS}, min_q={MIN_QUESTIONS}, "
          f"time={TIME_BUDGET_MINS}min")
    print(f"[Agent] Seed questions: {len(seed_questions)}")
    print(f"[Agent] API keys: gemini={'yes' if gemini_api_key else 'NO'}, "
          f"deepgram={'yes' if deepgram_key else 'NO'}, "
          f"elevenlabs={'yes' if elevenlabs_key else 'NO'}")

    system_prompt = _build_system_prompt(cv_data, jd_data, seed_questions)

    async with agent_utils.http_context.open():
        token = _generate_agent_token(room_name)
        room = rtc.Room()
        await room.connect(ws_url, token)
        print(f"[Agent] Connected to room '{room_name}'")

        hooks = AgentHooks(room, time.time())

        def _mark_candidate_joined(source: str):
            if hooks.candidate_joined:
                return
            hooks.candidate_joined = True
            # The clock starts when the candidate arrives, not when the agent
            # was prewarmed, or the time budget would be spent before they
            # even joined.
            hooks.start_time = time.time()
            print(f"[Agent] Candidate joined ({source}) — starting interview")

        @room.on("participant_connected")
        def _on_participant(participant):
            _mark_candidate_joined(participant.identity)

        # The candidate may already be present if prewarm did not run.
        if room.remote_participants:
            _mark_candidate_joined("already present")

        llm_instance = google.LLM(
            model=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
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

        # Verified at startup rather than assumed: a provider that has run
        # out of quota accepts the connection and returns silence.
        tts, tts_provider = await _select_tts(elevenlabs_key, deepgram_key)
        hooks.tts_provider = tts_provider

        agent = InterviewerAgent(instructions=system_prompt, hooks=hooks)

        session_kwargs = {"tts": tts} if tts is not None else {}
        session = AgentSession(
            stt=stt,
            llm=llm_instance,
            **session_kwargs,
            # AgentSession supplies the bundled Silero VAD by default.
            # Interruptions are allowed so a candidate who starts answering
            # early is still heard — with them disabled the framework logged
            # "skipping reply to user input" and silently dropped answers.
            allow_interruptions=True,
            min_interruption_duration=0.7,
            min_interruption_words=2,
            min_endpointing_delay=0.8,
            max_endpointing_delay=6.0,
        )

        @session.on("conversation_item_added")
        def _on_item(ev):
            item = ev.item
            if not isinstance(item, lk_llm.ChatMessage):
                return
            text = item.text_content
            if not text:
                return

            if item.role == "assistant":
                # tts_node normally publishes first; this is the fallback for
                # anything that reached the transcript without being spoken.
                if not hooks.already_published(text):
                    asyncio.ensure_future(hooks.publish_agent_speech(text))
            elif item.role == "user":
                hooks.transcript.append({"role": "candidate", "text": text})
                print(f"[Agent] Candidate: {text[:80]}")
                asyncio.ensure_future(hooks.publish({
                    "type": "transcript",
                    "text": text,
                    "is_final": True,
                    "q_count": hooks.q_count,
                }))

        @room.on("data_received")
        def _on_data(packet):
            """Collect client-side telemetry: distraction, emotion, attention, voice."""
            try:
                payload = json.loads(packet.data.decode())
            except Exception:
                return

            msg_type = payload.get("type", "")
            payload["timestamp"] = time.time()
            payload["question_number"] = hooks.q_count

            if msg_type == "distraction":
                hooks.distraction_events.append(payload)
                print(f"[Agent] Distraction: {payload.get('detail', 'unknown')} "
                      f"at Q{hooks.q_count}")
            elif msg_type == "emotion":
                hooks.emotion_timeline.append(payload)
            elif msg_type == "attention":
                hooks.attention_events.append(payload)
            elif msg_type == "voice":
                hooks.voice_samples.append(payload)

        await session.start(agent=agent, room=room)
        print("[Agent] Session started - waiting for candidate")

        # Tell the client which voice provider is live so it can warn the
        # candidate if the interview is running text-only.
        await hooks.publish({
            "type": "session_info",
            "tts_provider": tts_provider,
            "voice_enabled": tts is not None,
            "max_questions": MAX_QUESTIONS,
        })

        room.on("disconnected", lambda *_: hooks.end_event.set())

        async def _budget_watchdog():
            """Ask the agent to wrap up once the question or time budget is spent."""
            asked_to_wrap = False
            while not hooks.end_event.is_set():
                await asyncio.sleep(5)
                if asked_to_wrap or hooks.ending or hooks.q_count < MIN_QUESTIONS:
                    continue

                elapsed_mins = hooks.elapsed_seconds() / 60
                over_questions = hooks.q_count >= MAX_QUESTIONS
                over_time = elapsed_mins >= TIME_BUDGET_MINS
                if not (over_questions or over_time):
                    continue

                asked_to_wrap = True
                reason = "question limit" if over_questions else "time budget"
                print(f"[Agent] Wrap-up triggered ({reason}) at Q{hooks.q_count} "
                      f"/ {elapsed_mins:.1f} min")

                await hooks.publish({"type": "wrap_up", "reason": reason})
                try:
                    session.generate_reply(instructions=(
                        "The interview has reached its limit. Give one short "
                        "closing statement thanking the candidate by name and "
                        "telling them their report will be ready shortly, then "
                        "call the end_interview tool with reason 'completed'. "
                        "Do not ask any further questions."
                    ))
                except Exception as exc:
                    print(f"[Agent] Wrap-up reply failed: {exc}")

                # Safety net: close even if the model never calls the tool.
                await asyncio.sleep(35)
                hooks.end_event.set()

        watchdog = asyncio.create_task(_budget_watchdog())
        try:
            await hooks.end_event.wait()
        finally:
            watchdog.cancel()

        await hooks.publish({
            "type": "interview_ended",
            "reason": hooks.end_reason or "disconnected",
            "q_count": hooks.q_count,
        })
        # Give the client a moment to receive the final packet.
        await asyncio.sleep(0.6)

        _save_transcript(room_name, hooks, cv_data, jd_data)

        try:
            await session.aclose()
        except Exception:
            pass
        try:
            await room.disconnect()
        except Exception:
            pass
        print(f"[Agent] Interview ended (reason={hooks.end_reason or 'disconnected'})")


def _save_transcript(room_name: str, hooks: AgentHooks, cv_data: dict, jd_data: dict):
    out_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    out_dir.mkdir(exist_ok=True)
    data = {
        "session": room_name,
        "completed": True,
        "end_reason": hooks.end_reason or "disconnected",
        "questions_count": hooks.q_count,
        "turns_count": hooks.turn_count,
        "elapsed_mins": round(hooks.elapsed_seconds() / 60, 1),
        "conversation": hooks.transcript,
        "distraction_events": hooks.distraction_events,
        "emotion_timeline": hooks.emotion_timeline,
        "attention_events": hooks.attention_events,
        "voice_samples": hooks.voice_samples,
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
