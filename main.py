import os
from dotenv import load_dotenv
import requests

load_dotenv()
print("API Key:", os.getenv("TOGETHER_API_KEY"))  # Debugging

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key not found! Check your .env file.")

url = "https://api.together.xyz/v1/chat/completions"

def chat_with_mixtral(prompt):
    payload = {
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Use this model name
    "messages": [{"role": "user", "content": prompt}]
}


    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

# Test the chatbot
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    response = chat_with_mixtral(user_input)
    print(f"Bot: {response}")
