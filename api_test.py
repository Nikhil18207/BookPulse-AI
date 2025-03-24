import websockets
import asyncio

async def chat():
    uri = "ws://127.0.0.1:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        while True:
            msg = input("You: ")
            if msg.lower() in ["exit", "quit"]:
                break
            await websocket.send(msg)
            response = await websocket.recv()
            print(f"Bot: {response}")

asyncio.run(chat())
