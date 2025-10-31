from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, Any
import json
import os
from datetime import datetime
import logging

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartOrder PRO API", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === FICHIERS PERSISTANCE ===
CONFIG_DIR = "/opt/smartorder-pro/config"
STATE_FILE = f"{CONFIG_DIR}/state.json"
STRATEGIES_FILE = f"{CONFIG_DIR}/strategies_state.json"
EXCHANGES_FILE = f"{CONFIG_DIR}/exchanges_state.json"

os.makedirs(CONFIG_DIR, exist_ok=True)

# === ÉTAT GLOBAL (CHARGÉ DEPUIS FICHIERS) ===
def load_json(filepath, default):
    """Charger JSON avec fallback"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
    return default

def save_json(filepath, data):
    """Sauvegarder JSON"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False

# === ÉTAT INITIAL ===
DEFAULT_STRATEGIES = {
    "spot": [
        {"id": "grid_trading_spot", "name": "Grid Trading", "enabled": False, "score": 85, "pnl": 0.0},
        {"id": "dca_spot", "name": "DCA Strategy", "enabled": False, "score": 78, "pnl": 0.0},
        {"id": "scalping_spot", "name": "Scalping Volatilité", "enabled": False, "score": 72, "pnl": 0.0},
        {"id": "mean_reversion_spot", "name": "Mean Reversion", "enabled": False, "score": 68, "pnl": 0.0},
        {"id": "momentum_spot", "name": "Momentum Trading", "enabled": False, "score": 75, "pnl": 0.0},
        {"id": "breakout_spot", "name": "Breakout Detection", "enabled": False, "score": 70, "pnl": 0.0}
    ],
    "futures": [
        {"id": "adaptive_scalping", "name": "Adaptive Scalping", "enabled": False, "score": 92, "pnl": 0.0, "recommended": True},
        {"id": "grid_trading_futures", "name": "Grid Trading", "enabled": False, "score": 88, "pnl": 0.0},
        {"id": "multi_tp", "name": "Multi-TP Optimizer", "enabled": False, "score": 85, "pnl": 0.0},
        {"id": "infinity_grid", "name": "Infinity Grid", "enabled": False, "score": 80, "pnl": 0.0},
        {"id": "dca_futures", "name": "DCA Intelligent", "enabled": False, "score": 77, "pnl": 0.0}
    ],
    "hybride": [
        {"id": "adaptive_scalping_hybrid", "name": "Adaptive Scalping", "enabled": False, "score": 90, "pnl": 0.0},
        {"id": "grid_trading_hybrid", "name": "Grid Trading", "enabled": False, "score": 86, "pnl": 0.0},
        {"id": "dca_hybrid", "name": "DCA Strategy", "enabled": False, "score": 75, "pnl": 0.0},
        {"id": "arbitrage", "name": "Arbitrage Spot/Futures", "enabled": False, "score": 82, "pnl": 0.0}
    ]
}

DEFAULT_EXCHANGES = {
    "Bybit": {"connected": False, "primary": False, "latency": 0.0, "balance": {"USDT": 0.0}},
    "Binance": {"connected": True, "primary": True, "latency": 50.0, "balance": {"USDT": 1000.0}},
    "OKX": {"connected": False, "primary": False, "latency": 0.0, "balance": {"USDT": 0.0}},
    "KuCoin": {"connected": False, "primary": False, "latency": 0.0, "balance": {"USDT": 0.0}}
}

DEFAULT_STATE = {
    "mode": "futures",
    "paused": False,
    "active_exchanges": ["Binance"],
    "primary_exchange": "Binance",
    "positions": [],
    "pnl": {
        "total": 32.54,
        "daily": 32.54,
        "weekly": 32.54,
        "monthly": 32.54,
        "by_strategy": {}
    }
}

# CHARGER ÉTATS
strategies_state = load_json(STRATEGIES_FILE, DEFAULT_STRATEGIES)
exchanges_state = load_json(EXCHANGES_FILE, DEFAULT_EXCHANGES)
global_state = load_json(STATE_FILE, DEFAULT_STATE)

# === ROUTES ===
@app.get("/")
def root():
    return {
        "status": "✅ SmartOrder PRO API v2.2 (Persistent)", 
        "timestamp": datetime.now().isoformat(),
        "mode": "persistent"
    }

@app.get("/api/status")
def get_status():
    return {
        "bot_status": "online",
        "mode": global_state["mode"],
        "paused": global_state["paused"],
        "timestamp": datetime.now().isoformat()
    }

# === STRATÉGIES ===
@app.get("/api/strategies")
def get_strategies(mode: str = None):
    """Retourner stratégies SANS réinitialisation"""
    mode = mode or global_state.get("mode", "futures")
    mode_key = mode.lower()
    
    strategies = strategies_state.get(mode_key, [])
    
    return {
        "mode": mode,
        "strategies": strategies,
        "total_active": len([s for s in strategies if s.get("enabled")]),
        "timestamp": datetime.now().isoformat()
    }

@app.patch("/api/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str):
    """Toggle stratégie AVEC PERSISTANCE"""
    logger.info(f"Toggle strategy: {strategy_id}")
    
    mode = global_state.get("mode", "futures").lower()
    strategies = strategies_state.get(mode, [])
    
    strategy = None
    for s in strategies:
        if s["id"] == strategy_id:
            strategy = s
            break
    
    if not strategy:
        logger.error(f"Strategy not found: {strategy_id}")
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # TOGGLE
    strategy["enabled"] = not strategy.get("enabled", False)
    new_state = strategy["enabled"]
    
    # SAUVEGARDER IMMÉDIATEMENT
    if save_json(STRATEGIES_FILE, strategies_state):
        logger.info(f"✅ Strategy {strategy_id} {'ENABLED' if new_state else 'DISABLED'} - PERSISTED")
    else:
        logger.error(f"❌ Failed to persist strategy {strategy_id}")
    
    return {
        "status": "success",
        "strategy_id": strategy_id,
        "enabled": new_state,
        "message": f"Strategy {'enabled' if new_state else 'disabled'}",
        "persisted": True,
        "timestamp": datetime.now().isoformat()
    }

# === EXCHANGES ===
@app.get("/api/exchanges")
def get_exchanges():
    """Retourner exchanges DEPUIS FICHIER"""
    exchanges_list = []
    
    for name, data in exchanges_state.items():
        exchanges_list.append({
            "name": name,
            "connected": data.get("connected", False),
            "primary": data.get("primary", False),
            "latency": data.get("latency", 0.0),
            "balance": data.get("balance", {"USDT": 0.0})
        })
    
    return exchanges_list

@app.post("/api/exchanges/{name}/toggle")
async def toggle_exchange(name: str):
    """Toggle exchange AVEC PERSISTANCE"""
    logger.info(f"Toggle exchange: {name}")
    
    if name not in exchanges_state:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # TOGGLE
    current = exchanges_state[name]["connected"]
    exchanges_state[name]["connected"] = not current
    new_state = exchanges_state[name]["connected"]
    
    # Mettre à jour active_exchanges
    active = [ex for ex, data in exchanges_state.items() if data["connected"]]
    global_state["active_exchanges"] = active
    
    # Si primary désactivé, choisir un autre
    if name == global_state.get("primary_exchange") and not new_state:
        if active:
            global_state["primary_exchange"] = active[0]
            exchanges_state[active[0]]["primary"] = True
        else:
            global_state["primary_exchange"] = None
    
    # SAUVEGARDER
    save_json(EXCHANGES_FILE, exchanges_state)
    save_json(STATE_FILE, global_state)
    
    logger.info(f"✅ Exchange {name} {'ENABLED' if new_state else 'DISABLED'} - PERSISTED")
    
    return {
        "status": "enabled" if new_state else "disabled",
        "exchange": name,
        "active_exchanges": active,
        "primary_exchange": global_state.get("primary_exchange"),
        "persisted": True,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/exchanges/select")
async def select_primary_exchange(data: Dict[str, Any]):
    """Définir exchange principal"""
    exchange_name = data.get("exchange")
    
    if not exchange_name or exchange_name not in exchanges_state:
        raise HTTPException(status_code=400, detail="Invalid exchange")
    
    # Activer si désactivé
    if not exchanges_state[exchange_name]["connected"]:
        exchanges_state[exchange_name]["connected"] = True
    
    # Retirer primary des autres
    for ex in exchanges_state:
        exchanges_state[ex]["primary"] = (ex == exchange_name)
    
    global_state["primary_exchange"] = exchange_name
    
    # Sauvegarder
    save_json(EXCHANGES_FILE, exchanges_state)
    save_json(STATE_FILE, global_state)
    
    logger.info(f"✅ Primary exchange set to {exchange_name} - PERSISTED")
    
    return {
        "status": "success",
        "primary_exchange": exchange_name,
        "persisted": True,
        "timestamp": datetime.now().isoformat()
    }

# === POSITIONS & PNL ===
@app.get("/api/positions")
def get_positions():
    # Charger depuis data/state.json (ancien système Paper Trading)
    paper_file = "/opt/smartorder-pro/data/state.json"
    if os.path.exists(paper_file):
        try:
            with open(paper_file, 'r') as f:
                data = json.load(f)
            return data.get("positions", [])
        except:
            pass
    return []

@app.get("/api/pnl")
def get_pnl():
    paper_file = "/opt/smartorder-pro/data/state.json"
    if os.path.exists(paper_file):
        try:
            with open(paper_file, 'r') as f:
                data = json.load(f)
            pnl = data.get("pnl", {})
            return {
                "total_pnl": pnl.get("total", 0.0),
                "daily_pnl": pnl.get("daily", 0.0),
                "weekly_pnl": pnl.get("weekly", 0.0),
                "monthly_pnl": pnl.get("monthly", 0.0),
                "by_strategy": pnl.get("by_strategy", {}),
                "timestamp": datetime.now().isoformat()
            }
        except:
            pass
    return {"total_pnl": 0.0, "daily_pnl": 0.0, "weekly_pnl": 0.0, "monthly_pnl": 0.0, "by_strategy": {}}

# === MODE ===
@app.get("/api/mode")
def get_mode():
    return {
        "current_mode": global_state["mode"],
        "available_modes": ["spot", "futures", "hybrid", "manual"]
    }

@app.post("/api/mode")
def set_mode(data: Dict[str, Any]):
    mode = data.get("mode", "futures")
    global_state["mode"] = mode
    save_json(STATE_FILE, global_state)
    logger.info(f"Mode changed to {mode}")
    return {"status": "success", "mode": mode}

# === EMERGENCY ===
@app.post("/api/emergency/stop")
def emergency_stop():
    # Désactiver TOUTES les stratégies
    for mode_key in strategies_state:
        for strategy in strategies_state[mode_key]:
            strategy["enabled"] = False
    
    save_json(STRATEGIES_FILE, strategies_state)
    global_state["paused"] = True
    save_json(STATE_FILE, global_state)
    
    logger.warning("🚨 EMERGENCY STOP - All strategies disabled")
    return {"status": "emergency_stop_activated", "persisted": True}

@app.post("/api/emergency/pause")
def pause_trading():
    global_state["paused"] = True
    save_json(STATE_FILE, global_state)
    logger.warning("⏸️ Trading PAUSED")
    return {"status": "paused"}

@app.post("/api/emergency/resume")
def resume_trading():
    global_state["paused"] = False
    save_json(STATE_FILE, global_state)
    logger.info("▶️ Trading RESUMED")
    return {"status": "resumed"}

# === HEALTH ===
@app.get("/api/health")
def health_check():
    return {
        "api": "online",
        "version": "2.2.0",
        "persistence": "enabled",
        "config_dir": CONFIG_DIR,
        "files": {
            "strategies": os.path.exists(STRATEGIES_FILE),
            "exchanges": os.path.exists(EXCHANGES_FILE),
            "state": os.path.exists(STATE_FILE)
        },
        "timestamp": datetime.now().isoformat()
    }

logger.info("✅ SmartOrder PRO API v2.2 chargée (Persistent Mode)")
