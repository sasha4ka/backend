from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from hashlib import sha256
from time import time

from utils import calculate_roll, formula_to_string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

rooms = []


class Room:
    def __init__(self, host_id: str, password: str):
        self.room_id = sha256(f"{host_id}{time()}".encode()).hexdigest()[:16]
        self.host_id = host_id
        self.password = password
        self.participants = {}
        self.queue = []

    async def add_client(self, user_id: str, websocket: WebSocket):
        try:
            self.participants.update({user_id: websocket})
            for uid, websocket in self.participants.items():
                await websocket.send_json({
                    "action": "room_info",
                    "room_id": self.room_id,
                    "host_id": self.host_id,
                    "participants": list(self.participants.keys())
                })
        except KeyError:
            pass

    async def remove_client(self, user_id: str):
        try:
            self.participants.pop(user_id)
            for uid, websocket in self.participants.items():
                await websocket.send_json({
                    "action": "room_info",
                    "room_id": self.room_id,
                    "host_id": self.host_id,
                    "participants": list(self.participants.keys())
                })
        except KeyError:
            pass
        if len(self.participants) == 0:
            rooms.remove(self)

    async def new_message(self, user_id: str, message: str):
        self.queue.append((user_id, message))
        for uid, ws in self.participants.items():
            await ws.send_json(
                {"action": "new_message",
                    "from": user_id,
                    "text": message}
            )

    async def roll_dice(
        self,
        user_id: str,
        formula: dict,
        dices_result: dict,
        total: int
    ):
        for _, ws in self.participants.items():
            await ws.send_json(
                {"action": "dice_rolled",
                    "from": user_id,
                    "formula": formula,
                    "dices_result": dices_result,
                    "total": total}
            )

    def get_message_queue(self):
        return self.queue

    @staticmethod
    def get_room_by_id(room_id: str) -> 'Room | None':
        for room in rooms:
            if room.room_id == room_id:
                return room
        return None

    def __str__(self):
        return f"Room {self.room_id} hosted by {self.host_id}\n" + \
            f"Participants: {list(self.participants.keys())}\n" + \
            f"Chat: {self.queue}"


rooms.append(Room("host_example", ""))
rooms[0].room_id = "example_room_01"


class create_room_model(BaseModel):
    host_id: str = Field(description="user_id of host")
    password: str = Field(default="", description="password for your room")


@app.post('/room')
async def create_room(model: create_room_model):
    for room in rooms:
        if room.host_id == model.host_id:
            return {"status": "host_already_has_room", "room_id": room.room_id}
    room = Room(model.host_id, model.password)
    rooms.append(room)
    print("\n".join([str(room) for room in rooms]))
    return {"status": "room_created", "room_id": room.room_id}


@app.get('/rooms')
async def get_rooms():
    return {
        "rooms": [
            {
                "room_id": room.room_id,
                "host_id": room.host_id,
                "online": len(room.participants),
                "password_required": bool(room.password)
            } for room in rooms
        ]
    }


@app.websocket('/ws/{room_id}/{user_id}')
async def websocket_listener(
    websocket: WebSocket,
    room_id: str,
    user_id: str
):
    await websocket.accept()
    room = Room.get_room_by_id(room_id)
    if not room:
        await websocket.send_json({
            "status": "room_not_found"
        })
        await websocket.close()
        return

    if room.password:
        await websocket.send_json({
            "status": "password_required"
        })
        password_message = await websocket.receive_json()
        password = password_message.get("password", "")
        if password != room.password:
            await websocket.send_json({
                "status": "wrong_password"
            })
            await websocket.close()
            return

    await websocket.send_json({
        "status": "joined_room"
    })

    await room.add_client(user_id, websocket)
    await room.new_message("", f"{user_id} has joined the room.")
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "send_message":
                message = data.get("message")
                await room.new_message(user_id, message)
            if action == "get_chat_history":
                messages = room.get_message_queue()
                await websocket.send_json({"messages": messages})
            if action == "leave_room":
                await room.remove_client(user_id)
                await room.new_message("", f"{user_id} has left the room.")
                await websocket.close()
                break
            if action == "roll_dice":
                formula = data.get('formula', {})
                result, dices_result = calculate_roll(formula)
                formula_string = formula_to_string(formula)

                if formula_string == "1d2":
                    await room.new_message(
                        "", f"{user_id} flipped a coin: {result}"
                    )
                else:
                    await room.new_message(
                        "",
                        f"{user_id} rolled the dice {formula_string}: {result}"
                    )
                await room.roll_dice(user_id, formula, dices_result, result)
            if action == "get_room_info":
                await websocket.send_json({
                    "action": "room_info",
                    "room_id": room.room_id,
                    "host_id": room.host_id,
                    "participants": list(room.participants.keys())
                })

    except WebSocketDisconnect:
        await room.remove_client(user_id)
        await room.new_message("", f"{user_id} has left the room.")
        print("Client disconnected")
