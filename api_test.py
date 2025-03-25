import websockets
import asyncio

async def chat():
    uri = "ws://127.0.0.1:8000/ws/chat"
    
    while True:  # Auto-reconnect loop
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to server. Type 'exit' to quit.")
                
                while True:
                    msg = input("You: ")
                    if msg.lower() in ["exit", "quit"]:
                        print("Closing connection.")
                        return  

                    await websocket.send(msg)

                    while True:
                        response = await websocket.recv()
                        if response == "PING":  
                            continue  # Ignore PING messages
                        print(f"Bot: {response}")
                        break  

        except websockets.exceptions.ConnectionClosed:
            print("Connection lost. Reconnecting in 3 seconds...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(chat())