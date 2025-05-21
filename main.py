from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Firebase URLs
FIREBASE_TICKS_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/R_25.json"
FIREBASE_1MIN_URL = "https://data-364f1-default-rtdb.firebaseio.com/1minVix25.json"

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/ticks")
async def get_ticks():
    """Return last 300 ticks sorted by epoch"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FIREBASE_TICKS_URL) as resp:
                data = await resp.json()
                if not data:
                    return JSONResponse(content=[])
                sorted_data = sorted(data.values(), key=lambda x: x["epoch"])
                last_300 = sorted_data[-300:]
                return JSONResponse(content=last_300)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/candles")
async def get_candles():
    """Return all 1-min OHLC candles sorted by time"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FIREBASE_1MIN_URL) as resp:
                data = await resp.json()
                if not data:
                    return JSONResponse(content=[])
                sorted_data = sorted(data.values(), key=lambda x: x["time"])  # time = candle open epoch
                return JSONResponse(content=sorted_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
