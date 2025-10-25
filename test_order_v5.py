from pybit.unified_trading import HTTP
import os, json, time

print("=== 🔍 TEST BYBIT ORDER (pybit V5 HMAC) ===")

session = HTTP(
    api_key=os.getenv("BYBIT_API_KEY"),
    api_secret=os.getenv("BYBIT_API_SECRET"),
    testnet=False
)

resp = session.place_order(
    category="linear",
    symbol="BTCUSDT",
    side="Buy",
    orderType="Market",
    qty="0.001",
    timeInForce="GoodTillCancel",
    orderLinkId=f"smartorder_{int(time.time()*1000)}"
)

print(json.dumps(resp, indent=2))
