import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:3000/voice/ws"
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending Twilio start frame...")
            # Twilio's first frame is a connected message? No, according to hindi_bot_logic.py:
            # start_data = websocket.iter_text()
            # await start_data.__anext__()
            # call_data = json.loads(await start_data.__anext__())
            # stream_sid = call_data["start"]["streamSid"]
            
            # 1. Connected
            await websocket.send(json.dumps({"event": "connected", "protocol": "Call", "version": "1.0.0"}))
            # 2. Start
            await websocket.send(json.dumps({"event": "start", "sequenceNumber": "1", "start": {"streamSid": "MZ123", "accountSid": "AC123", "callSid": "CA123", "customParameters": {}}}))
            
            print("Sent start frames. Waiting for response...")
            # We just need to see if it doesn't crash.
            for i in range(2):
                msg = await websocket.recv()
                print(f"Received: {msg[:100]}...")
            print("Test passed.")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
