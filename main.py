import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com"

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

async def get_latest_tick(symbol: str):
    async with httpx.AsyncClient() as client:
        url = f"{FIREBASE_URL}/{symbol}.json"
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return max(data.values(), key=lambda x: x["timestamp"])

@app.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket)
    try:
        while True:
            tick = await get_latest_tick(symbol)
            if tick:
                message = {
                    "symbol": symbol,
                    "tick": {
                        "quote": tick["price"],
                        "epoch": tick["timestamp"],
                        "time": tick["time"],
                    }
                }
                await manager.send_message(websocket, json.dumps(message))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
