from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://vix75-f6684-default-rtdb.firebaseio.com/"
TICK_PATH = "ticks/R_25.json"

async def fetch_ticks():
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL + TICK_PATH)
        if res.status_code == 200:
            raw = res.json()
            if not raw:
                return []
            # Sort ticks by epoch ascending
            ticks = sorted(
                [{"time": v["epoch"], "price": v["quote"]} for v in raw.values()],
                key=lambda x: x["time"]
            )
            # Return last 300 ticks
            return ticks[-300:]
        return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            ticks = await fetch_ticks()
            if ticks:
                await websocket.send_json({"ticks": ticks})
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
