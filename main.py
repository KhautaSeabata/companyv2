from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FIREBASE_DB_URL = "https://company-bdb78-default-rtdb.firebaseio.com"

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data):
        await websocket.send_text(json.dumps(data))

manager = ConnectionManager()

def analyze_pattern(ticks):
    if len(ticks) < 5:
        return None
    last = ticks[-1]["quote"]
    prev = ticks[-5]["quote"]
    if last > prev * 1.005:
        return {
            "pattern": "DummyUptrend",
            "entry": last,
            "tp": round(last * 1.01, 2),
            "sl": round(last * 0.995, 2),
            "time": ticks[-1]["epoch"],
            "status": "Active"
        }
    return None

async def fetch_last_300_ticks():
    async with httpx.AsyncClient() as client:
        resp = await client.get(FIREBASE_DB_URL)
        data = resp.json()
        if not data:
            return []
        ticks_list = list(data.values())
        ticks_list.sort(key=lambda x: x["epoch"])
        return ticks_list[-300:]

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            ticks_list = await fetch_last_300_ticks()
            signal = analyze_pattern(ticks_list)
            await manager.send_json(websocket, {"ticks": ticks_list, "signal": signal})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
 
