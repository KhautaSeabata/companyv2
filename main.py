# main.py

import time
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from analyzer.analyzer import Analyzer
from notifier import send_signal_to_telegram

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your analyzer (head and shoulders, double top, trendline, channel, etc.)
analyzer = Analyzer()

# Simulated database or price stream (replace this with actual Firebase or Deriv WebSocket)
price_history = []

# Simulate incoming tick data for testing
async def fake_tick_stream():
    import random
    price = 1000
    while True:
        price += random.uniform(-1, 1)
        tick = {
            "epoch": int(time.time()),
            "quote": round(price, 2)
        }
        price_history.append(tick)
        if len(price_history) > 500:
            price_history.pop(0)
        await asyncio.sleep(1)

# Analyze prices every second
async def analyze_loop():
    while True:
        if len(price_history) > 50:
            signal = analyzer.analyze(price_history)
            if signal:
                print("✅ Signal detected:", signal)
                send_signal_to_telegram(signal)
        await asyncio.sleep(2)

# WebSocket endpoint for client
@app.websocket("/ws/{index}/{tf}")
async def websocket_endpoint(websocket: WebSocket, index: str, tf: str):
    await websocket.accept()
    try:
        while True:
            candles = analyzer.get_candles(price_history, tf)
            await websocket.send_json({"candles": candles})
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Startup background tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fake_tick_stream())  # Remove if using real tick stream
    asyncio.create_task(analyze_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
