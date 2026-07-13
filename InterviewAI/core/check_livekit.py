"""Check LiveKit setup end-to-end."""
import sys, os, json, urllib.request, socket, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 1. Check ports
print("=== Port Check ===")
for port, name in [(7880, "LiveKit"), (18765, "Web Server")]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    if s.connect_ex(("127.0.0.1", port)) == 0:
        print(f"  {name} port {port}: OPEN")
    else:
        print(f"  {name} port {port}: CLOSED")
    s.close()

# 2. Check web server token
print("\n=== Token Generation ===")
try:
    resp = urllib.request.urlopen("http://localhost:18765/token")
    data = json.loads(resp.read())
    print(f"  Room: {data['room']}")
    print(f"  Token: {data['token'][:50]}...")
    print(f"  URL: {data['url']}")
except Exception as e:
    print(f"  FAILED: {e}")

# 3. Check agent process
print("\n=== Agent Process ===")
import subprocess
result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], capture_output=True, text=True)
lines = [l for l in result.stdout.split('\n') if 'run_agent' in l.lower() or 'python' in l.lower()]
if lines:
    print(f"  Agent running: {len(lines)} matches")
else:
    print("  Agent: check tasklist above")

# 4. Quick test Gemini + ElevenLabs APIs
print("\n=== API Checks ===")
from core.livekit.voice import synthesize_speech, transcribe_audio
from core.llm import call_llm

try:
    r = call_llm("Say 'test' only", temperature=0.1)
    print(f"  Gemini: {r}")
except Exception as e:
    print(f"  Gemini FAILED: {e}")

try:
    audio = synthesize_speech("Hello test")
    if audio:
        print(f"  ElevenLabs: {len(audio)} bytes")
    else:
        print("  ElevenLabs: 0 bytes (check API key)")
except Exception as e:
    print(f"  ElevenLabs FAILED: {e}")

print("\nDone")
