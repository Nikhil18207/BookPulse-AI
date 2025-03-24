import os
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv
import requests

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

url = "https://api.together.xyz/v1/chat/completions"

app = FastAPI()

async def chat_with_mixtral(user_message):
    prompt = f"""
    You are a helpful AI assistant for a bookstore, specializing in customer engagement and lead conversion.
    - Provide **concise** responses (1-2 lines).
    - Help users find books based on their interests.
    - Recommend books based on bestsellers and reviews.
    - Encourage purchases and notify about discounts.
    - Answer FAQs about book availability, delivery, and pricing.
    
    User: {user_message}
    Assistant:"""
    
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            response = await chat_with_mixtral(data)
            await websocket.send_text(response)
        except Exception as e:
            await websocket.close()
            break
