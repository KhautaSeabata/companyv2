from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FIREBASE_DB_BASE = "https://vix75-f6684-default-rtdb.firebaseio.com"
NODE_PATH = "/ticks/R_25.json"
NODE_URL = FIREBASE_DB_BASE + NODE_PATH
MAX_RECORDS = 999

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

async def prune_old_ticks():
    async with httpx.AsyncClient() as client:
        resp = await client.get(NODE_URL)
        data = resp.json()
        if not data:
            return

        # Sort by epoch ascending (oldest first)
        sorted_items = sorted(data.items(), key=lambda item: item[1]["epoch"])
        total = len(sorted_items)

        if total <= MAX_RECORDS:
            return  # no pruning needed

        to_delete = total - MAX_RECORDS
        keys_to_delete = [k for k, v in sorted_items[:to_delete]]

        delete_payload = {key: None for key in keys_to_delete}

        patch_url = FIREBASE_DB_BASE + "/ticks/R_25.json"
        await client.patch(patch_url, json=delete_payload)

async def fetch_last_300_ticks():
    async with httpx.AsyncClient() as client:
        resp = await client.get(NODE_URL)
        data = resp.json()
        if not data:
            return []
        ticks_list = list(data.values())
        ticks_list.sort(key=lambda x: x["epoch"])
        return ticks_list[-300:]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await prune_old_ticks()  # prune old ticks first
            ticks_list = await fetch_last_300_ticks()
            signal = analyze_pattern(ticks_list)
            await manager.send_json(websocket, {"ticks": ticks_list, "signal": signal})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
