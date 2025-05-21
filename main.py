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
        while True:
            try:
                # Connect to Deriv WebSocket API
                async with websockets.connect("wss://ws.deriv.com/websockets/v3?app_id=1089") as deriv_ws:
                    await deriv_ws.send(json.dumps({
                        "ticks": index,
                        "subscribe": 1
                    }))

                    while True:
                        msg = await deriv_ws.recv()
                        data = json.loads(msg)

                        # Send to frontend only if tick data exists
                        if "tick" in data:
                            await websocket.send_json(data)

            except (websockets.ConnectionClosed, websockets.WebSocketException, asyncio.TimeoutError) as e:
                print(f"[Deriv WS Error] {e}, reconnecting in 3s...")
                await asyncio.sleep(3)  # Wait and reconnect

    except WebSocketDisconnect:
        print(f"Client disconnected from index: {index}")
    except Exception as e:
        print(f"[App Error] {e}")
        await websocket.close()

# Run locally or on Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
