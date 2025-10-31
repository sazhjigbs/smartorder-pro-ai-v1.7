# === PATCH POUR ANALYTICS DASHBOARD ===
# À ajouter dans /opt/smartorder-pro/api/main.py

import json
from pathlib import Path

# PORTFOLIO (existe déjà, mais amélioré)
@app.get("/api/portfolio")
def get_portfolio():
    """Récupérer le portfolio paper trading"""
    try:
        paper_file = Path("/opt/smartorder-pro/data/paper_trading.json")
        if paper_file.exists():
            data = json.loads(paper_file.read_text())
            return {
                "balance": data.get("balance", 0),
                "positions": data.get("positions", {}),
                "total_pnl": sum([
                    (pos.get("unrealized_pnl", 0)) 
                    for pos in data.get("positions", {}).values()
                ]),
                "initial_balance": data.get("initial_balance", 10000.0)
            }
        return {"balance": 0, "positions": {}, "total_pnl": 0, "initial_balance": 10000}
    except Exception as e:
        return {"balance": 0, "positions": {}, "total_pnl": 0, "initial_balance": 10000, "error": str(e)}

# STATS (NOUVEAU)
@app.get("/api/stats")
def get_stats():
    """Statistiques complètes pour le dashboard analytics"""
    try:
        paper_file = Path("/opt/smartorder-pro/data/paper_trading.json")
        if not paper_file.exists():
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
                "avg_trade": 0,
                "active_positions": 0
            }
        
        data = json.loads(paper_file.read_text())
        trades = data.get("trades", [])
        positions = data.get("positions", {})
        
        # Calculer statistiques
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        pnls = [t.get("pnl", 0) for t in trades if "pnl" in t]
        total_pnl = sum(pnls)
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0
        avg_trade = (total_pnl / len(pnls)) if pnls else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "best_trade": round(best_trade, 2),
            "worst_trade": round(worst_trade, 2),
            "avg_trade": round(avg_trade, 2),
            "active_positions": len(positions),
            "balance": data.get("balance", 0),
            "initial_balance": data.get("initial_balance", 10000)
        }
    except Exception as e:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "avg_trade": 0,
            "active_positions": 0,
            "error": str(e)
        }

# TRADES (NOUVEAU)
@app.get("/api/trades")
def get_trades(limit: int = 50):
    """Historique des trades pour analytics"""
    try:
        paper_file = Path("/opt/smartorder-pro/data/paper_trading.json")
        if not paper_file.exists():
            return []
        
        data = json.loads(paper_file.read_text())
        trades = data.get("trades", [])
        
        # Retourner les N derniers trades
        return trades[-limit:] if len(trades) > limit else trades
    except Exception as e:
        return []

# PRICE (NOUVEAU - pour le chart temps réel)
@app.get("/api/price/{symbol}")
def get_price(symbol: str = "BTCUSDT"):
    """Prix temps réel d'un symbole"""
    try:
        import ccxt
        exchange = ccxt.bybit()
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": ticker['last'],
            "timestamp": ticker['timestamp']
        }
    except Exception as e:
        return {"symbol": symbol, "price": 0, "error": str(e)}
