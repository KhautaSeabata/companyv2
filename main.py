from fastapi import FastAPI
from analyzer.analyzer import Analyzer
from notifier import send_signal_to_telegram
import asyncio
import firebase_admin
from firebase_admin import db, credentials

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://data-364f1-default-rtdb.firebaseio.com/"
})

app = FastAPI()
analyzer = Analyzer()

@app.on_event("startup")
async def start_stream():
    async def stream_loop():
        ref = db.reference("ticks/Vix25")
        last_processed = None
        while True:
            snapshot = ref.order_by_key().limit_to_last(1).get()
            if snapshot:
                for key, data in snapshot.items():
                    if key != last_processed:
                        last_processed = key
                        price = float(data["quote"])
                        timestamp = int(data["epoch"])
                        signal = analyzer.update(price, timestamp)
                        if signal:
                            send_signal_to_telegram(signal)
            await asyncio.sleep(1)

    asyncio.create_task(stream_loop())

@app.get("/")
def home():
    return {"status": "running"}
