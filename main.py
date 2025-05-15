import os
import asyncio
import time
import json
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import websockets

app = FastAPI()

# Serve static files (e.g., index.html, style.css)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html for GET and HEAD requests
@app.api_route("/", methods=["GET", "HEAD"])
async def get_index(request: Request):
    if request.method == "HEAD":
        return ""
    return FileResponse("static/index.html")

# WebSocket endpoint
@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    print(f"Client connected for index: {index}")
    try:
        async with websockets.connect('wss://ws.binaryws.com/websockets/v3?app_id=1089') as ws:
            await ws.send(json.dumps({"ticks": index}))
            while True:
                msg = await ws.recv()
                await websocket.send_text(msg)
    except Exception as e:
        print("[App Error]", e)
    finally:
        print("Connection closed")


# Run locally or on Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
