from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from analyzer.analyzer import Analyzer
import asyncio
import httpx
import uuid

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect root URL to static index.html
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# Firebase settings
BASE_URL = "https://vix75-f6684-default-rtdb.firebaseio.com/"
TICK_PATH = "ticks/R_25.json"
SIGNAL_PATH = "signals/R_25"

analyzer = Analyzer()

def generate_signal_id():
    return str(uuid.uuid4())[:8]

async def fetch_ticks():
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL + TICK_PATH)
        if res.status_code == 200:
            raw = res.json()
            if not raw:
                return []
            return sorted(
                [{"time": v["epoch"], "price": v["quote"]} for v in raw.values()],
                key=lambda x: x["time"]
            )
        return []

async def store_signal(signal):
    signal_id = generate_signal_id()
    data = {
        "entry": signal["entry"],
        "tp": signal["tp"],
        "sl": signal["sl"],
        "status": "active",
        "entry_time": signal["time"],
    }
    url = f"{BASE_URL}{SIGNAL_PATH}/{signal_id}.json"
    async with httpx.AsyncClient() as client:
        await client.put(url, json=data)

async def fetch_active_signals():
    url = f"{BASE_URL}{SIGNAL_PATH}.json"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code == 200 and res.json():
            return {k: v for k, v in res.json().items() if v.get("status") == "active"}
    return {}

async def update_signal_status(signal_id, status):
    url = f"{BASE_URL}{SIGNAL_PATH}/{signal_id}/status.json"
    async with httpx.AsyncClient() as client:
        await client.put(url, json=status)

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

            await websocket.send_json({"ticks": ticks})
            latest_price = ticks[-1]["price"]

            active_signals = await fetch_active_signals()
            to_display = []

            for sig_id, sig in active_signals.items():
                sl = sig.get("sl")
                tp = sig.get("tp")
                entry = sig.get("entry")
                entry_time = sig.get("entry_time")

                if sl is not None and latest_price <= sl:
                    await update_signal_status(sig_id, "complete")
                elif tp is not None and latest_price >= tp:
                    await update_signal_status(sig_id, "complete")
                else:
                    to_display.append({
                        "id": sig_id,
                        "entry": entry,
                        "tp": tp,
                        "sl": sl,
                        "entry_time": entry_time,
                    })

            await websocket.send_json({"signals": to_display})

            signal = analyzer.detect(ticks)
            if signal and (last_signal_time is None or signal["time"] != last_signal_time):
                last_signal_time = signal["time"]
                await store_signal(signal)

            await asyncio.sleep(1)

    except Exception as e:
        print("WebSocket disconnected:", e)
