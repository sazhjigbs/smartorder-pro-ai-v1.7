#!/usr/bin/env python3
import json, os, time, datetime, random

MEMORY_PATH = "/opt/smartorder/db/market_memory.json"
LOG_PATH = "/opt/smartorder/logs/market_learner.log"

def log(msg):
    ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(f"{ts} {msg}\n")

def load_memory():
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    return {"bias": "neutral", "volatility": 0.0, "trend": "flat"}

def save_memory(mem):
    with open(MEMORY_PATH, "w") as f:
        json.dump(mem, f, indent=2)

def analyze_market():
    bias = random.choice(["bullish", "bearish", "neutral"])
    vol = round(random.uniform(0.5, 3.5), 2)
    trend = "trend" if vol > 2 else "range" if vol < 1 else "flat"
    return {"bias": bias, "volatility": vol, "trend": trend}

def main():
    while True:
        memory = analyze_market()
        save_memory(memory)
        log(f"🧠 MarketMemory updated → {memory}")
        time.sleep(1800)  # update toutes les 30 min

if __name__ == "__main__":
    main()
