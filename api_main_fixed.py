from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# === LOGGING CONFIGURATION ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartOrder PRO API", version="2.1.0")

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
STRATEGIES_FILE = "/opt/smartorder-pro/data/strategies_state.json"

def load_state():
    """Charger l'état depuis le fichier"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    return {
        "mode": "spot",
        "paused": False,
        "active_strategies": [],
        "active_exchanges": ["Bybit"],
        "primary_exchange": "Bybit",
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
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"State saved: {state.get('mode')}, exchanges: {state.get('active_exchanges')}")
    except Exception as e:
        logger.error(f"Error saving state: {e}")

def load_strategies():
    """Charger l'état des stratégies"""
    if os.path.exists(STRATEGIES_FILE):
        try:
            with open(STRATEGIES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
    
    # État initial des stratégies
    return {
        "spot": [
            {"id": "grid_trading_spot", "name": "Grid Trading", "enabled": True, "score": 85, "pnl": 125.50},
            {"id": "dca_spot", "name": "DCA Strategy", "enabled": True, "score": 78, "pnl": 89.20},
            {"id": "scalping_spot", "name": "Scalping Volatilité", "enabled": False, "score": 72, "pnl": 0.00},
            {"id": "mean_reversion_spot", "name": "Mean Reversion", "enabled": False, "score": 68, "pnl": 0.00},
            {"id": "momentum_spot", "name": "Momentum Trading", "enabled": False, "score": 75, "pnl": 0.00},
            {"id": "breakout_spot", "name": "Breakout Detection", "enabled": False, "score": 70, "pnl": 0.00}
        ],
        "futures": [
            {"id": "adaptive_scalping", "name": "Adaptive Scalping", "enabled": True, "score": 92, "pnl": 234.80, "recommended": True},
            {"id": "grid_trading_futures", "name": "Grid Trading", "enabled": True, "score": 88, "pnl": 156.30},
            {"id": "multi_tp", "name": "Multi-TP Optimizer", "enabled": True, "score": 85, "pnl": 98.50},
            {"id": "infinity_grid", "name": "Infinity Grid", "enabled": False, "score": 80, "pnl": 0.00},
            {"id": "dca_futures", "name": "DCA Intelligent", "enabled": False, "score": 77, "pnl": 0.00}
        ],
        "hybride": [
            {"id": "adaptive_scalping_hybrid", "name": "Adaptive Scalping", "enabled": True, "score": 90, "pnl": 167.90},
            {"id": "grid_trading_hybrid", "name": "Grid Trading", "enabled": True, "score": 86, "pnl": 145.20},
            {"id": "dca_hybrid", "name": "DCA Strategy", "enabled": False, "score": 75, "pnl": 0.00},
            {"id": "arbitrage", "name": "Arbitrage Spot/Futures", "enabled": False, "score": 82, "pnl": 0.00}
        ]
    }

def save_strategies(strategies):
    """Sauvegarder l'état des stratégies"""
    os.makedirs(os.path.dirname(STRATEGIES_FILE), exist_ok=True)
    try:
        with open(STRATEGIES_FILE, 'w') as f:
            json.dump(strategies, f, indent=2)
        logger.info(f"Strategies saved")
    except Exception as e:
        logger.error(f"Error saving strategies: {e}")

# === BACKEND ===
class SmartOrderBackend:
    """Backend SmartOrder PRO en mode standalone"""
    
    def __init__(self):
        self.exchanges = ["Bybit", "Binance", "OKX", "KuCoin"]
        self.state = load_state()
        self.strategies = load_strategies()
    
    def save(self):
        """Sauvegarder l'état"""
        save_state(self.state)
        save_strategies(self.strategies)

# Instance globale
backend = SmartOrderBackend()

# === ROUTES WEB ===
@app.get("/")
def root():
    return {
        "status": "✅ SmartOrder PRO API v2.1 (Fixed)", 
        "timestamp": datetime.now().isoformat(),
        "mode": "standalone"
    }

@app.get("/dashboard")
def dashboard_page():
    return FileResponse("/opt/smartorder-pro/web/dashboard.html")

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
    logger.info(f"Mode change requested: {mode}")
    backend.state["mode"] = mode
    backend.save()
    return {"status": "success", "mode": mode}

# STRATÉGIES - NOUVEAU : TOGGLE AVEC PERSISTANCE
@app.get("/api/strategies")
def get_active_strategies(mode: str = None):
    """Get active strategies for current mode"""
    mode = mode or backend.state.get("mode", "futures")
    mode_key = mode.lower()
    
    strategies = backend.strategies.get(mode_key, [])
    
    return {
        "mode": mode,
        "strategies": strategies,
        "total_active": len([s for s in strategies if s.get("enabled")])
    }

@app.patch("/api/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str):
    """Toggle strategy enabled/disabled state"""
    logger.info(f"Toggle strategy requested: {strategy_id}")
    
    mode = backend.state.get("mode", "futures").lower()
    strategies = backend.strategies.get(mode, [])
    
    # Trouver la stratégie
    strategy = None
    for s in strategies:
        if s["id"] == strategy_id:
            strategy = s
            break
    
    if not strategy:
        logger.error(f"Strategy not found: {strategy_id}")
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Toggle état
    strategy["enabled"] = not strategy.get("enabled", False)
    new_state = strategy["enabled"]
    
    # Sauvegarder
    backend.save()
    
    # Log
    logger.info(f"Strategy {strategy_id} {'ENABLED' if new_state else 'DISABLED'}")
    
    return {
        "status": "success",
        "strategy_id": strategy_id,
        "enabled": new_state,
        "message": f"Strategy {'enabled' if new_state else 'disabled'}",
        "timestamp": datetime.now().isoformat()
    }

# EXCHANGES - NOUVEAU : TOGGLE ET SELECT AVEC PERSISTANCE
@app.get("/api/exchanges")
def get_exchanges():
    exchanges_data = []
    
    for ex in backend.exchanges:
        connected = ex in backend.state.get("active_exchanges", ["Bybit"])
        is_primary = ex == backend.state.get("primary_exchange", "Bybit")
        
        # Simuler des données réalistes
        balance_usdt = 1000.0 if connected else 0.0
        latency = 50.0 if connected else 0.0
        
        exchanges_data.append({
            "name": ex,
            "connected": connected,
            "primary": is_primary,
            "latency": latency,
            "balance": {"USDT": balance_usdt}
        })
    
    return exchanges_data

@app.post("/api/exchanges/{name}/toggle")
async def toggle_exchange(name: str):
    """Toggle exchange enabled/disabled"""
    logger.info(f"Toggle exchange requested: {name}")
    
    if name not in backend.exchanges:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    active_exchanges = backend.state.get("active_exchanges", [])
    
    if name in active_exchanges:
        active_exchanges.remove(name)
        status = "disabled"
        logger.info(f"Exchange {name} DISABLED")
    else:
        active_exchanges.append(name)
        status = "enabled"
        logger.info(f"Exchange {name} ENABLED")
    
    backend.state["active_exchanges"] = active_exchanges
    
    # Si on désactive le primary, en choisir un autre
    if name == backend.state.get("primary_exchange") and status == "disabled":
        if active_exchanges:
            backend.state["primary_exchange"] = active_exchanges[0]
            logger.info(f"Primary exchange changed to {active_exchanges[0]}")
    
    backend.save()
    
    return {
        "status": status,
        "exchange": name,
        "active_exchanges": active_exchanges,
        "primary_exchange": backend.state.get("primary_exchange"),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/exchanges/select")
async def select_exchange(data: Dict[str, Any]):
    """Select primary exchange for routing"""
    exchange_name = data.get("exchange")
    
    if not exchange_name or exchange_name not in backend.exchanges:
        raise HTTPException(status_code=400, detail="Invalid exchange")
    
    logger.info(f"Select primary exchange: {exchange_name}")
    
    # Activer l'exchange s'il ne l'est pas
    if exchange_name not in backend.state.get("active_exchanges", []):
        backend.state["active_exchanges"].append(exchange_name)
    
    # Définir comme primary
    backend.state["primary_exchange"] = exchange_name
    
    backend.save()
    
    logger.info(f"Primary exchange set to {exchange_name}")
    
    return {
        "status": "success",
        "primary_exchange": exchange_name,
        "active_exchanges": backend.state.get("active_exchanges"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/exchanges/status")
def get_exchanges_status():
    """Get detailed exchange status"""
    return {
        "active_exchanges": backend.state.get("active_exchanges", []),
        "primary_exchange": backend.state.get("primary_exchange", "Bybit"),
        "timestamp": datetime.now().isoformat()
    }

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
    logger.warning("EMERGENCY STOP ACTIVATED")
    return {"status": "emergency_stop_activated"}

@app.post("/api/emergency/pause")
def pause_trading():
    backend.state["paused"] = True
    backend.save()
    logger.warning("Trading PAUSED")
    return {"status": "paused"}

@app.post("/api/emergency/resume")
def resume_trading():
    backend.state["paused"] = False
    backend.save()
    logger.info("Trading RESUMED")
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
    logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": "Système démarré avec succès"
        }
    ]
    
    for strategy in backend.state["active_strategies"]:
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": "success",
            "message": f"Stratégie {strategy} active"
        })
    
    return {"logs": logs, "count": len(logs)}

# STATE
@app.get('/api/state')
async def get_state_unified():
    try:
        state = backend.state
        return {
            'mode': state.get('mode', 'PAPER'),
            'paused': state.get('paused', False),
            'active_strategies': state.get('active_strategies', []),
            'active_exchanges': state.get('active_exchanges', []),
            'primary_exchange': state.get('primary_exchange', 'Bybit'),
            'timestamp': datetime.now().isoformat(),
            'pnl': state.get('pnl', {'total': 0, 'daily': 0, 'weekly': 0, 'monthly': 0})
        }
    except Exception as e:
        return {'error': str(e), 'mode': 'PAPER', 'paused': False}

# FUNDING RATES - DÉCOUPLÉ PAR EXCHANGE
@app.get("/api/funding/rates")
def get_funding_rates():
    """Get current funding rates from primary exchange"""
    primary_exchange = backend.state.get("primary_exchange", "Bybit")
    
    # Mock data - à remplacer par vraies données selon exchange
    rates_by_exchange = {
        "Bybit": [
            {"symbol": "BTC/USDT:USDT", "rate": 0.0001, "next_funding": "2025-10-30T20:00:00"},
            {"symbol": "ETH/USDT:USDT", "rate": 0.00008, "next_funding": "2025-10-30T20:00:00"}
        ],
        "Binance": [
            {"symbol": "BTC/USDT", "rate": 0.00009, "next_funding": "2025-10-30T20:00:00"},
            {"symbol": "ETH/USDT", "rate": 0.00007, "next_funding": "2025-10-30T20:00:00"}
        ],
        "KuCoin": [
            {"symbol": "BTCUSDTM", "rate": 0.00011, "next_funding": "2025-10-30T20:00:00"},
            {"symbol": "ETHUSDTM", "rate": 0.00009, "next_funding": "2025-10-30T20:00:00"}
        ],
        "OKX": [
            {"symbol": "BTC-USDT-SWAP", "rate": 0.0001, "next_funding": "2025-10-30T20:00:00"},
            {"symbol": "ETH-USDT-SWAP", "rate": 0.00008, "next_funding": "2025-10-30T20:00:00"}
        ]
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "source_exchange": primary_exchange,
        "rates": rates_by_exchange.get(primary_exchange, [])
    }

logger.info("✅ SmartOrder PRO API v2.1 chargée (Fixed Mode)")
