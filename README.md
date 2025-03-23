
## 🚀 Features
- AI-powered chatbot using Llama 3
- WebSocket-based real-time communication
- Firebase Firestore integration for chat logging
- Automatic reconnection and keep-alive functionality
- API request retries for robustness

## 📂 Project Structure
```
BookPulse-AI/
├── main.py               # FastAPI application with WebSocket support
├── api_test.py           # API testing script
├── db.py                 # Database connection management
├── .env                  # Environment variables (API keys, credentials)
├── .gitignore            # Ignored files (API keys, logs, virtual environments)
└── README.md             # Project documentation
```

## 🛠️ Installation & Setup
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/yourusername/BookPulse-AI.git
cd BookPulse-AI
```

### 2️⃣ Set Up a Virtual Environment (Optional but Recommended)
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables
Create a `.env` file in the project root and add:
```ini
TOGETHER_API_KEY=your_together_api_key
```

### 5️⃣ Set Up Firebase Credentials
'''
cred = credentials.Certificate("/path/to/your/firebase.json")
```

### 6️⃣ Run the Server
```sh
uvicorn main:app --reload
```

## 🔌 WebSocket Usage
Connect to the WebSocket endpoint using any WebSocket client:
```
ws://localhost:8000/ws/chat
```
Send a message and receive AI-generated responses.

## 🔒 Security & Best Practices
- **DO NOT** commit `.env` or Firebase credentials to version control.
- Add the following to your `.gitignore`:
  ```
  .env
  chatlogs-*.json
  __pycache__/
  venv/
  *.log
  ```
- Rotate API keys periodically.
