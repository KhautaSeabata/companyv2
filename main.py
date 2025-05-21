from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio
import time
import json
from pattern_detector import detect_patterns

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Firebase URLs
FIREBASE_TICKS_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/R_25.json"
FIREBASE_PATTERNS_URL = "https://data-364f1-default-rtdb.firebaseio.com/patterns.json"

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

@app.get("/api/patterns")
async def get_patterns():
    """Return detected patterns"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FIREBASE_PATTERNS_URL) as resp:
                data = await resp.json()
                if not data:
                    return JSONResponse(content=[])
                patterns = list(data.values())
                return JSONResponse(content=patterns)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

async def detect_and_store_patterns():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FIREBASE_TICKS_URL) as resp:
                    data = await resp.json()
                    if data:
                        sorted_data = sorted(data.values(), key=lambda x: x["epoch"])
                        patterns = detect_patterns(sorted_data)
                        if patterns:
                            for pattern in patterns:
                                timestamp = int(time.time() * 1000)
                                pattern_data = {
                                    "entry_price": pattern["entry_price"],
                                    "stop_loss": pattern["stop_loss"],
                                    "take_profit": pattern["take_profit"],
                                    "pattern": pattern["pattern"],
                                    "timestamp": timestamp
                                }
                                await session.post(FIREBASE_PATTERNS_URL, json=pattern_data)
        except Exception as e:
            print(f"Error detecting/storing patterns: {e}")
        await asyncio.sleep(60)  # Wait for 60 seconds before next check

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(detect_and_store_patterns())
