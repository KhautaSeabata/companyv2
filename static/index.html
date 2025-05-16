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

async def fetch_all_ticks():
    async with httpx.AsyncClient() as client:
        resp = await client.get(FIREBASE_DB_URL)
        resp.raise_for_status()
        return resp.json()

@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await manager.connect(websocket)
    try:
        # Send historical data first
        all_ticks = await fetch_all_ticks()
        sorted_ticks = sorted(all_ticks.values(), key=lambda x: x["timestamp"])
        recent_ticks = sorted_ticks[-200:]

        history = [
            {
                "quote": tick["price"],
                "epoch": tick["timestamp"],
                "time": tick["time"]
            }
            for tick in recent_ticks
        ]
        await manager.send_message(websocket, json.dumps({"history": history}))

        # Stream live data
        while True:
            latest_tick = sorted_ticks[-1] if sorted_ticks else None
            new_ticks = await fetch_all_ticks()
            new_sorted = sorted(new_ticks.values(), key=lambda x: x["timestamp"])
            if latest_tick and new_sorted[-1]["timestamp"] != latest_tick["timestamp"]:
                latest_tick = new_sorted[-1]
                message = {
                    "tick": {
                        "quote": latest_tick["price"],
                        "epoch": latest_tick["timestamp"],
                        "time": latest_tick["time"]
                    }
                }
                await manager.send_message(websocket, json.dumps(message))
                sorted_ticks = new_sorted
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
