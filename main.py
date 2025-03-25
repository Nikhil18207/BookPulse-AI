import os
import httpx
import firebase_admin
import spacy
from firebase_admin import credentials, firestore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import asyncio
from datetime import datetime

load_dotenv()

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Firebase Initialization
def initialize_firebase():
    global db
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin.get_app())

    try:
        cred = credentials.Certificate("/var/home/ujjain/Desktop/code/BookPulse-AI/chatlogs-44941-firebase-adminsdk-fbsvc-a01056838e.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("INFO: Firebase initialized successfully")
    except Exception as e:
        print(f"ERROR: Firebase initialization failed: {e}")

initialize_firebase()

# API Keys
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

app = FastAPI()

def extract_book_name(text):
    """
    Uses spaCy Named Entity Recognition (NER) to detect book names from user input.
    """
    doc = nlp(text)
    books = [ent.text for ent in doc.ents if ent.label_ in ["WORK_OF_ART"]]
    return books if books else None

async def chat_with_mixtral(prompt, chat_history):
    """
    Sends user input along with past conversation history to Together AI API.
    """
    system_prompt = "You are a helpful AI assistant for an online bookstore. " \
                    "You're based in India, so show prices in Rupees. " \
                    "Use emojis to make the conversation friendly 😊. " \
                    "Keep responses short, engaging, and lead-focused."

    book_names = extract_book_name(prompt)

    if book_names:
        book_list = ", ".join(book_names)
        system_prompt += f"\nUser is interested in these books: {book_list}. Provide relevant information or purchase links."

    messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": prompt}]

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": messages,
        "max_tokens": 100
    }
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}

    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                response = await client.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.RequestError as e:
                print(f"API Error (Retrying...): {str(e)}")
                await asyncio.sleep(1)
            except httpx.HTTPStatusError as e:
                return f"HTTP Error: {e.response.text}"
        return "AI model is currently unavailable. Please try again later."

async def save_to_firestore(user_msg: str, bot_resp: str):
    global db
    try:
        db.collection("chat_history").document().set({
            "user_message": user_msg,
            "bot_response": bot_resp,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print(f"Firestore Error: {e}")
        initialize_firebase()

async def get_last_messages():
    """
    Fetches the last few messages from Firestore for context retention.
    """
    try:
        messages_ref = db.collection("chat_history").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5)
        messages = messages_ref.stream()

        chat_history = []
        for msg in messages:
            data = msg.to_dict()
            chat_history.append({"role": "user", "content": data["user_message"]})
            chat_history.append({"role": "assistant", "content": data["bot_response"]})

        return list(reversed(chat_history))  # Reverse to maintain chronological order
    except Exception as e:
        print(f"Firestore Fetch Error: {e}")
        return []

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("INFO: WebSocket connection opened")

    is_connected = True
    chat_history = await get_last_messages()  # Load past context

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

    keep_alive_task = asyncio.create_task(keep_alive())

    while is_connected:
        try:
            data = await websocket.receive_text()

            if not data.strip():
                continue

            if data.strip().upper() == "PING":
                continue

            response = await chat_with_mixtral(data, chat_history)

            # Update session chat history
            chat_history.append({"role": "user", "content": data})
            chat_history.append({"role": "assistant", "content": response})

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

    keep_alive_task.cancel()
