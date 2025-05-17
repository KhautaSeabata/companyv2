import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

app = FastAPI()

# Serve static files from ./static folder at /static route
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse("static/index.html")


FIREBASE_DB_URL = "https://data-364f1-default-rtdb.firebaseio.com/Vix75.json"

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)

manager = ConnectionManager()

async def get_latest_tick():
    """Fetch latest tick from Firebase Realtime Database."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(FIREBASE_DB_URL)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        # data is dict of ticks keyed by random ids, get the one with max timestamp
        latest_tick = max(data.values(), key=lambda x: x["timestamp"])
        return latest_tick

@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await manager.connect(websocket)
    try:
        while True:
            # fetch latest tick from Firebase every second
            tick = await get_latest_tick()
            if tick is None:
                await asyncio.sleep(1)
                continue

            # Prepare message JSON to send
            message = {
                "tick": {
                    "quote": tick["price"],
                    "epoch": tick["timestamp"],
                    "time": tick["time"],
                },
                # Example: no signal here, but you can add signal data
                # "signal": {
                #     "signal": "buy",
                #     "entry": tick["price"],
                #     "tp": tick["price"] + 10,
                #     "sl": tick["price"] - 10,
                #     "timestamp": tick["timestamp"]
                # }
            }

            await manager.send_message(websocket, json.dumps(message))
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
