import asyncio, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
from collections import defaultdict
from datetime import datetime, timedelta

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com"

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, index: str):
        await websocket.accept()
        self.active_connections[index].append(websocket)

    def disconnect(self, websocket: WebSocket, index: str):
        self.active_connections[index].remove(websocket)

    async def send_message(self, index: str, message: str):
        for ws in self.active_connections[index]:
            await ws.send_text(message)

manager = ConnectionManager()

async def fetch_ticks(index: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FIREBASE_URL}/{index}.json")
        data = resp.json()
        if not data:
            return []
        return sorted(data.values(), key=lambda x: x["timestamp"])

def aggregate_candles(ticks, timeframe_sec):
    candles = []
    current = None
    for tick in ticks:
        ts = tick["timestamp"]
        dt = datetime.fromtimestamp(ts)
        bucket = dt - timedelta(seconds=dt.second % timeframe_sec, microseconds=dt.microsecond)

        if not current or current["bucket"] != bucket:
            if current:
                candles.append(current)
            current = {
                "time": bucket.timestamp(),
                "bucket": bucket,
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "close": tick["price"],
            }
        else:
            current["high"] = max(current["high"], tick["price"])
            current["low"] = min(current["low"], tick["price"])
            current["close"] = tick["price"]
    if current:
        candles.append(current)
    return candles

@app.websocket("/ws/{index}/{tf}")
async def chart_ws(websocket: WebSocket, index: str, tf: str):
    await manager.connect(websocket, index)
    try:
        ticks = await fetch_ticks(index)
        tf_map = {"tick": 0, "1": 60, "2": 120, "3": 180, "4": 240, "5": 300}
        timeframe = tf_map.get(tf, 60)

        if timeframe == 0:
            candles = [{"time": tick["timestamp"], "open": tick["price"], "high": tick["price"],
                        "low": tick["price"], "close": tick["price"]} for tick in ticks]
        else:
            candles = aggregate_candles(ticks, timeframe)

        await websocket.send_text(json.dumps({"candles": candles}))

        while True:
            ticks = await fetch_ticks(index)
            if not ticks:
                await asyncio.sleep(1)
                continue

            latest_tick = ticks[-1]
            message = {
                "tick": {
                    "price": latest_tick["price"],
                    "timestamp": latest_tick["timestamp"],
                    "time": latest_tick["time"],
                }
            }
            await manager.send_message(index, json.dumps(message))
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket, index)
