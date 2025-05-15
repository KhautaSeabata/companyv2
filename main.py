import os
import asyncio
import time
import json
from fastapi import FastAPI, WebSocket, Request
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

# WebSocket endpoint to stream live tick data
@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    deriv_url = "wss://ws.deriv.com/websockets/v3?app_id=1089"

    try:
        async with websockets.connect(deriv_url) as deriv_ws:
            # Subscribe to live ticks for the given index (e.g., R_75)
            await deriv_ws.send(json.dumps({
                "ticks": index,
                "subscribe": 1
            }))

            while True:
                response = await deriv_ws.recv()
                data = json.loads(response)

                # Forward tick data to frontend
                if "tick" in data:
                    await websocket.send_json(data)
    except Exception as e:
        print("WebSocket connection error:", e)
        await websocket.close()

# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
