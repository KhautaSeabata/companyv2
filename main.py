from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.websocket("/ws/vix25")
async def vix25_websocket(websocket: WebSocket):
    await websocket.accept()
    firebase_url = "https://data-364f1-default-rtdb.firebaseio.com/vix25.json"

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(firebase_url) as resp:
                    data = await resp.json()
                    if not data:
                        continue
                    latest_key = sorted(data.keys())[-1]
                    tick = data[latest_key]  # expects {"epoch": ..., "quote": ...}
                    await websocket.send_json(tick)
            except Exception as e:
                await websocket.close()
                break
            await asyncio.sleep(1)  # poll every 1 second

