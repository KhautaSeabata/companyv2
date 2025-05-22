# main.py
import asyncio
import websockets
import json
import requests
import time

FIREBASE_URL = "https://company-bdb78-default-rtdb.firebaseio.com"
DERIV_WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
SYMBOL = "R_25"
MAX_RECORDS = 999

def push_tick(tick_data):
    url = f"{FIREBASE_URL}/ticks/{SYMBOL}.json"
    response = requests.post(url, json=tick_data)
    print("[TICK PUSHED]", tick_data if response.status_code == 200 else response.text)

def trim_old_ticks():
    url = f"{FIREBASE_URL}/ticks/{SYMBOL}.json?orderBy=\"epoch\"&limitToLast={MAX_RECORDS}"
    res = requests.get(url)
    if res.status_code == 200 and res.json():
        ticks = res.json()
        keep_keys = set(ticks.keys())
        all_url = f"{FIREBASE_URL}/ticks/{SYMBOL}.json"
        full_res = requests.get(all_url)
        if full_res.status_code == 200 and full_res.json():
            for k in full_res.json():
                if k not in keep_keys:
                    del_url = f"{FIREBASE_URL}/ticks/{SYMBOL}/{k}.json"
                    requests.delete(del_url)
                    print("[DELETED OLD TICK]", k)

async def stream_ticks():
    while True:
        try:
            async with websockets.connect(DERIV_WS_URL) as ws:
                await ws.send(json.dumps({
                    "ticks": SYMBOL,
                    "subscribe": 1
                }))
                print("[STARTED] Subscribed to ticks")

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    if "tick" in data:
                        tick = {
                            "symbol": data["tick"]["symbol"],
                            "epoch": data["tick"]["epoch"],
                            "quote": data["tick"]["quote"]
                        }

                        push_tick(tick)
                        trim_old_ticks()
        except Exception as e:
            print("[ERROR]", e)
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(stream_ticks())
