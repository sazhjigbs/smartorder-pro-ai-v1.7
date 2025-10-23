import ccxt, json, os, time, random
from loguru import logger

EXCH_EXEC = os.getenv("EXCH_EXEC", "bybit,binance,kucoin").split(",")
ACTIVE_EXCHANGE = os.getenv("ACTIVE_EXCHANGE", "bybit")

CACHE_FILE = "/opt/smartorder/state_exchange.json"

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f: return json.load(f)
    except: return {}

def save_cache(data):
    with open(CACHE_FILE, "w") as f: json.dump(data, f, indent=2)

def choose_exchange(symbol="BTC/USDT"):
    for ex_name in EXCH_EXEC:
        try:
            ex_class = getattr(ccxt, ex_name)()
            mkts = ex_class.load_markets()
            if symbol in mkts:
                info = mkts[symbol]
                if "limits" in info and info["limits"]["cost"]["min"] < 10:
                    logger.info(f"✅ Route sélectionnée: {ex_name.upper()} — minNotional OK")
                    cache = load_cache()
                    cache["last_used"] = ex_name
                    save_cache(cache)
                    return ex_name
        except Exception as e:
            logger.warning(f"{ex_name} erreur: {e}")
    return ACTIVE_EXCHANGE
