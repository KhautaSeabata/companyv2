from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials, db
import asyncio
import json
import time

app = FastAPI()

# Serve static files (index.html, chart.js, etc)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Firebase setup
cred = credentials.Certificate("path/to/your/firebase-service-account.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://vix75-f6684-default-rtdb.firebaseio.com/"
})

# Reference to ticks R_25
ticks_ref = db.reference("ticks/R_25")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data):
        await websocket.send_text(json.dumps(data))

    async def broadcast(self, data):
        for connection in self.active_connections:
            await self.send_json(connection, data)

manager = ConnectionManager()

# Dummy analyzer function example (replace with your actual pattern detection logic)
def analyze_pattern(ticks):
    # For example, detect if last price increased sharply (dummy signal)
    if len(ticks) < 5:
        return None
    last = ticks[-1]["quote"]
    prev = ticks[-5]["quote"]
    if last > prev * 1.005:  # 0.5% increase in 5 ticks
        return {
            "pattern": "DummyUptrend",
            "entry": last,
            "tp": round(last * 1.01, 2),
            "sl": round(last * 0.995, 2),
            "time": ticks[-1]["epoch"],
            "status": "Active"
        }
    return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # On connect, send last 300 ticks snapshot once
        while True:
            all_ticks = ticks_ref.order_by_key().limit_to_last(300).get()
            if all_ticks:
                # all_ticks is dict {key: {epoch, quote, symbol}}
                # convert to list sorted by epoch ascending
                ticks_list = sorted(all_ticks.values(), key=lambda x: x["epoch"])
            else:
                ticks_list = []

            # Analyze pattern from current ticks
            signal = analyze_pattern(ticks_list)

            # Send ticks + signal to client
            await manager.send_json(websocket, {"ticks": ticks_list, "signal": signal})

            await asyncio.sleep(1)  # update every 1 sec
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
