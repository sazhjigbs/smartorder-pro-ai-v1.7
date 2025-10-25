import random, time, threading
CACHE = {"trust":{}, "last_update":None}

def _loop():
    while True:
        try:
            CACHE["trust"]["BTCUSDT"] = round(random.uniform(75, 90), 1)
            CACHE["trust"]["ETHUSDT"] = round(random.uniform(65, 80), 1)
            CACHE["last_update"] = time.strftime("%H:%M:%S")
        except Exception as e:
            CACHE["error"] = str(e)
        time.sleep(10)

def start(): threading.Thread(target=_loop, daemon=True).start()
def get(): return CACHE
