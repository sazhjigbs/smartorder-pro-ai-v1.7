from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn, os, json, datetime
from loguru import logger

LOG_PATH = "/opt/smartorder/logs/dashboard.log"
logger.add(LOG_PATH, rotation="1 MB")

app = FastAPI(title="SAFELOGIC AI Dashboard", version="1.8-FINAL")

@app.get("/")
def root():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "status": "running",
        "time": now,
        "phase": "9 – AI Live Dashboard",
        "fusion_bias": os.getenv("AI_BIAS", "neutral"),
        "trend": os.getenv("AI_TREND", "flat"),
        "volatility": os.getenv("AI_VOL", "1.7")
    }
    logger.info(f"📊 Dashboard ping @ {now}")
    return JSONResponse(data)

if __name__ == "__main__":
    logger.info("🖥️ SAFELOGIC Dashboard Live lancé sur port 8088")
    uvicorn.run(app, host="0.0.0.0", port=8088)
