import os
import asyncio
import signal
import http
import websockets

async def echo(ws):
    async for msg in ws:
        await ws.send(msg)

async def health_check(path, request_headers):
    # Return 200 OK for /healthz so Render’s health check passes
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"

async def main():
    port = int(os.environ.get("PORT", 8765))          # Use $PORT, default 8765 for local dev
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None) 
    # Serve on all interfaces (0.0.0.0) at the given port
    async with websockets.serve(
        echo,
        host="0.0.0.0",
        port=port,
        process_request=health_check,               # health check on /healthz
    ):
        print(f"WebSocket server listening on port {port}")
        await stop

if __name__ == "__main__":
    asyncio.run(main())
