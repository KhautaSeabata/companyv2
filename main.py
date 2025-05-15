import os
import asyncio
import time
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve static files (e.g. index.html, style.css) under /static path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html on GET / and respond properly to HEAD /
@app.api_route("/", methods=["GET", "HEAD"])
async def get_index(request: Request):
    if request.method == "HEAD":
        # Return empty response for HEAD requests (status 200 OK)
        return ""
    # On GET, serve the index.html file
    return FileResponse("static/index.html")

# WebSocket endpoint for realtime data streaming
@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    try:
        while True:
            # Simulate price tick with current epoch time and fixed quote
            await websocket.send_json({
                "tick": {
                    "epoch": int(time.time()),
                    "quote": 123.45  # Replace with your real data source
                }
            })
            await asyncio.sleep(1)
    except Exception as e:
        print("WebSocket connection closed:", e)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
