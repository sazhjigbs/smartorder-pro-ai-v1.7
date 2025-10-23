from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="SAFELOGIC SmartOrder PRO API")

@app.get("/status")
def status():
    return {"status": "running", "phase": "4A", "exchange": "bybit"}

@app.get("/trade/simulate")
def simulate():
    return {"trade": "simulated", "symbol": "BTCUSDT", "mode": "paper"}
