#!/usr/bin/env python3
# =============================================================
# 🚀 SMARTORDER PRO — AUTO EXECUTOR (Bybit V5 HMAC FIXED LIVE)
# Phase 4.1 — Mainnet Execution Live & Stable
# =============================================================
import os, time, json, hmac, hashlib, requests
from loguru import logger

LOG_PATH = "/opt/smartorder/logs/auto_executor.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger.add(LOG_PATH, rotation="1 MB")

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
QTY = os.getenv("QTY", "0.001")

URL = "https://api.bybit.com/v5/order/create"

def sign_request(body):
    timestamp = str(int(time.time() * 1000))
    body_json = json.dumps(body, separators=(',', ':'), sort_keys=True)
    param_str = timestamp + API_KEY + "5000" + body_json
    sign = hmac.new(API_SECRET.encode(), param_str.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": sign,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }
    return headers, body_json

def place_order(side):
    body = {
        "category": "linear",
        "symbol": SYMBOL,
        "side": side,
        "orderType": "Market",
        "qty": QTY,
        "timeInForce": "GoodTillCancel",
        "orderLinkId": f"smartorder_{int(time.time()*1000)}"
    }
    headers, body_json = sign_request(body)
    resp = requests.post(URL, headers=headers, data=body_json)
    result = resp.json()
    logger.info(json.dumps(result, indent=2))
    if result.get("retCode") == 0:
        logger.info("✅ Ordre exécuté avec succès sur Bybit Mainnet.")
    else:
        logger.warning(f"⚠️ Erreur Bybit : {result.get('retMsg')}")
    return result

def main():
    logger.info("=== START AUTO-EXECUTOR (BYBIT V5 HMAC – LIVE) ===")
    bias_path = "/opt/smartorder/db/market_memory.json"

    try:
        data = json.load(open(bias_path))
        bias = data.get("bias", "neutral")
        trend = data.get("trend", "flat")
    except Exception:
        bias, trend = "neutral", "flat"

    logger.info(f"🧠 FusionEngine → Bias={bias} | Trend={trend}")

    if bias == "bullish":
        side = "Buy"
    elif bias == "bearish":
        side = "Sell"
    else:
        logger.info("⚖️ Aucun signal prioritaire — neutre.")
        return

    logger.info(f"💡 Signal exécuté : {side} @ {SYMBOL}")
    place_order(side)
    logger.info("🏁 Cycle d'exécution terminé.\n")

if __name__ == "__main__":
    main()
