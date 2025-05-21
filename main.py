from fastapi import FastAPI
from analyzer.analyzer import Analyzer
from notifier import send_signal_to_telegram
import asyncio
import requests

# Your public Firebase Realtime DB URL
FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/Vix25.json"

app = FastAPI()
analyzer = Analyzer()

@app.on_event("startup")
async def start_stream():
    async def stream_loop():
        last_processed = None
        while True:
            try:
                response = requests.get(FIREBASE_URL)
                data = response.json()
                if data:
                    # Get the last item based on sorted keys
                    last_key = sorted(data.keys())[-1]
                    if last_key != last_processed:
                        last_processed = last_key
                        tick = data[last_key]
                        price = float(tick["quote"])
                        timestamp = int(tick["epoch"])
                        signal = analyzer.update(price, timestamp)
                        if signal:
                            send_signal_to_telegram(signal)
            except Exception as e:
                print("Error:", e)
            await asyncio.sleep(1)

    asyncio.create_task(stream_loop())

@app.get("/")
def home():
    return {"status": "running"}
