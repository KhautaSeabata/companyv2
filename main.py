from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import asyncio
import httpx
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return HTMLResponse("<h2>Choose a chart:</h2><ul>" +
                        "<li><a href='/vix10'>Vix10</a></li>" +
                        "<li><a href='/vix25'>Vix25</a></li>" +
                        "<li><a href='/vix75'>Vix75</a></li>" +
                        "<li><a href='/vix100'>Vix100</a></li></ul>")

@app.get("/vix10")
async def vix10():
    return FileResponse("static/chart.html")

@app.get("/vix25")
async def vix25():
    return FileResponse("static/chart.html")

@app.get("/vix75")
async def vix75():
    return FileResponse("static/chart.html")

@app.get("/vix100")
async def vix100():
    return FileResponse("static/chart.html")

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com"

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)

manager = ConnectionManager()

async def get_latest_tick(symbol: str):
    async with httpx.AsyncClient() as client:
        url = f"{FIREBASE_URL}/{symbol}.json"
        resp = await client.get(url)
        data = resp.json()
        if not data:
            return None
        return max(data.values(), key=lambda x: x["timestamp"])

@app.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket)
    try:
        while True:
            tick = await get_latest_tick(symbol)
            if tick:
                message = {
                    "symbol": symbol,
                    "tick": {
                        "quote": tick["price"],
                        "epoch": tick["timestamp"],
                        "time": tick["time"],
                    }
                }
                await manager.send_message(websocket, json.dumps(message))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
