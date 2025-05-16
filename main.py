# main.py
import asyncio
import json
import requests
import sseclient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from analyze import Analyzer

app = FastAPI()

# Allow all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIREBASE_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks.json"


def listen_to_firebase():
    headers = {'Accept': 'text/event-stream'}
    params = {"print": "event"}
    response = requests.get(FIREBASE_URL, stream=True, headers=headers, params=params)
    return sseclient.SSEClient(response)


@app.websocket("/ws/{index_name}")
async def websocket_endpoint(websocket: WebSocket, index_name: str):
    await websocket.accept()
    seen_ids = set()
    analyzer = Analyzer()

    try:
        for event in listen_to_firebase():
            if event.event == 'put':
                data = json.loads(event.data)
                if not data.get('data'):
                    continue

                ticks_data = data["data"] if isinstance(data["data"], dict) else {}
                for tick_id, tick in ticks_data.items():
                    if tick_id in seen_ids:
                        continue
                    seen_ids.add(tick_id)

                    price = tick.get("price")
                    timestamp = tick.get("timestamp")

                    if price is None or timestamp is None:
                        continue

                    signal = analyzer.analyze(price, timestamp)

                    await websocket.send_json({
                        "tick": {
                            "quote": price,
                            "epoch": timestamp
                        },
                        "signal": signal
                    })

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print("Error in WebSocket or Firebase stream:", e)
