import requests, time, threading
CACHE = {"pnl":{}, "last_update":None}

def pnl_percent(type_, entry, last, leverage=1):
    if type_.upper() == "LONG":
        return round(((last-entry)/entry)*100*leverage,2)
    else:
        return round(((entry-last)/entry)*100*leverage,2)

def _loop():
    while True:
        try:
            data = requests.get("https://api.bybit.com/v5/market/tickers?category=linear", timeout=3).json()
            d = {i["symbol"]:float(i["lastPrice"]) for i in data["result"]["list"]}
            CACHE["pnl"]["BTCUSDT"] = pnl_percent("LONG", 68430, d.get("BTCUSDT", 68430))
            CACHE["pnl"]["ETHUSDT"] = pnl_percent("SHORT", 2458, d.get("ETHUSDT", 2458))
            CACHE["last_update"] = time.strftime("%H:%M:%S")
        except Exception as e:
            CACHE["error"] = str(e)
        time.sleep(5)

def start(): threading.Thread(target=_loop, daemon=True).start()
def get(): return CACHE
