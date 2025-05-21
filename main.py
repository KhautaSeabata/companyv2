from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FIREBASE_DB_URL = "https://vix75-f6684-default-rtdb.firebaseio.com/ticks/R_25.json"

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

# Dummy analyzer for example
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
        # data is dict: key -> {epoch, quote, symbol}
        ticks_list = list(data.values())
        # sort by epoch ascending
        ticks_list.sort(key=lambda x: x["epoch"])
        # keep last 300
        return ticks_list[-300:]

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
        print("Client disconnected")
