import asyncio, json
from aiohttp import web

STATUS = {"phase": "10 – MTF Sync Live Dashboard", "status": "running",
          "bias": "neutral", "trend": "flat", "volatility": 0.0, "pnl": 0.0}

async def update_data():
    while True:
        try:
            with open("/opt/smartorder/db/market_memory.json", "r") as f:
                STATUS.update(json.load(f))
        except Exception:
            pass
        await asyncio.sleep(5)

async def http_status(request):
    return web.json_response(STATUS)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    try:
        while True:
            await ws.send_str(json.dumps(STATUS))
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass
    return ws

async def start_app():
    app = web.Application()
    app.add_routes([web.get("/", http_status), web.get("/ws", websocket_handler)])
    asyncio.create_task(update_data())
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8088)
    await site.start()
    print("🧠 SAFELOGIC MTF Sync Dashboard stable sur port 8088")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(start_app())
