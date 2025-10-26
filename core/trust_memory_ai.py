import time, threading
try:
    from ai.signal_memory import get_trust_score
except ImportError:
    def get_trust_score(symbol, timeframe=None, last_n=50):
        return {"trust_score": 75.0, "status": "fallback"}

CACHE = {"trust":{}, "last_update":None}

def _loop():
    """Loop mise à jour trust scores depuis SQLite"""
    while True:
        try:
            # Fetch trust scores from DB
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
            
            for symbol in symbols:
                trust_data = get_trust_score(symbol, None, 50)
                CACHE["trust"][symbol] = trust_data.get("trust_score", 50.0)
            
            CACHE["last_update"] = time.strftime("%H:%M:%S")
        except Exception as e:
            CACHE["error"] = str(e)
        time.sleep(30)  # Update every 30s

def start(): threading.Thread(target=_loop, daemon=True).start()
def get(): return CACHE
