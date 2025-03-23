# BookPulse-AI Chatbot

BookPulse-AI is an AI-powered chatbot designed for bookstores, providing engaging and lead-driven responses. It leverages FastAPI, WebSockets, Firebase Firestore, and Together AI's Llama 3 model to offer real-time interactions.

## Features
- AI chatbot powered by Together AI (Llama 3)
- WebSocket-based real-time chat
- Firestore integration for chat history storage
- Automatic Firebase reinitialization for stability
- Keep-alive mechanism to maintain WebSocket connection

## Installation

### Prerequisites
- Python 3.10+
- Firebase Firestore credentials (JSON file)
- Together AI API Key

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/BookPulse-AI.git
   cd BookPulse-AI
   ```

2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file:
     ```sh
     touch .env
     ```
   - Add the following variables:
     ```ini
     TOGETHER_API_KEY=your_api_key_here
     ```

5. Add your Firebase credentials JSON file and update the path in `main.py`:
   ```python
   cred = credentials.Certificate("path/to/your-firebase.json")
   ```

## Running the Application
```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## WebSocket Usage
Connect to WebSocket endpoint:
```
ws://localhost:8000/ws/chat
```
Send a message and receive AI-generated responses.

## API Overview
- **WebSocket Endpoint:** `/ws/chat` 
  - Sends messages and receives chatbot responses in real-time.
  - Includes keep-alive mechanism to prevent disconnects.

## Deployment
You can deploy the application using Docker, AWS, or any cloud provider supporting FastAPI.

## Contributing
Feel free to fork this project and contribute!

## License
MIT License