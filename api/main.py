from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des adaptateurs config
try:
    sys.path.insert(0, "/opt/smartorder-pro")
    from adapters.config_adapter import (
        read_risk_config,
        write_risk_config,
        read_watchlist,
        write_watchlist,
        read_wallet,
        write_wallet,
        read_trading_modes,
        write_trading_modes
    )
    ADAPTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Config adapters not available: {e}")
    ADAPTERS_AVAILABLE = False

# Import des routers
try:
    from .trade_api import router as router_trade
except:
    router_trade = None

app = FastAPI(
    title="SmartOrder PRO API",
    description="API complète pour le trading multi-exchange",
    version="2.1.0-P2P3"
)

# ============================================================================
# P2 SECURITY - Bearer Token Authentication
# ============================================================================

API_TOKEN = os.getenv("SMARTORDER_API_TOKEN", "dev_token_12345")

def verify_token(authorization: Optional[str] = Header(None)):
    """Vérifie le Bearer Token pour les endpoints protégés."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    if parts[1] != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Status(BaseModel):
    phase: str
    status: str
    bias: str
    trend: str
    volatility: float
    pnl: float
    time_updated: str

class Position(BaseModel):
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float

class Order(BaseModel):
    order_id: str
    symbol: str
    side: str
    type: str
    quantity: float
    price: Optional[float]
    status: str
    timestamp: str

class TradingMode(BaseModel):
    mode: str  # spot, futures, hybrid
    strategy: str
    active: bool
    capital_allocated: float

class ExchangeStatus(BaseModel):
    name: str
    connected: bool
    latency: float
    balance: Dict[str, float]

# Routes principales
@app.get("/")
def root():
    return {
        "status": "✅ SmartOrder PRO API v2.1-P2P3",
        "env": os.getcwd(),
        "timestamp": datetime.now().isoformat(),
        "adapters_available": ADAPTERS_AVAILABLE,
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "wallet": "/api/wallet",
            "risk_config": "/api/risk-config",
            "watchlist": "/api/watchlist",
            "modes": "/api/modes",
            "strategies": "/api/strategies",
            "trading": "/api/trading/*",
            "positions": "/api/positions",
            "orders": "/api/orders",
            "exchanges": "/api/exchanges",
            "strategies": "/api/strategies",
            "pnl": "/api/pnl",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.get("/status", response_model=Status)
def get_status():
    return {
        "phase": "Production Ready",
        "status": "running",
        "bias": "neutral",
        "trend": "monitoring",
        "volatility": 1.5,
        "pnl": 0.0,
        "time_updated": datetime.now().isoformat()
    }

# Trading endpoints
@app.get("/api/positions", response_model=List[Position])
def get_positions():
    # TODO: Implémenter la logique réelle
    return []

@app.get("/api/orders", response_model=List[Order])
def get_orders():
    # TODO: Implémenter la logique réelle
    return []

@app.post("/api/orders")
def create_order(order: Dict[str, Any]):
    # TODO: Implémenter la logique réelle
    return {
        "status": "order_placed",
        "order_id": "mock_order_123",
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/api/orders/{order_id}")
def cancel_order(order_id: str):
    # TODO: Implémenter la logique réelle
    return {
        "status": "order_cancelled",
        "order_id": order_id,
        "timestamp": datetime.now().isoformat()
    }

# Exchange endpoints
@app.get("/api/exchanges", response_model=List[ExchangeStatus])
def get_exchanges():
    return [
        {
            "name": "Bybit",
            "connected": False,
            "latency": 0.0,
            "balance": {"USDT": 0.0}
        },
        {
            "name": "Binance",
            "connected": False,
            "latency": 0.0,
            "balance": {"USDT": 0.0}
        }
    ]

@app.get("/api/exchanges/{exchange_name}/balance")
def get_exchange_balance(exchange_name: str):
    # TODO: Implémenter la logique réelle
    return {"USDT": 0.0, "BTC": 0.0}

# Strategy endpoints
@app.get("/api/strategies")
def get_strategies():
    return [
        {"name": "Grid Trading", "active": False, "pnl": 0.0},
        {"name": "DCA Strategy", "active": False, "pnl": 0.0},
        {"name": "Scalping", "active": False, "pnl": 0.0},
        {"name": "Trend Following", "active": False, "pnl": 0.0}
    ]

@app.post("/api/strategies/{strategy_name}/start")
def start_strategy(strategy_name: str):
    # TODO: Implémenter la logique réelle
    return {
        "status": "strategy_started",
        "strategy": strategy_name,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/strategies/{strategy_name}/stop")
def stop_strategy(strategy_name: str):
    # TODO: Implémenter la logique réelle
    return {
        "status": "strategy_stopped",
        "strategy": strategy_name,
        "timestamp": datetime.now().isoformat()
    }

# PnL endpoints
@app.get("/api/pnl")
def get_pnl():
    return {
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "weekly_pnl": 0.0,
        "monthly_pnl": 0.0,
        "by_strategy": {},
        "by_exchange": {},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/pnl/history")
def get_pnl_history(days: int = 30):
    # TODO: Implémenter la logique réelle
    return {"history": [], "period_days": days}

# Trading mode endpoints
@app.get("/api/mode")
def get_trading_mode():
    return {
        "current_mode": "spot",
        "available_modes": ["spot", "futures", "hybrid"],
        "auto_switch": False
    }

@app.post("/api/mode")
def set_trading_mode(mode: TradingMode):
    # TODO: Implémenter la logique réelle
    return {
        "status": "mode_changed",
        "mode": mode.mode,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# P2 CONFIG MANAGEMENT ENDPOINTS (v2.1-P2P3 avec Adapters)
# ============================================================================

@app.get("/api/wallet")
def api_get_wallet(authorization: Optional[str] = Header(None)):
    """Récupère les informations du portefeuille (Paper Trading)."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        wallet_data = read_wallet()
        return wallet_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading wallet: {str(e)}")


@app.get("/api/risk-config")
def api_get_risk_config(authorization: Optional[str] = Header(None)):
    """Récupère la configuration Risk Management."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        risk_data = read_risk_config()
        # Retourner seulement les champs pertinents pour le dashboard
        return {
            "max_allocation_per_trade": risk_data.get("max_allocation_per_trade", 1000),
            "max_risk_per_trade": risk_data.get("max_risk_per_trade", 10),
            "stop_loss_percent": risk_data.get("stop_loss_percent", 2.0),
            "take_profit_percent": risk_data.get("take_profit_percent", 3.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading risk config: {str(e)}")


@app.post("/api/risk-config")
def api_update_risk_config(
    config: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Met à jour la configuration Risk Management."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        # Lire config actuelle pour fusion
        current_config = read_risk_config()
        
        # Mettre à jour les champs fournis
        current_config.update(config)
        
        # Sauvegarder
        write_risk_config(current_config)
        
        return {
            "status": "success",
            "message": "Risk config updated successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating risk config: {str(e)}")


@app.get("/api/watchlist")
def api_get_watchlist(authorization: Optional[str] = Header(None)):
    """Récupère la liste des paires surveillées."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        watchlist_data = read_watchlist()
        return watchlist_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading watchlist: {str(e)}")


@app.post("/api/watchlist")
def api_update_watchlist(
    data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Ajoute une paire à la watchlist ou met à jour complètement."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        # Si "pairs" fourni, remplacer complètement
        if "pairs" in data:
            write_watchlist(data["pairs"])
            return {
                "status": "success",
                "message": "Watchlist replaced successfully",
                "timestamp": datetime.now().isoformat()
            }
        
        # Sinon, ajouter une nouvelle paire
        current_watchlist = read_watchlist()
        new_pair = {
            "exchange": data.get("exchange", "binance"),
            "symbol": data.get("symbol", "BTC/USDT"),
            "active": data.get("active", True)
        }
        
        # Vérifier si la paire existe déjà
        exists = any(
            p["exchange"] == new_pair["exchange"] and p["symbol"] == new_pair["symbol"]
            for p in current_watchlist
        )
        
        if not exists:
            current_watchlist.append(new_pair)
            write_watchlist(current_watchlist)
        
        return {
            "status": "success",
            "message": "Pair added to watchlist" if not exists else "Pair already exists",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating watchlist: {str(e)}")


# ============================================================================
# P4 TRADING MODES & STRATEGIES ENDPOINTS
# ============================================================================

@app.get("/api/modes")
def api_get_modes(authorization: Optional[str] = Header(None)):
    """Récupère la configuration des modes de trading."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        data = read_trading_modes()
        return {
            "current_mode": data.get("current_mode", "spot"),
            "modes": data.get("modes", {}),
            "ai_strategy_selector": data.get("ai_strategy_selector", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading modes: {str(e)}")


@app.post("/api/modes")
def api_update_modes(
    mode_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Met à jour le mode de trading actif."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        current_config = read_trading_modes()
        
        # Mettre à jour le mode actuel
        if "current_mode" in mode_data:
            current_config["current_mode"] = mode_data["current_mode"]
        
        # Mettre à jour AI strategy selector
        if "ai_strategy_selector" in mode_data:
            current_config["ai_strategy_selector"].update(mode_data["ai_strategy_selector"])
        
        write_trading_modes(current_config)
        
        return {
            "status": "success",
            "message": "Trading mode updated successfully",
            "current_mode": current_config["current_mode"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating modes: {str(e)}")


@app.get("/api/strategies")
def api_get_strategies(
    mode: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Récupère les stratégies. Si mode spécifié, retourne uniquement celles du mode."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        data = read_trading_modes()
        strategies = data.get("strategies", {})
        
        if mode:
            return strategies.get(mode, [])
        
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading strategies: {str(e)}")


@app.post("/api/strategies")
def api_update_strategies(
    strategy_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Met à jour l'état enabled/disabled d'une ou plusieurs stratégies."""
    verify_token(authorization)
    
    if not ADAPTERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Config adapters not available")
    
    try:
        current_config = read_trading_modes()
        
        # Format: {"mode": "spot", "strategy_id": "grid_trading", "enabled": true}
        if "mode" in strategy_data and "strategy_id" in strategy_data:
            mode = strategy_data["mode"]
            strategy_id = strategy_data["strategy_id"]
            enabled = strategy_data.get("enabled", True)
            
            # Trouver et mettre à jour la stratégie
            strategies = current_config.get("strategies", {}).get(mode, [])
            for strategy in strategies:
                if strategy["id"] == strategy_id:
                    strategy["enabled"] = enabled
                    break
            
            write_trading_modes(current_config)
            
            return {
                "status": "success",
                "message": f"Strategy {strategy_id} updated",
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            }
        
        # Format: Remplacement complet des stratégies d'un mode
        elif "mode" in strategy_data and "strategies" in strategy_data:
            mode = strategy_data["mode"]
            current_config["strategies"][mode] = strategy_data["strategies"]
            write_trading_modes(current_config)
            
            return {
                "status": "success",
                "message": f"Strategies for {mode} updated",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy data format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating strategies: {str(e)}")

# Market data endpoints
@app.get("/api/market/{symbol}")
def get_market_data(symbol: str):
    # TODO: Implémenter la logique réelle
    return {
        "symbol": symbol,
        "price": 0.0,
        "change_24h": 0.0,
        "volume_24h": 0.0,
        "timestamp": datetime.now().isoformat()
    }

# Monter les fichiers statiques
try:
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")
        
        @app.get("/dashboard")
        def dashboard():
            from fastapi.responses import FileResponse
            return FileResponse(os.path.join(web_dir, "dashboard.html"))
        
        @app.get("/ui")
        def ui():
            from fastapi.responses import FileResponse
            index_file = os.path.join(web_dir, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            return {"error": "UI not found"}
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# Include trade router if available
if router_trade:
    app.include_router(router_trade, prefix="/trade", tags=["Trading"])
