from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from analyzer.analyzer import Analyzer  # Make sure it has a detect(ticks) method
import asyncio
import aiohttp
import datetime
import firebase_admin
from firebase_admin import db, credentials

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# Firebase setup
cred = credentials.Certificate("firebase-admin.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://data-364f1-default-rtdb.firebaseio.com/"
})

analyzer = Analyzer()
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        ref = db.reference("ticks/Vix75")
        last_signal_time = None

        while True:
            ticks = ref.order_by_key().limit_to_last(200).get()
            if ticks:
                tick_list = [{"time": int(k), "price": v} for k, v in ticks.items()]
                tick_list.sort(key=lambda x: x["time"])
                await websocket.send_json({"ticks": tick_list})

                # Detect pattern
                signal = analyzer.detect(tick_list)
                if signal and (not last_signal_time or signal["time"] != last_signal_time):
                    last_signal_time = signal["time"]

                    # Store signal in Firebase
                    db.reference("signals/Vix75").push(signal)

                    # Send signal to frontend
                    await websocket.send_json({"signal": signal})
            await asyncio.sleep(1)

    except Exception as e:
        print("WebSocket error:", e)
    finally:
        clients.remove(websocket)
