#!/usr/bin/env python3
import os, time, json, hmac, hashlib, requests

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

url = "https://api.bybit.com/v5/order/create"
timestamp = str(int(time.time() * 1000))

body = {
    "category": "linear",
    "symbol": "BTCUSDT",
    "side": "Buy",
    "orderType": "Market",
    "qty": "0.001",
    "timeInForce": "GoodTillCancel",
    "orderLinkId": f"smartorder_{timestamp}"
}

# ✅ Tri alphabétique + signature correcte (Bybit V5)
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

print("=== 🔍 TEST BYBIT ORDER HMAC V5 (Python 3.8 – FIX SIGNATURE) ===")
resp = requests.post(url, headers=headers, data=body_json)
print(json.dumps(resp.json(), indent=2))
