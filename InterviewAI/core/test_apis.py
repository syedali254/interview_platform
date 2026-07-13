"""Quick test for all three APIs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.livekit.voice import synthesize_speech, transcribe_audio
from core.llm import call_llm

# 1. Gemini
print("=== Gemini ===")
try:
    r = call_llm("Say hello in one word", temperature=0.1)
    print(f"OK: {r}")
except Exception as e:
    print(f"FAIL: {e}")

# 2. ElevenLabs TTS
print("=== ElevenLabs TTS ===")
try:
    audio = synthesize_speech("Hello, this is a test.")
    if audio:
        print(f"OK: {len(audio)} bytes")
    else:
        print("FAIL: no audio returned")
except Exception as e:
    print(f"FAIL: {e}")

# 3. Deepgram STT
print("=== Deepgram STT ===")
try:
    # small valid webm with silence
    result = transcribe_audio(b"\x1a\x45\xdf\xa3" + b"\x00" * 2000)
    print(f"OK: '{result}'")
except Exception as e:
    print(f"FAIL: {e}")

print("\nDone")
