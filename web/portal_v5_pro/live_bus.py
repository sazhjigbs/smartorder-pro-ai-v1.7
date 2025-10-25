import asyncio, json, psutil, datetime, os
from fastapi import WebSocket
import aiofiles

async def stream_logs(websocket: WebSocket, path="/opt/smartorder/logs/bybitbot.log"):
    await websocket.accept()
    try:
        while True:
            if os.path.exists(path):
                async with aiofiles.open(path, mode='r') as f:
                    lines = await f.readlines()
                    tail = ''.join(lines[-20:])
                    await websocket.send_text(json.dumps({"logs": tail}))
            await asyncio.sleep(2)
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()
