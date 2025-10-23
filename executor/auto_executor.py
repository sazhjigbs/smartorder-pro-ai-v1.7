#!/usr/bin/env python3
# ===============================================================
# ✅ SAFELOGIC SMARTORDER PRO AI v1.8 — AUTO EXECUTOR (Bybit V5 Official)
# ===============================================================
import os, json, time, random
from loguru import logger
from pybit.unified_trading import HTTP

LOG_PATH = "/opt/smartorder/logs/auto_executor.log"
MEM_PATH = "/opt/smartorder/db/market_memory.json"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger.add(LOG_PATH, rotation="2 MB", level="INFO")

def get_bias():
    try:
        if os.path.exists(MEM_PATH):
            with open(MEM_PATH, "r") as f:
                data = json.load(f)
                bias, trend = data.get("bias", "neutral"), data.get("trend", "flat")
                logger.info(f"🧠 FusionEngine → Bias: {bias} | Trend: {trend}")
                return bias, trend
    except Exception as e:
        logger.error(f"Erreur lecture mémoire : {e}")
    return "neutral", "flat"

def place_order(symbol="BTCUSDT", side="Buy", qty="0.001"):
    try:
        session = HTTP(
            api_key=os.getenv("BYBIT_API_KEY", ""),
            api_secret=os.getenv("BYBIT_API_SECRET", ""),
            testnet=False,
        )

        params = {
            "category": "linear",              # Futures USDT Perp
            "symbol": symbol,
            "side": side,                      # "Buy" ou "Sell"
            "orderType": "Market",
            "qty": qty,
            "timeInForce": "GoodTillCancel",
            "orderLinkId": f"smartorder_{int(time.time() * 1000)}",
            "reduceOnly": False,
            "closeOnTrigger": False,
        }

        logger.info(f"➡️ Sending order: {params}")
        res = session.place_order(**params)
        logger.info(f"⬅️ Response: {res}")

        if res.get("retCode") == 0:
            logger.success(f"✅ Order {side} executed successfully ✅")
        else:
            logger.warning(f"⚠️ Bybit error: {res.get('retMsg')}")

    except Exception as e:
        logger.error(f"❌ Exception: {e}")

def main():
    logger.info("=== START AUTO-EXECUTOR (BYBIT V5 OFFICIAL SDK) ===")
    bias, trend = get_bias()
    if bias == "bullish" and trend == "trend":
        side = "Buy"
    elif bias == "bearish" and trend == "trend":
        side = "Sell"
    else:
        side = random.choice(["Buy", "Sell"])
    logger.info(f"💡 Signal: {side.upper()} @ BTCUSDT")
    place_order("BTCUSDT", side, "0.001")

if __name__ == "__main__":
    main()
