from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import httpx
import asyncio
from analyzer.analyzer import Analyzer  # your analyzer module

app = FastAPI()

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect root to index.html
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# Firebase DB URLs
BASE_URL = "https://vix75-f6684-default-rtdb.firebaseio.com/"
TICK_PATH = "ticks/R_25.json"

analyzer = Analyzer()

async def fetch_ticks():
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL + TICK_PATH)
        if res.status_code == 200:
            raw = res.json()
            if not raw:
                return []
            ticks = sorted(
                [{"time": v["epoch"], "price": v["quote"]} for v in raw.values()],
                key=lambda x: x["time"]
            )
            return ticks[-300:]  # last 300 ticks
        return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_signal_time = None

    try:
        while True:
            ticks = await fetch_ticks()
            if not ticks:
                await asyncio.sleep(1)
                continue

            # Run analyzer on ticks for signal detection
            signal = analyzer.detect(ticks)

            # Only send signal if new or changed
            send_signal = None
            if signal and (last_signal_time is None or signal["time"] != last_signal_time):
                last_signal_time = signal["time"]
                send_signal = {
                    "pattern": signal.get("pattern", "Unknown"),
                    "entry": signal["entry"],
                    "tp": signal["tp"],
                    "sl": signal["sl"],
                    "time": signal["time"],
                    "status": "Active",
                }

            # Send ticks and signal (if any) to client
            payload = {"ticks": ticks}
            if send_signal:
                payload["signal"] = send_signal

            await websocket.send_json(payload)

            await asyncio.sleep(1)

    except Exception as e:
        print(f"WebSocket disconnected: {e}")
