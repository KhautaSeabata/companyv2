from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import aiohttp

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.websocket("/ws/vix75")
async def vix75_socket(websocket: WebSocket):
    await websocket.accept()

    url = "https://data-364f1-default-rtdb.firebaseio.com/vix75.json"

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
                    if not data:
                        await asyncio.sleep(1)
                        continue

                    # Get the latest tick
                    latest_key = sorted(data.keys())[-1]
                    tick = data[latest_key]

                    await websocket.send_json({"tick": tick})

            except Exception as e:
                print("WebSocket error:", e)
                break

            await asyncio.sleep(1)

