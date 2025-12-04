# Dicer (backend)

Lightweight FastAPI backend that provides WebSocket-based chat rooms and a dice-rolling API intended for tabletop-style games.

This server supports:
- Creating rooms
- Joining rooms over WebSockets
- Sending chat messages
- Rolling dice using a JSON formula and broadcasting results to all room participants

---

## Quick summary

- Language: Python
- Web framework: FastAPI
- ASGI server: uvicorn
- WebSocket support via FastAPI + websockets

Files of interest:
- `main.py` — FastAPI app with endpoints and WebSocket handler
- `utils.py` — Dice roll logic and helper to render formulas as strings
- `requirements.txt` — pinned dependency list

---

## Installation

Recommended: create and use a virtual environment, then install requirements.

On Windows Powershell:

```powershell
python -m venv .venv
; .\.venv\Scripts\Activate.ps1
; python -m pip install --upgrade pip
; pip install -r requirements.txt
```

---

## Run (development)

Start the server with uvicorn from the `backend` folder:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API docs (for the HTTP endpoints) will be available at:

http://127.0.0.1:8000/docs

---

## HTTP API

POST /create_room

Request body (JSON):

```json
{
	"host_id": "string",
	"password": "optional password"
}
```

Response (JSON):

```json
{
	"status": "room_created",
	"room_id": "<generated-room-id>"
}
```

---

## WebSocket protocol

Connect:

ws://{host}:8000/ws/{room_id}/{user_id}

1. Password auntefication (if room has a password):

```json
// Server requires password
{
    "status": "password_required"
}

// User sends password
{
    "password": "***"
}

// Answer when password is wrong
{
    "status": "wrong_password"
}

// Answer when password is correct
{
    "status": "joined_room"
}
```

2. User and server communication:

User-side actions:

```json
// Send message
{ "action": "send_message", "message": "Hello everyone" }

// Get chat history
{ "action": "get_chat_history" }
// Response
{
    "messages": [
        ["", "gorsh04ek has joined the room"],
        ["gorsh04ek", "Hello everyone"], 
        ["noname", "hi"]
    ] 
}


// Leave room
{ "action": "leave_room" }

// Roll dice
{
    "action": "roll_dice",
    "formula": {
        "dices": { "6": 2, "20": 1 },
        "bonus": 3
    }
}
```

Server-side actions:

```json
// When message sent
// broadcasting to everyone
{
    "action": "new_mesage",
    "from": "gorsh04ek",
    "text": "hello!"
}

// When dice rolled
// broadcasting to everyone
{
    "action": "dice_rolled",
    "from": "user123",
    "dices_result": { 
        "6": [4, 2], "20": [17], "2": [], 
        "4": [], "8": [], "10": [], "12": [] 
    },
    "total": 26
}
```

---

## Dice rules / formula notes

- Supported die faces: 2, 4, 6, 8, 10, 12, 20
- `dices` must be an object with the face as a string and the count as an integer
- `bonus` is optional and added to the final total

Examples:
- `{ "dices": {"6": 2}, "bonus": 1 }` -> roll 2d6 + 1
