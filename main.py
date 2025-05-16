import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FIREBASE_DB_URL = "https://data-364f1-default-rtdb.firebaseio.com/Vix75.json"

@app.get("/")
async def index():
    return FileResponse("static/index.html")

@app.get("/api/vix75")
async def get_vix75_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(FIREBASE_DB_URL)
        response.raise_for_status()
        data = response.json()

    # Convert ticks into sorted list
    sorted_ticks = sorted(data.values(), key=lambda x: x["timestamp"])
    candles = []
    current_candle = {}

    for tick in sorted_ticks:
        ts = tick["timestamp"]
        minute = ts - (ts % 60)
        price = tick["price"]

        if not current_candle or current_candle["time"] != minute:
            if current_candle:
                candles.append(current_candle)
            current_candle = {
                "time": minute * 1000,
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }
        else:
            current_candle["high"] = max(current_candle["high"], price)
            current_candle["low"] = min(current_candle["low"], price)
            current_candle["close"] = price

    if current_candle:
        candles.append(current_candle)

    return candles
