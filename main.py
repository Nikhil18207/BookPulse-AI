import os
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

app = FastAPI()

# Root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "API is running!"}

class ChatRequest(BaseModel):
    message: str

def chat_with_mixtral(prompt):
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
    response = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

# Chatbot endpoint
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    response = chat_with_mixtral(chat_request.message)
    return {"response": response}
