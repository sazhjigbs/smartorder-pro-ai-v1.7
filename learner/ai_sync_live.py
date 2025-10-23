#!/usr/bin/env python3
# =============================================================
# 🧠 SMARTORDER PRO — AI MEMORY SYNC LIVE
# Phase 6 → Self-Learning Integration with MarketMemory
# =============================================================
import os, json, time
from loguru import logger

LOG_PATH = "/opt/smartorder/logs/ai_sync_live.log"
MEMORY_PATH = "/opt/smartorder/db/market_memory.json"
FEEDBACK_PATH = "/opt/smartorder/db/ai_feedback.json"

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger.add(LOG_PATH, rotation="1 MB")

def main():
    logger.info("=== 🧩 AI Memory Sync Live démarré ===")
    while True:
        if not (os.path.exists(MEMORY_PATH) and os.path.exists(FEEDBACK_PATH)):
            time.sleep(10)
            continue

        with open(MEMORY_PATH) as f:
            memory = json.load(f)
        with open(FEEDBACK_PATH) as f:
            feedback = json.load(f)

        bias, adj = memory.get("bias"), feedback.get("adjustment")
        if adj == "↑" and bias != "bullish":
            memory["bias"] = "bullish"
        elif adj == "↓" and bias != "bearish":
            memory["bias"] = "bearish"
        elif adj == "→":
            pass

        memory["time_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(MEMORY_PATH, "w") as f:
            json.dump(memory, f, indent=2)
        logger.info(f"✅ Memory Sync Live → {memory}")
        time.sleep(60)

if __name__ == "__main__":
    main()
