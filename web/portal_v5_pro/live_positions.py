import asyncio, json, requests, datetime
from fastapi import WebSocket

async def stream_positions(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = {}
            try:
                core = requests.get("http://127.0.0.1:8091/status", timeout=3).json()
                data["exchange"] = core.get("exchange","—")
                data["auto_mode"] = core.get("auto_mode", False)
                data["cpu"] = core.get("cpu",0)
                data["mem"] = core.get("mem",0)
                data["time"] = core.get("time", "")
            except Exception:
                data = {"exchange":"offline","auto_mode":False,"time":str(datetime.datetime.now())}
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(2)
    except Exception as e:
        await websocket.send_text(json.dumps({"error":str(e)}))
        await websocket.close()
