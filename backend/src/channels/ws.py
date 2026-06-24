from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, channel_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[channel_id].append(ws)

    def disconnect(self, channel_id: str, ws: WebSocket) -> None:
        self._connections[channel_id].remove(ws)

    async def broadcast(self, channel_id: str, message: dict) -> None:
        for ws in list(self._connections[channel_id]):
            await ws.send_json(message)

    async def broadcast_others(self, channel_id: str, sender: WebSocket, message: dict) -> None:
        for ws in list(self._connections[channel_id]):
            if ws is not sender:
                await ws.send_json(message)


manager = ConnectionManager()

