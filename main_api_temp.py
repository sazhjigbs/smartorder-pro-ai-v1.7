from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path

app = FastAPI(title="SmartOrder PRO API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === STOCKAGE PERSISTANT ===
STATE_FILE = "/opt/smartorder-pro/data/state.json"

def load_state():
    """Charger l'état depuis le fichier"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {
        "mode": "spot",
        "paused": False,
        "active_strategies": [],
        "active_exchanges": ["Bybit"],
        "watchlist": ["BTC", "ETH", "SOL", "BNB"],
        "positions": [],
        "pnl": {
            "total": 0.0,
            "daily": 0.0,
            "weekly": 0.0,
            "monthly": 0.0,
            "by_strategy": {}
        }
    }

def save_state(state):
    """Sauvegarder l'état"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# === BACKEND ===
class SmartOrderBackend:
    """Backend SmartOrder PRO en mode standalone"""
    
    def __init__(self):
        self.strategies = [
            "Grid Trading",
            "DCA Strategy", 
            "Scalping",
            "Trend Following"
        ]
        self.exchanges = ["Bybit", "Binance", "OKX", "KuCoin"]
        
        # Charger état persistant
        self.state = load_state()
    
    def save(self):
        """Sauvegarder l'état"""
        save_state(self.state)

# Instance globale
backend = SmartOrderBackend()

# === ROUTES WEB ===
@app.get("/")
def root():
    return {
        "status": "✅ SmartOrder PRO API v2.0 (Standalone)", 
        "timestamp": datetime.now().isoformat(),
        "mode": "standalone"
    }

@app.get("/dashboard")
def dashboard_page():
    return FileResponse("/opt/smartorder-pro/web/dashboard_unified.html")

@app.get("/strategies")
def strategies_page():
    return FileResponse("/opt/smartorder-pro/web/strategies_config.html")

@app.get("/mode")
def mode_page():
    return FileResponse("/opt/smartorder-pro/web/mode_switcher.html")

@app.get("/analytics")
def analytics_page():
    return FileResponse("/opt/smartorder-pro/web/dashboard_advanced.html")

@app.get("/backtesting")
def backtesting_page():
    return FileResponse("/opt/smartorder-pro/web/backtesting.html")

# === API ENDPOINTS ===

# STATUS
@app.get("/api/status")
def get_status():
    return {
        "bot_status": "online",
        "mode": backend.state["mode"],
        "active_strategies": backend.state["active_strategies"],
        "paused": backend.state["paused"],
        "timestamp": datetime.now().isoformat(),
        "modules_loaded": True
    }

# MODES
@app.get("/api/mode")
def get_mode():
    return {
        "current_mode": backend.state["mode"],
        "available_modes": ["spot", "futures", "hybrid", "manual"],
        "auto_switch": False
    }

@app.post("/api/mode")
def set_mode(data: Dict[str, Any]):
    mode = data.get("mode", "spot")
    backend.state["mode"] = mode
    backend.save()
    return {"status": "success", "mode": mode}

# STRATÉGIES
@app.get("/api/strategies")
def get_strategies():
    strategies_data = []
    
    for s in backend.strategies:
        pnl = backend.state["pnl"]["by_strategy"].get(s, 0.0)
        
        strategies_data.append({
            "name": s,
            "active": s in backend.state["active_strategies"],
            "pnl": pnl
        })
    
    return strategies_data

@app.post("/api/strategies/{name}/start")
def start_strategy(name: str):
    if name not in backend.state["active_strategies"]:
        backend.state["active_strategies"].append(name)
        backend.save()
    
    return {"status": "started", "strategy": name}

@app.post("/api/strategies/{name}/stop")
def stop_strategy(name: str):
    if name in backend.state["active_strategies"]:
        backend.state["active_strategies"].remove(name)
        backend.save()
    
    return {"status": "stopped", "strategy": name}

# EXCHANGES
@app.get("/api/exchanges")
def get_exchanges():
    exchanges_data = []
    
    for ex in backend.exchanges:
        connected = ex in backend.state["active_exchanges"]
        
        # Simuler des données réalistes
        balance_usdt = 1000.0 if connected else 0.0
        latency = 50.0 if connected else 0.0
        
        exchanges_data.append({
            "name": ex,
            "connected": connected,
            "latency": latency,
            "balance": {"USDT": balance_usdt}
        })
    
    return exchanges_data

@app.post("/api/exchanges/{name}/toggle")
def toggle_exchange(name: str):
    if name in backend.state["active_exchanges"]:
        backend.state["active_exchanges"].remove(name)
        status = "disabled"
    else:
        backend.state["active_exchanges"].append(name)
        status = "enabled"
    
    backend.save()
    return {"status": status, "exchange": name}

# WATCHLIST
@app.get("/api/watchlist")
def get_watchlist():
    return {
        "symbols": backend.state["watchlist"], 
        "count": len(backend.state["watchlist"])
    }

@app.post("/api/watchlist/add")
def add_to_watchlist(data: Dict[str, str]):
    symbol = data.get("symbol", "").upper()
    
    if symbol and symbol not in backend.state["watchlist"]:
        backend.state["watchlist"].append(symbol)
        backend.save()
    
    return {"status": "added", "symbol": symbol, "watchlist": backend.state["watchlist"]}

@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    if symbol in backend.state["watchlist"]:
        backend.state["watchlist"].remove(symbol)
        backend.save()
    
    return {"status": "removed", "symbol": symbol, "watchlist": backend.state["watchlist"]}

# POSITIONS
@app.get("/api/positions")
def get_positions():
    return backend.state.get("positions", [])

# ORDERS
@app.get("/api/orders")
def get_orders():
    return []

@app.post("/api/orders")
def create_order(data: Dict[str, Any]):
    # Simuler création d'ordre
    order_id = f"ORDER_{datetime.now().timestamp()}"
    return {"status": "success", "order_id": order_id, "data": data}

# PNL
@app.get("/api/pnl")
def get_pnl():
    return {
        "total_pnl": backend.state["pnl"]["total"],
        "daily_pnl": backend.state["pnl"]["daily"],
        "weekly_pnl": backend.state["pnl"]["weekly"],
        "monthly_pnl": backend.state["pnl"]["monthly"],
        "by_strategy": backend.state["pnl"]["by_strategy"],
        "timestamp": datetime.now().isoformat()
    }

# URGENCE
@app.post("/api/emergency/stop")
def emergency_stop():
    backend.state["active_strategies"].clear()
    backend.state["paused"] = True
    backend.state["positions"] = []
    backend.save()
    
    return {"status": "emergency_stop_activated"}

@app.post("/api/emergency/pause")
def pause_trading():
    backend.state["paused"] = True
    backend.save()
    return {"status": "paused"}

@app.post("/api/emergency/resume")
def resume_trading():
    backend.state["paused"] = False
    backend.save()
    return {"status": "resumed"}

# HEALTH CHECK
@app.get("/api/health")
def health_check():
    health = {
        "api": "online",
        "timestamp": datetime.now().isoformat(),
        "mode": "standalone",
        "state_file": STATE_FILE,
        "state_loaded": True,
        "modules": {
            "trading_manager": True,
            "signal_validator": True,
            "exchange_router": True,
            "watchlist_manager": True,
            "pnl_engine": True,
            "state_manager": True
        }
    }
    
    # Statut exchanges
    health["exchanges"] = {}
    for ex in backend.state["active_exchanges"]:
        health["exchanges"][ex] = {
            "status": "online",
            "latency": 50.0,
            "last_check": datetime.now().isoformat()
        }
    
    return health

# LOGS
@app.get("/api/logs")
def get_logs():
    """Récupérer les derniers logs"""
    logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": "Système démarré avec succès"
        }
    ]
    
    # Ajouter logs des stratégies actives
    for strategy in backend.state["active_strategies"]:
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": "success",
            "message": f"Stratégie {strategy} active"
        })
    
    return {"logs": logs, "count": len(logs)}

print("✅ SmartOrder PRO API chargée (Standalone Mode)")

# Chart routes integration
from api.api_charts import register_chart_routes
register_chart_routes(app)
