from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from analyzer.analyzer import Analyzer  # your analyzer module
import asyncio
import httpx
import uuid

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase base paths
BASE_URL = "https://vix75-f6684-default-rtdb.firebaseio.com/"
TICK_PATH = "ticks/R_25.json"
SIGNAL_PATH = "signals/R_25"

# Initialize analyzer
analyzer = Analyzer()

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "FastAPI is running successfully!"}

# Generate a short signal ID
def generate_signal_id():
    return str(uuid.uuid4())[:8]

# Fetch recent tick data from Firebase
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

# Store a new signal to Firebase
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

# Fetch all active signals from Firebase
async def fetch_active_signals():
    url = f"{BASE_URL}{SIGNAL_PATH}.json"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code == 200 and res.json():
            return {k: v for k, v in res.json().items() if v.get("status") == "active"}
    return {}

# Update the status of a signal (e.g., to 'complete')
async def update_signal_status(signal_id, status):
    url = f"{BASE_URL}{SIGNAL_PATH}/{signal_id}/status.json"
    async with httpx.AsyncClient() as client:
        await client.put(url, json=status)

# WebSocket endpoint for real-time charting and signals
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

            # Send tick data to frontend
            await websocket.send_json({"ticks": ticks})
            latest_price = ticks[-1]["price"]

            # Check active signals
            active_signals = await fetch_active_signals()
            to_display = []

            for sig_id, sig in active_signals.items():
                sl = sig.get("sl")
                tp = sig.get("tp")
                entry = sig.get("entry")
                entry_time = sig.get("entry_time")

                # If SL or TP is hit, mark signal as complete
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

            # Send current active signals to frontend
            await websocket.send_json({"signals": to_display})

            # Run analyzer to detect new signals
            signal = analyzer.detect(ticks)
            if signal and (last_signal_time is None or signal["time"] != last_signal_time):
                last_signal_time = signal["time"]
                await store_signal(signal)

            await asyncio.sleep(1)

    except Exception as e:
        print("WebSocket disconnected:", e)
