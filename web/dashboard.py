from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests, os, json, asyncio

app = FastAPI(title="SAFELOGIC SmartOrder PRO v4-UI Pro")

app.mount("/static", StaticFiles(directory="/opt/smartorder/web/static"), name="static")
templates = Jinja2Templates(directory="/opt/smartorder/web/templates")

API_BASE = "http://127.0.0.1:8191"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        status = requests.get(f"{API_BASE}/status", timeout=2).json()
        positions = requests.get(f"{API_BASE}/positions", timeout=2).json()
    except Exception:
        status = {"status":"offline"}
        positions = []
    return templates.TemplateResponse("index.html", {"request": request, "status": status, "positions": positions})

@app.post("/set_exchange")
async def set_exchange(exchange: str = Form(...)):
    os.system(f"sed -i '/ACTIVE_EXCHANGE/d' /opt/smartorder/.env && echo ACTIVE_EXCHANGE={exchange} >> /opt/smartorder/.env")
    return JSONResponse({"exchange": exchange})

@app.get("/api/reload")
async def reload_system():
    os.system("systemctl restart smartorder-pro.service")
    return {"status":"restarting"}

@app.get("/api/telegram_sync")
async def telegram_sync():
    os.system("systemctl restart smartorder-telegram.service")
    return {"status":"telegram_sync_restarted"}
