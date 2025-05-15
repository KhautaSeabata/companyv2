import asyncio
import websockets
from analyzer import Analyzer
from datetime import datetime
import json

analyzer = Analyzer()

async def handler(websocket, path):
    index = path.strip("/").split("/")[-1]
    while True:
        quote = simulate_live_price()
        timestamp = int(datetime.utcnow().timestamp())

        tick_data = {'tick': {'quote': quote, 'epoch': timestamp}}
        signal_data = analyzer.update(quote, timestamp)

        if signal_data:
            tick_data['signal'] = signal_data

        await websocket.send(json.dumps(tick_data))
        await asyncio.sleep(1)

def simulate_live_price():
    from random import uniform
    return round(100 + uniform(-1, 1), 4)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8000):  # Use 0.0.0.0 in production
        print("WebSocket server started on port 8000")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
