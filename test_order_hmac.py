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

# création de la signature HMAC SHA256 :
param_str = timestamp + API_KEY + "5000" + json.dumps(body, separators=(',', ':'))
sign = hmac.new(API_SECRET.encode("utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()

headers = {
    "X-BAPI-API-KEY": API_KEY,
    "X-BAPI-SIGN": sign,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": "5000",
    "Content-Type": "application/json"
}

print("=== 🔍 TEST BYBIT ORDER HMAC V5 (Python 3.8) ===")
resp = requests.post(url, headers=headers, data=json.dumps(body))
print(json.dumps(resp.json(), indent=2))

