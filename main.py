import os
import asyncio
import time
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve static files like index.html and style.css
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the HTML file at root
@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

# WebSocket endpoint
@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    try:
        while True:
            # Simulate price ticks (replace with real logic)
            await websocket.send_json({
                "tick": {
                    "epoch": int(time.time()),
                    "quote": 123.45  # Replace with real-time quote
                }
            })
            await asyncio.sleep(1)
    except Exception as e:
        print("WebSocket closed:", e)
