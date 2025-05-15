import asyncio
from aiohttp import web

# Handler for normal HTTP requests (GET, HEAD)
async def http_handler(request):
    return web.Response(text="Hello, this is HTTP!")

# Handler for WebSocket connections on /ws
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    print("WebSocket connection opened")

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            print(f"Received message: {msg.data}")
            # Echo back or process the message
            await ws.send_str(f"Echo: {msg.data}")
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket connection closed with exception {ws.exception()}")

    print("WebSocket connection closed")
    return ws

async def on_startup(app):
    print("Server is starting...")

async def on_shutdown(app):
    print("Server is shutting down...")

def main():
    app = web.Application()
    
    # Routes
    app.router.add_get('/', http_handler)
    app.router.add_head('/', http_handler)  # Handle HEAD requests properly
    app.router.add_get('/ws', websocket_handler)  # WebSocket endpoint

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, port=8765)

if __name__ == "__main__":
    main()
