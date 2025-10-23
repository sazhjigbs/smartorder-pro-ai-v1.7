from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json, os, requests

app = FastAPI(title="SAFELOGIC SmartOrder PRO Dashboard v4-UI Pro")

templates = Jinja2Templates(directory="/opt/smartorder/web/templates")
app.mount("/static", StaticFiles(directory="/opt/smartorder/web/static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status")
def status():
    try:
        r = requests.get("http://127.0.0.1:8191/status", timeout=2)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/trade/{mode}")
def trade(mode: str):
    return {"mode": mode, "action": "triggered"}
