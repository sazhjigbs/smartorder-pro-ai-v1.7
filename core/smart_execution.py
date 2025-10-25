import time, random, threading
CACHE = {"executions":[], "status":"idle"}

def simulate_order(symbol, side, size):
    pnl = round(random.uniform(-1.5, 2.5), 2)
    entry = 68430 if symbol=="BTCUSDT" else 2458
    CACHE["executions"].append({
        "symbol": symbol, "side": side, "size": size,
        "entry": entry, "pnl": pnl,
        "time": time.strftime("%H:%M:%S")
    })
    CACHE["status"] = "ok"

def _loop():
    while True:
        time.sleep(15)
        if random.random()>0.7:
            simulate_order("BTCUSDT", random.choice(["LONG","SHORT"]), 0.001)
            simulate_order("ETHUSDT", random.choice(["LONG","SHORT"]), 0.005)

def start(): threading.Thread(target=_loop, daemon=True).start()
def get(): return CACHE
