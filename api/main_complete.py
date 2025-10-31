from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

app = FastAPI(title="SmartOrder PRO API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# État global
STATE = {
    "mode": "spot",
    "strategies": ["Grid Trading", "DCA Strategy", "Scalping", "Trend Following"],
    "active_strategies": [],
    "exchanges": ["Bybit", "Binance", "OKX", "KuCoin"],
    "active_exchanges": ["Bybit"],
    "watchlist": ["BTC", "ETH", "SOL", "BNB"],
    "paused": False
}

# === ROUTES WEB ===
@app.get("/")
def root():
    return {"status": "✅ SmartOrder PRO API v2.0", "timestamp": datetime.now().isoformat()}

@app.get("/dashboard")
def dashboard_page():
    return FileResponse("/opt/smartorder-pro/web/dashboard_unified.html")

@app.get("/strategies")
def strategies_page():
    return FileResponse("/opt/smartorder-pro/web/strategies_config.html")

@app.get("/mode")
def mode_page():
    return FileResponse("/opt/smartorder-pro/web/mode_switcher.html")

# === API ENDPOINTS ===

# STATUS
@app.get("/api/status")
def get_status():
    return {
        "bot_status": "online",
        "mode": STATE["mode"],
        "active_strategies": STATE["active_strategies"],
        "paused": STATE["paused"],
        "timestamp": datetime.now().isoformat()
    }

# MODES
@app.get("/api/mode")
def get_mode():
    return {
        "current_mode": STATE["mode"],
        "available_modes": ["spot", "futures", "hybrid", "manual"],
        "auto_switch": False
    }

@app.post("/api/mode")
def set_mode(data: Dict[str, Any]):
    mode = data.get("mode", "spot")
    STATE["mode"] = mode
    return {"status": "success", "mode": mode}

# STRATÉGIES
@app.get("/api/strategies")
def get_strategies():
    return [
        {"name": s, "active": s in STATE["active_strategies"], "pnl": 0.0}
        for s in STATE["strategies"]
    ]

@app.post("/api/strategies/{name}/start")
def start_strategy(name: str):
    if name not in STATE["active_strategies"]:
        STATE["active_strategies"].append(name)
    return {"status": "started", "strategy": name}

@app.post("/api/strategies/{name}/stop")
def stop_strategy(name: str):
    if name in STATE["active_strategies"]:
        STATE["active_strategies"].remove(name)
    return {"status": "stopped", "strategy": name}

# EXCHANGES
@app.get("/api/exchanges")
def get_exchanges():
    return [
        {
            "name": ex,
            "connected": ex in STATE["active_exchanges"],
            "latency": 0.0,
            "balance": {"USDT": 0.0}
        }
        for ex in STATE["exchanges"]
    ]

@app.post("/api/exchanges/{name}/toggle")
def toggle_exchange(name: str):
    if name in STATE["active_exchanges"]:
        STATE["active_exchanges"].remove(name)
        status = "disabled"
    else:
        STATE["active_exchanges"].append(name)
        status = "enabled"
    return {"status": status, "exchange": name}

# WATCHLIST
@app.get("/api/watchlist")
def get_watchlist():
    return {"symbols": STATE["watchlist"], "count": len(STATE["watchlist"])}

@app.post("/api/watchlist/add")
def add_to_watchlist(data: Dict[str, str]):
    symbol = data.get("symbol", "").upper()
    if symbol and symbol not in STATE["watchlist"]:
        STATE["watchlist"].append(symbol)
    return {"status": "added", "watchlist": STATE["watchlist"]}

@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    if symbol in STATE["watchlist"]:
        STATE["watchlist"].remove(symbol)
    return {"status": "removed", "watchlist": STATE["watchlist"]}

# POSITIONS
@app.get("/api/positions")
def get_positions():
    return []

# ORDERS
@app.get("/api/orders")
def get_orders():
    return []

@app.post("/api/orders")
def create_order(data: Dict[str, Any]):
    return {"status": "order_placed", "order_id": "mock_123"}

# PNL
@app.get("/api/pnl")
def get_pnl():
    return {
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "weekly_pnl": 0.0,
        "monthly_pnl": 0.0,
        "by_strategy": {},
        "timestamp": datetime.now().isoformat()
    }

# URGENCE
@app.post("/api/emergency/stop")
def emergency_stop():
    STATE["active_strategies"].clear()
    STATE["paused"] = True
    return {"status": "emergency_stop_activated"}

@app.post("/api/emergency/pause")
def pause_trading():
    STATE["paused"] = True
    return {"status": "paused"}

@app.post("/api/emergency/resume")
def resume_trading():
    STATE["paused"] = False
    return {"status": "resumed"}

print("✅ SmartOrder PRO API chargée")
