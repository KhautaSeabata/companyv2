from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/data")
async def get_vix75_data():
    url = "https://data-364f1-default-rtdb.firebaseio.com/Vix75.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    ticks = sorted(data.values(), key=lambda x: x["timestamp"])
    candles = []
    current = None
    current_minute = None

    for tick in ticks:
        ts = tick["timestamp"]
        dt = datetime.datetime.fromtimestamp(ts)
        minute_key = dt.replace(second=0)

        if current_minute != minute_key:
            if current:
                candles.append(current)
            current = {
                "time": minute_key.isoformat(),
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "close": tick["price"]
            }
            current_minute = minute_key
        else:
            current["high"] = max(current["high"], tick["price"])
            current["low"] = min(current["low"], tick["price"])
            current["close"] = tick["price"]

    if current:
        candles.append(current)

    return candles

