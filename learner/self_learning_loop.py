#!/usr/bin/env python3
# =============================================================
# 🤖 SMARTORDER PRO — SELF LEARNING LOOP
# Phase 5 → AI Feedback & Adaptive Bias Weighting
# =============================================================
import os, json, time, random
from datetime import datetime
from loguru import logger

LOG_PATH = "/opt/smartorder/logs/self_learning.log"
MEMORY_PATH = "/opt/smartorder/db/market_memory.json"
FEEDBACK_PATH = "/opt/smartorder/db/ai_feedback.json"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger.add(LOG_PATH, rotation="1 MB")

def simulate_pnl():
    # 🧩 Simulation PnL (à remplacer plus tard par la lecture réelle de l'API Bybit)
    return round(random.uniform(-2.0, 2.0), 2)

def adjust_bias(bias, pnl):
    if pnl > 0.5:
        if bias == "bullish": weight = "↑"
        elif bias == "bearish": weight = "↓"
        else: weight = "→"
    elif pnl < -0.5:
        if bias == "bullish": weight = "↓"
        elif bias == "bearish": weight = "↑"
        else: weight = "→"
    else:
        weight = "→"
    return weight

def main():
    logger.info("=== 🤖 Self-Learning Loop actif ===")
    while True:
        if not os.path.exists(MEMORY_PATH):
            time.sleep(15)
            continue
        with open(MEMORY_PATH) as f:
            memory = json.load(f)

        bias = memory.get("bias", "neutral")
        pnl = simulate_pnl()
        adjustment = adjust_bias(bias, pnl)

        feedback = {
            "time": datetime.now().isoformat(),
            "bias": bias,
            "pnl": pnl,
            "adjustment": adjustment
        }

        with open(FEEDBACK_PATH, "w") as f:
            json.dump(feedback, f, indent=2)

        logger.info(f"Feedback enregistré → {feedback}")
        time.sleep(60)

if __name__ == "__main__":
    main()
