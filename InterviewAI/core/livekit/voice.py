"""Server-side voice: faster-whisper STT + edge-tts TTS.

Used by app.py Step 6 for accurate speech transcription.
"""

import io
import os
import tempfile
import wave
from pathlib import Path


# ── Lazy-loaded whisper model ────────────────────────────────────────────
_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print("[Whisper] Loading model (base)...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print("[Whisper] Model loaded.")
    return _whisper_model


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe raw PCM audio bytes with faster-whisper."""
    model = _get_whisper()

    # Save to temp WAV file (faster-whisper reads from file or numpy)
    import soundfile as sf
    import numpy as np

    try:
        data, samplerate = sf.read(io.BytesIO(audio_bytes))
    except Exception:
        # Try as raw PCM (16-bit, 16kHz, mono)
        data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        samplerate = 16000

    segments, _ = model.transcribe(data, beam_size=5, language="en")
    return " ".join(seg.text for seg in segments).strip()


def synthesize_speech(text: str, voice: str = "en-GB-SoniaNeural") -> bytes:
    """Generate TTS audio bytes using edge-tts."""
    import edge_tts
    import asyncio

    async def _synth():
        communicate = edge_tts.Communicate(text, voice=voice)
        audio = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
        return audio

    return asyncio.run(_synth())
