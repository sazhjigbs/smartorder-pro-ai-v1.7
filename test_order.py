#!/usr/bin/env python3
from pybit.usdt_perpetual import HTTP
import os, time, json

print("=== 🔍 TEST BYBIT ORDER (pybit v2.4.1 compatible Python 3.8) ===")

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

if not api_key or not api_secret:
    print("❌ Clés API Bybit non trouvées dans .env — charge-les d'abord.")
    exit(1)

session = HTTP(endpoint="https://api.bybit.com", api_key=api_key, api_secret=api_secret)

try:
    result = session.place_active_order(
        symbol="BTCUSDT",
        side="Buy",
        order_type="Market",
        qty=0.001,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        close_on_trigger=False
    )
    print("=== ✅ Réponse Bybit ===")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"❌ Erreur API : {e}")
