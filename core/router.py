import os
import ccxt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router")

EXCH_EXEC = os.getenv("EXCH_EXEC", "bybit,binance,kucoin").split(",")
ACTIVE_EXCHANGE = os.getenv("ACTIVE_EXCHANGE", "bybit")

def choose_exchange(symbol="BTC/USDT"):
    for exch_name in EXCH_EXEC:
        try:
            exch = getattr(ccxt, exch_name)({"enableRateLimit": True})
            markets = exch.load_markets()
            if symbol in markets:
                logger.info(f"Selected exchange: {exch_name}")
                return exch_name
        except Exception as e:
            logger.warning(f"Exchange {exch_name} failed: {e}")
    return ACTIVE_EXCHANGE
