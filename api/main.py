from fastapi import FastAPI
from pydantic import BaseModel
from trade_api import router_trade
import os

app = FastAPI(title="SAFELOGIC SmartOrder Pro API", version="1.0")
app.include_router(router_trade, prefix="/trade", tags=["Trading"])

class Status(BaseModel):
    phase: str
    status: str
    bias: str
    trend: str
    volatility: float
    pnl: float
    time_updated: str

@app.get("/")
def root():
    return {"status": "✅ API SmartOrder Pro opérationnelle", "env": os.getcwd()}

@app.get("/status", response_model=Status)
def get_status():
    return {
        "phase": "Phase 4 – AutoExec Live",
        "status": "running",
        "bias": "neutral",
        "trend": "flat",
        "volatility": 1.77,
        "pnl": 0.0,
        "time_updated": "2025-10-23"
    }
