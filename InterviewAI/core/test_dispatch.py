"""Test agent dispatch."""
import sys, os, json, urllib.request, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from livekit.api import LiveKitAPI
from livekit.api.agent_dispatch_service import CreateAgentDispatchRequest

async def main():
    # 1. Get a token (which should dispatch)
    resp = urllib.request.urlopen("http://localhost:18765/token")
    data = json.loads(resp.read())
    room_name = data["room"]
    print(f"Room: {room_name}")

    # 2. Check dispatches
    api = LiveKitAPI("ws://localhost:7880", "devkey", "secret")
    try:
        dispatches = await api.agent_dispatch.list_dispatch(
            # Use a simple approach - list all
        )
        print(f"Dispatches: {dispatches}")
    except Exception as e:
        print(f"List error: {e}")

    # 3. Try to check room participants
    try:
        participants = await api.room.list_participants(room_name)
        print(f"Participants: {participants}")
    except Exception as e:
        print(f"Participants error: {e}")

    await api.aclose()

asyncio.run(main())
