"""Server-side voice: Deepgram STT + ElevenLabs TTS.

Used by app.py Step 6 for accurate speech transcription.
"""

import io
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"   # Rachel


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes with Deepgram REST API (nova-3)."""
    if not DEEPGRAM_API_KEY:
        return ""

    url = "https://api.deepgram.com/v1/listen?model=nova-3&language=en&punctuate=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm",
    }
    try:
        resp = requests.post(url, headers=headers, data=audio_bytes, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    except Exception:
        pass
    return ""


def synthesize_speech(text: str) -> bytes:
    """Generate TTS audio bytes using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        return b""

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return b""
