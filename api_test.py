import websockets
import asyncio

async def chat():
    uri = "ws://127.0.0.1:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                msg = input("You: ")
                if msg.lower() in ["exit", "quit"]:
                    break

                await websocket.send(msg)
                while True:
                    response = await websocket.recv()
                    if response == "PING":  
                        continue
                    print(f"Bot: {response}")
                    break  # Exit loop after receiving response
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server.")

if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(chat())
