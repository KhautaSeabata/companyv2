from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import time
from datetime import datetime
from collections import defaultdict

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

html_path = "static/index.html"

@app.get("/")
async def get():
    with open(html_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

# Simulated tick stream (you should replace this with real data source)
async def get_latest_tick():
    now = int(time.time())
    price = 1000 + (now % 100) * 0.1  # Simulated price
    return {
        "price": round(price, 2),
        "timestamp": now,
        "time": datetime.utcfromtimestamp(now).strftime("%H:%M:%S")
    }

clients = set()

@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    clients.add(websocket)
    ticks = []

    try:
        while True:
            tick = await get_latest_tick()
            ticks.append(tick)

            # Extract timeframe from query params
            params = websocket.query_params
            timeframe = params.get("timeframe", "tick")

            if timeframe == "tick":
                data = {
                    "tick": {
                        "quote": tick["price"],
                        "epoch": tick["timestamp"],
                        "time": tick["time"]
                    }
                }
            else:
                interval = int(timeframe)
                candles = group_ticks_to_ohlc(ticks, interval)
                data = {
                    "candles": candles[-60:]  # Last 60 candles
                }

            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        clients.remove(websocket)

def group_ticks_to_ohlc(ticks, interval_sec):
    candles = {}
    for tick in ticks:
        key = tick["timestamp"] - (tick["timestamp"] % interval_sec)
        if key not in candles:
            candles[key] = {
                "timestamp": key,
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "close": tick["price"]
            }
        else:
            candles[key]["high"] = max(candles[key]["high"], tick["price"])
            candles[key]["low"] = min(candles[key]["low"], tick["price"])
            candles[key]["close"] = tick["price"]
    return [candles[k] for k in sorted(candles)]
