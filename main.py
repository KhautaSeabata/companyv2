# main.py
import asyncio
import websockets
import json
import requests

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com"
DERIV_WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
SYMBOL = "R_25"  # Volatility 25 Index (change to R_10, R_75, etc.)

async def get_ticks():
    async with websockets.connect(DERIV_WS_URL) as ws:
        # Subscribe to ticks
        await ws.send(json.dumps({
            "ticks": SYMBOL,
            "subscribe": 1
        }))
        print(f"Subscribed to {SYMBOL} ticks...")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            if "tick" in data:
                tick = data["tick"]
                tick_data = {
                    "symbol": tick["symbol"],
                    "epoch": tick["epoch"],
                    "quote": tick["quote"]
                }

                # Push to Firebase
                firebase_url = f"{FIREBASE_URL}/ticks/{SYMBOL}.json"
                try:
                    response = requests.post(firebase_url, json=tick_data)
                    if response.status_code != 200:
                        print("Failed to push tick:", response.text)
                    else:
                        print("Tick pushed:", tick_data)
                except Exception as e:
                    print("Firebase error:", e)

if __name__ == "__main__":
    asyncio.run(get_ticks())
