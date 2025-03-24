import os
import httpx
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import asyncio

load_dotenv()

def initialize_firebase():
    global db
    try:
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())  # Delete previous instance
        cred = credentials.Certificate("/var/home/ujjain/Desktop/code/BookPulse-AI/chatlogs-44941-firebase-adminsdk-fbsvc-a01056838e.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("INFO: Firebase reinitialized successfully")
    except Exception as e:
        print(f"ERROR: Firebase initialization failed: {e}")

initialize_firebase()

# Together AI API Key
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

app = FastAPI()


async def chat_with_mixtral(prompt):
    """
    Send a request to Together API and get a chatbot response.
    Ensures short, engaging, and lead-driven responses.
    """
    system_prompt = "You are a helpful AI assistant for a bookstore. " \
                    "You're based in india so have the prices in Rupees" \
                    "Use emojis to make the conversation friendly 😊. " \
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

    async with httpx.AsyncClient() as client:
        for _ in range(3):  # Retry up to 3 times
            try:
                response = await client.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.RequestError as e:
                print(f"API Error (Retrying...): {str(e)}")
                await asyncio.sleep(1)  # Small delay before retrying
            except httpx.HTTPStatusError as e:
                return f"HTTP Error: {e.response.text}"
        return "AI model is currently unavailable. Please try again later."


async def save_to_firestore(user_msg: str, bot_resp: str):
    global db
    try:
        db.collection("chat_history").document().set({
            "user_message": user_msg,
            "bot_response": bot_resp
        })
    except Exception as e:
        print(f"Firestore Error: {e}")
        initialize_firebase()  

# === 🔹 WebSocket Route 🔹 ===
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("INFO: WebSocket connection opened")

    is_connected = True 

    # === 🔹 Keep WebSocket Alive with Pings (Handles Reconnection) ===
    async def keep_alive():
        while is_connected:
            try:
                await asyncio.sleep(15)
                await websocket.send_text("PING")
            except WebSocketDisconnect:
                print("INFO: WebSocket disconnected during keep-alive")
                break
            except RuntimeError:
                print("INFO: WebSocket already closed, stopping keep-alive task")
                break

    keep_alive_task = asyncio.create_task(keep_alive())  # Start keep-alive task

    while is_connected:
        try:
            data = await websocket.receive_text()

            if data.strip().upper() == "PING":
                continue  # Ignore PING messages from the client

            response = await chat_with_mixtral(data)
            asyncio.create_task(save_to_firestore(data, response))

            await websocket.send_text(response)

        except WebSocketDisconnect:
            print("INFO: WebSocket connection closed")
            is_connected = False
            break
        except RuntimeError:
            print("INFO: WebSocket already closed, skipping message send.")
            is_connected = False
            break
        except Exception as e:
            print(f"ERROR: {e}")
            is_connected = False
            break

    keep_alive_task.cancel()  # Stop the keep-alive task when WebSocket is closed
