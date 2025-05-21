from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/R_25.json"

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/ticks")
async def get_ticks():
    async with aiohttp.ClientSession() as session:
        async with session.get(FIREBASE_URL) as resp:
            data = await resp.json()
            if not data:
                return JSONResponse(content=[])
            sorted_data = sorted(data.values(), key=lambda x: x["epoch"])
            last_300 = sorted_data[-300:]
            return JSONResponse(content=last_300)
