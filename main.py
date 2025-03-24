import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import requests

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

url = "https://api.together.xyz/v1/chat/completions"

app = FastAPI()

# Configure Logging
logging.basicConfig(filename="chat_logs.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Store active WebSocket connections
active_connections = set()

async def chat_with_mixtral(prompt):
    """
    Send a request to Together API and get a chatbot response.
    Ensures short, engaging, and lead-driven responses.
    """
    system_prompt = "You are a helpful AI assistant for a bookstore. " \
                    "Keep responses short (1-2 sentences), engaging, and lead-focused. " \
                    "Encourage book purchases or capture leads for follow-ups."

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 50  # Limit response length
    }

    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        bot_response = response.json()["choices"][0]["message"]["content"]
        logging.info(f"User: {prompt} | Bot: {bot_response}")
        return bot_response
    else:
        return f"Error: {response.text}"

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    Supports multiple users and logs interactions.
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            response = await chat_with_mixtral(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logging.info("A user disconnected.")
