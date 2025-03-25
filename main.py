import os
import httpx
import firebase_admin
import spacy
from firebase_admin import credentials, firestore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables from .env file
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
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

app = FastAPI()

# Intent Detection using Llama 3
async def detect_intent(prompt):
    system_prompt = "You are an AI chatbot for a bookstore. Classify the user's intent into: 'discount', 'book_info', 'purchase', 'general_chat'. Return only the category name."
    
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        "max_tokens": 10
    }
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(TOGETHER_API_URL, json=payload, headers=headers)
        intent = response.json()["choices"][0]["message"]["content"].strip().lower()
        return intent

async def chat_with_mixtral(prompt, chat_history):
    system_prompt = "You are a helpful AI assistant for an online bookstore. Use emojis to make chat friendly 😊. Keep responses short, engaging, and lead-focused."
    
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
            except httpx.RequestError:
                await asyncio.sleep(1)
        return "AI model is currently unavailable. Please try again later."

def generate_coupon():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def send_coupon_email(user_email, coupon_code):
    message = Mail(
        from_email="ujjwalpardeshi@gmail.com",
        to_emails=user_email,
        subject="Your Special Discount Coupon 🎁",
        html_content=f"""
            <strong>Hi there! 💖 Here's a special gift for you!</strong><br>
            Use the code <b>{coupon_code}</b> to get a discount on your next purchase. 
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"Email Error: {e}")

async def save_to_firestore(user_msg, bot_resp):
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

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("INFO: WebSocket connection opened")
    
    is_connected = True
    chat_history = []
    user_email = None
    
    async def keep_alive():
        while is_connected:
            try:
                await asyncio.sleep(15)
                await websocket.send_text("PING")
            except WebSocketDisconnect:
                break
    
    keep_alive_task = asyncio.create_task(keep_alive())

    while is_connected:
        try:
            data = await websocket.receive_text()
            if not data.strip():
                continue
            if data.strip().upper() == "PING":
                continue
            
            intent = await detect_intent(data)
            
            if intent == "discount":
                await websocket.send_text("That's great! 🎁 We have special discounts. Share your email for a coupon! 💖")
                continue
            
            if "@" in data and "." in data and user_email is None:
                user_email = data.strip()
                coupon_code = generate_coupon()
                await websocket.send_text(f"Thanks! 🎉 Your discount code: {coupon_code}. We've emailed it to you! 📩")
                send_coupon_email(user_email, coupon_code)
                db.collection("user_emails").document().set({"email": user_email, "coupon_code": coupon_code, "timestamp": datetime.utcnow()})
                continue
            
            response = await chat_with_mixtral(data, chat_history)
            chat_history.append({"role": "user", "content": data})
            chat_history.append({"role": "assistant", "content": response})
            
            asyncio.create_task(save_to_firestore(data, response))
            await websocket.send_text(response)
        
        except WebSocketDisconnect:
            is_connected = False
            break
        except Exception as e:
            print(f"ERROR: {e}")
            is_connected = False
            break
    
    keep_alive_task.cancel()
