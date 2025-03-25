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

def generate_coupon():
    """
    Generates a unique 10-character coupon code.
    """
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(letters_and_digits, k=10))

def send_coupon_email(user_email, coupon_code):
    """
    Sends an email using SendGrid with the discount coupon.
    """
    message = Mail(
        from_email="ujjwalpardeshi@gmail.com",  # Replace with your verified email
        to_emails=user_email,
        subject="Your Special Discount Coupon 🎁",
        html_content=f"""
            <strong>Hi there! 💖 Here's a special gift for you!</strong><br>
            Use the code <b>{coupon_code}</b> to get a discount on your next purchase. 
            Thank you for being awesome! 🌟
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {user_email}: {response.status_code}")
    except Exception as e:
        print(f"Email Error: {e}")


async def save_to_firestore(user_msg: str, bot_resp: str):
    """
    Saves chat messages to Firebase Firestore.
    """
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
    chat_history = []  # Only session-based context retention
    user_email = None
    message_count = 0  # Track messages for email prompt

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

            message_count += 1

            # Ask for email after 3 messages
            if message_count == 3 and not user_email:
                await websocket.send_text("Hey! 🎁 We'd love to send you a free gift! Please share your email 💖.")
                continue

            # If user provides email, store it and send coupon
            if "@" in data and "." in data and user_email is None:
                user_email = data.strip()
                coupon_code = generate_coupon()
                await websocket.send_text(f"Thanks! 🎉 Your discount code is: {coupon_code}. We've also emailed it to you! 📩")
                send_coupon_email(user_email, coupon_code)

                # Save email to Firebase
                db.collection("user_emails").document().set({
                    "email": user_email,
                    "coupon_code": coupon_code,
                    "timestamp": datetime.utcnow()
                })
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
