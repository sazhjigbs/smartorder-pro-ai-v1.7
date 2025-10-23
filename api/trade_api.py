from fastapi import APIRouter
from core.router import choose_exchange

router_trade = APIRouter()

@router_trade.get("/trade/simulate")
def trade_simulate(symbol: str = "BTC/USDT", side: str = "buy", qty: float = 0.001):
    exch = choose_exchange(symbol)
    return {
        "exchange": exch,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "status": "simulated",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
