import os, time, json, psutil
from fastapi import FastAPI
from pydantic import BaseModel
from ai_core.ai_memory import AIMemory
from fastapi.responses import JSONResponse

APP_DIR = os.environ.get("APP_DIR", "/opt/smartorder-pro")
AI_DIR  = os.environ.get("AI_DIR", f"{APP_DIR}/ai_core")
MEM_PATH = os.environ.get("AI_MEMORY_PATH", f"{AI_DIR}/ai_memory.json")
LOCKFILE = os.environ.get("AI_PAUSE_LOCK", f"{AI_DIR}/PAUSED.lock")

app = FastAPI(title="SMARTORDER AI API", version="2.0")

class ActionResp(BaseModel):
    ok: bool
    paused: bool
    msg: str

@app.get("/health")
def health():
    return {"ok": True, "ver": "ai-api-2.0", "cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent, "time": time.time()}

@app.get("/ai/status")
def ai_status():
    mem = AIMemory(MEM_PATH).get()
    return {"ok": True, "paused": os.path.exists(LOCKFILE), "memory": mem}

@app.post("/ai/pause", response_model=ActionResp)
def ai_pause():
    if not os.path.exists(LOCKFILE):
        open(LOCKFILE, "w").close()
        return ActionResp(ok=True, paused=True, msg="Paused")
    return ActionResp(ok=True, paused=True, msg="Already paused")

@app.post("/ai/resume", response_model=ActionResp)
def ai_resume():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        return ActionResp(ok=True, paused=False, msg="Resumed")
    return ActionResp(ok=True, paused=False, msg="Already running")
