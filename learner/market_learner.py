#!/usr/bin/env python3
# =============================================================
# 🧠 SMARTORDER PRO – MARKET LEARNER
# Phase 9 → Bias Sync Engine (AI Memory AutoFeed)
# =============================================================
import os, time, json, random
from datetime import datetime
from loguru import logger

LOG_PATH = "/opt/smartorder/logs/market_learner.log"
MEMORY_PATH = "/opt/smartorder/db/market_memory.json"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger.add(LOG_PATH, rotation="1 MB")

def generate_bias():
    # ⚙️ Simulation provisoire (en attendant MTF Analyzer live)
    options = ["bullish", "bearish", "neutral"]
    trend = random.choice(["trend", "range", "flat"])
    bias = random.choices(options, weights=[0.4, 0.4, 0.2])[0]
    vol = round(random.uniform(0.5, 2.5), 2)
    return {"bias": bias, "trend": trend, "volatility": vol, "time": datetime.now().isoformat()}

def save_memory(data):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)

def main():
    logger.info("=== 🧠 MarketLearner Sync actif ===")
    while True:
        data = generate_bias()
        save_memory(data)
        logger.info(f"MarketMemory updated → {data}")
        time.sleep(30)

if __name__ == "__main__":
    main()
