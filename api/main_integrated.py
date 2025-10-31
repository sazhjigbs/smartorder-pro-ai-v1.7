from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import des modules core
try:
    from core.unified_trading_manager import UnifiedTradingManager
    from core.signal_validator import SignalValidator
    from core.exchange_router import ExchangeRouter
    from core.watchlist_manager import WatchlistManager
    from core.pnl_engine import PNLEngine
    from core.bot_state_manager import BotStateManager
    MODULES_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Modules core non disponibles: {e}")
    MODULES_AVAILABLE = False

app = FastAPI(title="SmartOrder PRO API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === INITIALISATION DES MODULES ===
class SmartOrderBackend:
    """Backend unifié SmartOrder PRO"""
    
    def __init__(self):
        self.mode = "spot"
        self.paused = False
        self.strategies = ["Grid Trading", "DCA Strategy", "Scalping", "Trend Following"]
        self.active_strategies = []
        self.exchanges = ["Bybit", "Binance", "OKX", "KuCoin"]
        self.active_exchanges = ["Bybit"]
        
        # Initialiser tous les attributs à None par défaut
        self.trading_manager = None
        self.signal_validator = None
        self.exchange_router = None
        self.watchlist_manager = None
        self.pnl_engine = None
        self.state_manager = None
        
        if MODULES_AVAILABLE:
            try:
                # Trading manager
                self.trading_manager = UnifiedTradingManager(use_encryption=False)
                
                # Signal validator
                self.signal_validator = SignalValidator()
                
                # Exchange router
                self.exchange_router = ExchangeRouter(self.trading_manager)
                
                # Watchlist
                self.watchlist_manager = WatchlistManager()
                
                # PNL Engine
                self.pnl_engine = PNLEngine()
                
                # State manager
                self.state_manager = BotStateManager()
                
                print("✅ Backend modules loaded")
            except Exception as e:
                print(f"⚠️ Error loading modules: {e}")
                import traceback
                traceback.print_exc()

# Instance globale
backend = SmartOrderBackend()

# === ROUTES WEB ===
@app.get("/")
def root():
    return {
        "status": "✅ SmartOrder PRO API v2.0", 
        "timestamp": datetime.now().isoformat(),
        "modules": "loaded" if MODULES_AVAILABLE else "mock"
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

# === API ENDPOINTS ===

# STATUS
@app.get("/api/status")
def get_status():
    return {
        "bot_status": "online",
        "mode": backend.mode,
        "active_strategies": backend.active_strategies,
        "paused": backend.paused,
        "timestamp": datetime.now().isoformat(),
        "modules_loaded": MODULES_AVAILABLE
    }

# MODES
@app.get("/api/mode")
def get_mode():
    return {
        "current_mode": backend.mode,
        "available_modes": ["spot", "futures", "hybrid", "manual"],
        "auto_switch": False
    }

@app.post("/api/mode")
def set_mode(data: Dict[str, Any]):
    mode = data.get("mode", "spot")
    backend.mode = mode
    
    # Mettre à jour state manager si disponible
    if backend.state_manager:
        backend.state_manager.set_mode(mode)
    
    return {"status": "success", "mode": mode}

# STRATÉGIES
@app.get("/api/strategies")
def get_strategies():
    strategies_data = []
    
    for s in backend.strategies:
        pnl = 0.0
        
        # Si PNL engine disponible, récupérer PNL réel
        if backend.pnl_engine and s in backend.active_strategies:
            try:
                pnl = backend.pnl_engine.get_strategy_pnl(s)
            except:
                pass
        
        strategies_data.append({
            "name": s,
            "active": s in backend.active_strategies,
            "pnl": pnl
        })
    
    return strategies_data

@app.post("/api/strategies/{name}/start")
def start_strategy(name: str):
    if name not in backend.active_strategies:
        backend.active_strategies.append(name)
        
        # Log dans state manager
        if backend.state_manager:
            backend.state_manager.log_event("strategy_started", {"name": name})
    
    return {"status": "started", "strategy": name}

@app.post("/api/strategies/{name}/stop")
def stop_strategy(name: str):
    if name in backend.active_strategies:
        backend.active_strategies.remove(name)
        
        # Log dans state manager
        if backend.state_manager:
            backend.state_manager.log_event("strategy_stopped", {"name": name})
    
    return {"status": "stopped", "strategy": name}

# EXCHANGES
@app.get("/api/exchanges")
def get_exchanges():
    exchanges_data = []
    
    for ex in backend.exchanges:
        ex_lower = ex.lower()
        
        # Récupérer infos réelles si trading manager disponible
        balance = {"USDT": 0.0}
        latency = 0.0
        connected = ex in backend.active_exchanges
        
        if backend.trading_manager and connected:
            try:
                # Récupérer balance réelle
                balance_data = backend.trading_manager.get_balance(exchange=ex_lower)
                if balance_data:
                    balance = {"USDT": balance_data.get("USDT", {}).get("free", 0.0)}
                
                # Récupérer health
                health = backend.trading_manager.health_monitor.get_exchange_health(ex_lower)
                latency = health.get("latency", 0.0)
            except:
                pass
        
        exchanges_data.append({
            "name": ex,
            "connected": connected,
            "latency": latency,
            "balance": balance
        })
    
    return exchanges_data

@app.post("/api/exchanges/{name}/toggle")
def toggle_exchange(name: str):
    if name in backend.active_exchanges:
        backend.active_exchanges.remove(name)
        status = "disabled"
    else:
        backend.active_exchanges.append(name)
        status = "enabled"
    
    # Log
    if backend.state_manager:
        backend.state_manager.log_event("exchange_toggled", {"name": name, "status": status})
    
    return {"status": status, "exchange": name}

# WATCHLIST
@app.get("/api/watchlist")
def get_watchlist():
    if backend.watchlist_manager:
        symbols = backend.watchlist_manager.get_watchlist()
    else:
        symbols = ["BTC", "ETH", "SOL", "BNB"]
    
    return {"symbols": symbols, "count": len(symbols)}

@app.post("/api/watchlist/add")
def add_to_watchlist(data: Dict[str, str]):
    symbol = data.get("symbol", "").upper()
    
    if backend.watchlist_manager:
        backend.watchlist_manager.add_symbol(symbol)
    
    return {"status": "added", "symbol": symbol}

@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    if backend.watchlist_manager:
        backend.watchlist_manager.remove_symbol(symbol)
    
    return {"status": "removed", "symbol": symbol}

# POSITIONS
@app.get("/api/positions")
def get_positions():
    positions = []
    
    if backend.trading_manager:
        try:
            # Récupérer positions réelles de tous les exchanges actifs
            for ex in backend.active_exchanges:
                ex_positions = backend.trading_manager.get_positions(exchange=ex.lower())
                positions.extend(ex_positions)
        except Exception as e:
            print(f"Error getting positions: {e}")
    
    return positions

# ORDERS
@app.get("/api/orders")
def get_orders():
    orders = []
    
    if backend.trading_manager:
        try:
            for ex in backend.active_exchanges:
                ex_orders = backend.trading_manager.get_open_orders(exchange=ex.lower())
                orders.extend(ex_orders)
        except:
            pass
    
    return orders

@app.post("/api/orders")
def create_order(data: Dict[str, Any]):
    if not backend.trading_manager:
        return {"status": "error", "message": "Trading manager not available"}
    
    try:
        # Router l'ordre vers le meilleur exchange
        symbol = data.get("symbol")
        side = data.get("side")
        order_type = data.get("type", "market")
        quantity = data.get("quantity")
        
        if backend.exchange_router:
            best_exchange = backend.exchange_router.get_best_exchange(symbol, criteria='fees')
        else:
            best_exchange = backend.active_exchanges[0].lower()
        
        # Placer l'ordre
        order = backend.trading_manager.place_order(
            exchange=best_exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity
        )
        
        return {"status": "success", "order": order}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

# PNL
@app.get("/api/pnl")
def get_pnl():
    pnl_data = {
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "weekly_pnl": 0.0,
        "monthly_pnl": 0.0,
        "by_strategy": {},
        "timestamp": datetime.now().isoformat()
    }
    
    if backend.pnl_engine:
        try:
            pnl_data["total_pnl"] = backend.pnl_engine.get_total_pnl()
            pnl_data["daily_pnl"] = backend.pnl_engine.get_daily_pnl()
            pnl_data["weekly_pnl"] = backend.pnl_engine.get_weekly_pnl()
            pnl_data["monthly_pnl"] = backend.pnl_engine.get_monthly_pnl()
            
            # PNL par stratégie
            for strat in backend.active_strategies:
                pnl_data["by_strategy"][strat] = backend.pnl_engine.get_strategy_pnl(strat)
        except:
            pass
    
    return pnl_data

# URGENCE
@app.post("/api/emergency/stop")
def emergency_stop():
    backend.active_strategies.clear()
    backend.paused = True
    
    # Fermer toutes les positions si trading manager disponible
    if backend.trading_manager:
        try:
            for ex in backend.active_exchanges:
                backend.trading_manager.close_all_positions(exchange=ex.lower())
        except:
            pass
    
    if backend.state_manager:
        backend.state_manager.log_event("emergency_stop", {"timestamp": datetime.now().isoformat()})
    
    return {"status": "emergency_stop_activated"}

@app.post("/api/emergency/pause")
def pause_trading():
    backend.paused = True
    
    if backend.state_manager:
        backend.state_manager.log_event("trading_paused", {"timestamp": datetime.now().isoformat()})
    
    return {"status": "paused"}

@app.post("/api/emergency/resume")
def resume_trading():
    backend.paused = False
    
    if backend.state_manager:
        backend.state_manager.log_event("trading_resumed", {"timestamp": datetime.now().isoformat()})
    
    return {"status": "resumed"}

# HEALTH CHECK
@app.get("/api/health")
def health_check():
    health = {
        "api": "online",
        "timestamp": datetime.now().isoformat(),
        "modules": {
            "trading_manager": backend.trading_manager is not None,
            "signal_validator": backend.signal_validator is not None if MODULES_AVAILABLE else False,
            "exchange_router": backend.exchange_router is not None if MODULES_AVAILABLE else False,
            "watchlist_manager": backend.watchlist_manager is not None if MODULES_AVAILABLE else False,
            "pnl_engine": backend.pnl_engine is not None if MODULES_AVAILABLE else False,
            "state_manager": backend.state_manager is not None if MODULES_AVAILABLE else False
        }
    }
    
    if backend.trading_manager:
        health["exchanges"] = {}
        for ex in backend.active_exchanges:
            ex_health = backend.trading_manager.health_monitor.get_exchange_health(ex.lower())
            health["exchanges"][ex] = ex_health
    
    return health

print("✅ SmartOrder PRO API chargée (mode intégré)")
