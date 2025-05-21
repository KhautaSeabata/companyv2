import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

app = FastAPI()

# Serve static files from /static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
async def get_index(request: Request):
    if request.method == "HEAD":
        return ""
    return FileResponse("static/index.html")

@app.get("/api/ticks")
async def get_latest_ticks():
    # Replace this URL with your actual Firebase Realtime Database ticks node URL
    firebase_url = (
        "https://your-project-id.firebaseio.com/ticks.json"
        "?orderBy=\"epoch\"&limitToLast=300"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(firebase_url)
        response.raise_for_status()
        data = response.json()

    # Firebase returns a dict of ticks keyed by their unique id
    ticks = list(data.values()) if data else []

    # Sort ascending by epoch (oldest first)
    ticks.sort(key=lambda x: x.get("epoch", 0))

    return ticks

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
