#!/usr/bin/env python3
"""
BACKEND API COMPLET
Support TOUS les modes + Exchanges multiples
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI(title="SmartOrder PRO API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins fichiers
STATE_FILE = '/opt/smartorder-pro/data/trading_state.json'
ALL_MODES_FILE = '/opt/smartorder-pro/data/all_modes_test.json'
SIGNALS_FILE = '/opt/smartorder-pro/data/signals.json'

# Models
class TradingMode(BaseModel):
    mode: str  # SPOT, FUTURES, HYBRIDE, MANUEL

class StrategyToggle(BaseModel):
    strategy: str
    enabled: bool

class ExchangeStatus(BaseModel):
    exchange: str
    connected: bool
    balance: float

def read_json(filepath, default=None):
    """Lit un fichier JSON"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return default if default else {}
    except Exception as e:
        print(f"Erreur lecture {filepath}: {e}")
        return default if default else {}

def write_json(filepath, data):
    """Écrit un fichier JSON"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Erreur écriture {filepath}: {e}")
        return False

@app.get("/api/state")
def get_trading_state():
    """État général du trading"""
    state = read_json(STATE_FILE, {
        'mode': 'PAPER',
        'current_capital': 10000,
        'total_pnl': 0,
        'active_strategies': ['Grid Trading', 'DCA Strategy', 'Scalping'],
        'positions': [],
        'last_update': datetime.now().isoformat()
    })
    
    # Merge avec test all modes si disponible
    all_modes = read_json(ALL_MODES_FILE)
    if all_modes and 'modes' in all_modes:
        state['all_modes'] = all_modes['modes']
        state['current_price'] = all_modes.get('current_price', 0)
    
    return state

@app.get("/api/exchanges")
def get_exchanges():
    """Liste des exchanges connectés"""
    all_modes = read_json(ALL_MODES_FILE)
    
    if all_modes and 'exchanges' in all_modes:
        exchanges = []
        for name, info in all_modes['exchanges'].items():
            exchanges.append({
                'name': name,
                'connected': info['connected'],
                'balance': info['balance']
            })
        return {'exchanges': exchanges}
    
    # Fallback
    return {
        'exchanges': [
            {'name': 'Bybit', 'connected': True, 'balance': 10000},
            {'name': 'Binance', 'connected': False, 'balance': 0},
            {'name': 'OKX', 'connected': False, 'balance': 0}
        ]
    }

@app.get("/api/modes")
def get_modes_status():
    """Statut de tous les modes"""
    all_modes = read_json(ALL_MODES_FILE)
    
    if all_modes and 'modes' in all_modes:
        return {
            'modes': all_modes['modes'],
            'current_price': all_modes.get('current_price', 0),
            'timestamp': all_modes.get('timestamp')
        }
    
    return {
        'modes': {
            'SPOT': {'balance': 10000, 'pnl': 0, 'positions': 0, 'trades': 0},
            'FUTURES': {'balance': 10000, 'pnl': 0, 'positions': 0, 'trades': 0},
            'HYBRIDE': {'balance': 10000, 'pnl': 0, 'positions': 0, 'trades': 0},
            'MANUEL': {'balance': 10000, 'pnl': 0, 'positions': 0, 'trades': 0}
        }
    }

@app.post("/api/mode")
def set_trading_mode(data: TradingMode):
    """Change le mode de trading"""
    state = read_json(STATE_FILE, {})
    state['mode'] = data.mode
    state['last_update'] = datetime.now().isoformat()
    
    if write_json(STATE_FILE, state):
        return {'success': True, 'mode': data.mode}
    else:
        raise HTTPException(status_code=500, detail="Erreur sauvegarde")

@app.post("/api/strategy/toggle")
def toggle_strategy(data: StrategyToggle):
    """Active/désactive une stratégie"""
    state = read_json(STATE_FILE, {'active_strategies': []})
    
    strategies = state.get('active_strategies', [])
    
    if data.enabled and data.strategy not in strategies:
        strategies.append(data.strategy)
    elif not data.enabled and data.strategy in strategies:
        strategies.remove(data.strategy)
    
    state['active_strategies'] = strategies
    state['last_update'] = datetime.now().isoformat()
    
    if write_json(STATE_FILE, state):
        return {'success': True, 'active_strategies': strategies}
    else:
        raise HTTPException(status_code=500, detail="Erreur sauvegarde")

@app.get("/api/signals")
def get_signals():
    """Signaux de trading récents"""
    signals = read_json(SIGNALS_FILE, {'signals': []})
    return signals

@app.get("/api/performance")
def get_performance():
    """Performance globale"""
    all_modes = read_json(ALL_MODES_FILE)
    
    if all_modes and 'modes' in all_modes:
        total_pnl = sum(mode.get('pnl', 0) for mode in all_modes['modes'].values())
        total_trades = sum(mode.get('trades', 0) for mode in all_modes['modes'].values())
        
        return {
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'modes': all_modes['modes']
        }
    
    return {'total_pnl': 0, 'total_trades': 0, 'modes': {}}

@app.get("/api/logs")
def get_logs(limit: int = 50):
    """Logs récents"""
    try:
        log_file = '/opt/smartorder-pro/logs/trading.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                return {'logs': lines[-limit:]}
        return {'logs': []}
    except Exception as e:
        return {'logs': [f"Erreur lecture logs: {e}"]}

@app.get("/health")
def health_check():
    """Health check"""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'api_version': '2.0'
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
