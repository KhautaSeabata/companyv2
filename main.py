import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import random

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_message(self, client_id: str, message: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

def generate_dummy_candles(count=100, start_price=1000):
    """Generate dummy OHLC candles 1 min apart"""
    candles = []
    base_time = datetime.utcnow() - timedelta(minutes=count)
    price = start_price
    for i in range(count):
        open_p = price
        high_p = open_p + random.uniform(0, 10)
        low_p = open_p - random.uniform(0, 10)
        close_p = low_p + random.uniform(0, high_p - low_p)
        candle = {
            "timestamp": int((base_time + timedelta(minutes=i)).timestamp()),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2)
        }
        price = close_p  # next candle starts from close
        candles.append(candle)
    return candles

def aggregate_ticks_to_candles(ticks, interval_seconds):
    """Aggregate tick data into candles of interval_seconds"""
    if not ticks:
        return []
    candles = []
    ticks_sorted = sorted(ticks, key=lambda x: x["timestamp"])
    bucket_start = ticks_sorted[0]["timestamp"] // interval_seconds * interval_seconds
    o = h = l = c = None
    count = 0
    for tick in ticks_sorted:
        ts = tick["timestamp"]
        p = tick["price"]
        bucket = ts // interval_seconds * interval_seconds
        if bucket != bucket_start:
            # save candle
            candles.append({
                "timestamp": bucket_start,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            })
            # reset for new bucket
            bucket_start = bucket
            o = h = l = c = None
            count = 0
        if count == 0:
            o = h = l = c = p
        else:
            if p > h:
                h = p
            if p < l:
                l = p
            c = p
        count += 1
    # last candle
    if o is not None:
        candles.append({
            "timestamp": bucket_start,
            "open": o,
            "high": h,
            "low": l,
            "close": c
        })
    return candles

@app.websocket("/ws/{index}/{tf}")
async def chart_ws(websocket: WebSocket, index: str, tf: str):
    client_id = f"{index}_{tf}_{id(websocket)}"
    await manager.connect(websocket, client_id)
    print(f"Client connected: {client_id}")
    try:
        # For demo, generate dummy tick data (1 tick per 5 seconds)
        tick_interval_seconds = 5
        total_ticks = 500
        base_time = datetime.utcnow() - timedelta(seconds=tick_interval_seconds * total_ticks)
        ticks = []
        price = 1000
        for i in range(total_ticks):
            ts = int((base_time + timedelta(seconds=i * tick_interval_seconds)).timestamp())
            price += random.uniform(-2, 2)
            ticks.append({"timestamp": ts, "price": round(price, 2)})

        # Parse timeframe in minutes to seconds
        tf_map = {
            "tick": 0,
            "1": 60,
            "2": 120,
            "3": 180,
            "4": 240,
            "5": 300
        }
        interval_seconds = tf_map.get(tf, 60)

        # Aggregate ticks into candles for selected timeframe
        if interval_seconds == 0:
            # Tick data: convert each tick to candle with open=high=low=close=price
            candles = [
                {
                    "timestamp": t["timestamp"],
                    "open": t["price"],
                    "high": t["price"],
                    "low": t["price"],
                    "close": t["price"]
                } for t in ticks
            ]
        else:
            candles = aggregate_ticks_to_candles(ticks, interval_seconds)

        # Send initial historical candles
        await manager.send_message(client_id, json.dumps({"candles": candles}))

        # Simulate live updates: every tick_interval_seconds, send new candle data (append 1 candle)
        current_index = len(candles)
        while True:
            await asyncio.sleep(tick_interval_seconds)
            # Create new tick and candle update
            last_price = ticks[-1]["price"] if ticks else 1000
            new_ts = int(datetime.utcnow().timestamp())
            new_price = round(last_price + random.uniform(-2, 2), 2)
            new_tick = {"timestamp": new_ts, "price": new_price}
            ticks.append(new_tick)

            # Re-aggregate candles with new tick
            if interval_seconds == 0:
                new_candle = {
                    "timestamp": new_ts,
                    "open": new_price,
                    "high": new_price,
                    "low": new_price,
                    "close": new_price
                }
            else:
                candles = aggregate_ticks_to_candles(ticks, interval_seconds)
                new_candle = candles[-1]

            # Send only the latest candle update
            await manager.send_message(client_id, json.dumps({"new_candle": new_candle}))

    except WebSocketDisconnect:
        print(f"Client disconnected: {client_id}")
        manager.disconnect(client_id)
