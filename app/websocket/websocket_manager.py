from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Map: room_id -> List[{ "ws": WebSocket, "user_id": str }]
        self.active_rooms: Dict[str, List[Dict]] = {}

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket, user_name: str = "Anonymous"):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        
        self.active_rooms[room_id].append({"ws": websocket, "user_id": user_id, "user_name": user_name})

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_rooms:
            self.active_rooms[room_id] = [
                c for c in self.active_rooms[room_id] 
                if c["ws"] != websocket
            ]
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude_ws: WebSocket = None):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                if connection["ws"] != exclude_ws:
                    try:
                        await connection["ws"].send_json(message)
                    except:
                        pass

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except:
            pass

    async def send_to_user(self, room_id: str, target_user_id: str, message: dict):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                if connection["user_id"] == target_user_id:
                    try:
                        await connection["ws"].send_json(message)
                    except:
                        pass
                    return

    def get_participants(self, room_id: str) -> List[Dict]:
        if room_id in self.active_rooms:
            return [
                {"userId": c["user_id"], "userName": c.get("user_name", "Anonymous")}
                for c in self.active_rooms[room_id]
            ]
        return []

connection_manager = ConnectionManager()
