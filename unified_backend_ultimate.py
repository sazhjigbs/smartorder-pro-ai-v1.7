#!/usr/bin/env python3
"""
Backend unifié - Connecté au Ultimate Paper Trader
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import logging
import sqlite3
import json

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = '/opt/smartorder-pro/data/ultimate_paper.db'
STATE_FILE = '/opt/smartorder-pro/data/state.json'

# State management
def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "mode": "PAPER",
        "active_strategies": ["Ultimate AI Trader"],
        "paused": False,
        "watchlist": ["BTC", "ETH"]
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

STATE = load_state()

# Helper functions
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_latest_signal():
    """Get dernière analyse"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'timestamp': row[1],
                'symbol': row[2],
                'regime': row[3],
                'action': row[4],
                'confidence': row[5],
                'reason': row[6],
                'price': row[7],
                'rsi': row[8],
                'macd': row[9],
                'adx': row[10]
            }
    except:
        pass
    return None

def get_total_pnl():
    """Get PnL total"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(pnl) FROM trades')
        total = cursor.fetchone()[0] or 0.0
        conn.close()
        return total
    except:
        return 0.0

def get_trades_count():
    """Get nombre de trades"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM trades')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_recent_trades(limit=10):
    """Get derniers trades"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}')
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'id': row[0],
                'timestamp': row[1],
                'symbol': row[2],
                'side': row[3],
                'amount': row[4],
                'price': row[5],
                'value': row[6],
                'pnl': row[7],
                'balance_after': row[8]
            })
        conn.close()
        return trades
    except:
        return []

# API Routes
@app.get("/api/state")
def get_full_state():
    """État complet du système"""
    signal = get_latest_signal()
    total_pnl = get_total_pnl()
    trades_count = get_trades_count()
    
    return {
        "mode": STATE["mode"],
        "active_strategies": STATE["active_strategies"],
        "paused": STATE["paused"],
        "watchlist": STATE["watchlist"],
        "timestamp": datetime.now().isoformat(),
        "bot_status": {
            "running": True,
            "last_signal": signal,
            "total_pnl": total_pnl,
            "total_trades": trades_count
        }
    }

@app.post("/api/mode/set")
def set_mode(mode: str):
    """Change le mode"""
    if mode in ["PAPER", "LIVE", "spot", "futures", "hybrid", "manual"]:
        STATE["mode"] = mode.upper() if mode == "paper" or mode == "live" else mode
        save_state(STATE)
        return {"success": True, "mode": STATE["mode"]}
    raise HTTPException(400, "Mode invalide")

@app.post("/api/strategy/start")
def start_strategy(strategy: str):
    """Démarre une stratégie"""
    if strategy not in STATE["active_strategies"]:
        STATE["active_strategies"].append(strategy)
        save_state(STATE)
    return {"success": True, "strategy": strategy, "active": STATE["active_strategies"]}

@app.post("/api/strategy/stop")
def stop_strategy(strategy: str):
    """Arrête une stratégie"""
    if strategy in STATE["active_strategies"]:
        STATE["active_strategies"].remove(strategy)
        save_state(STATE)
    return {"success": True, "strategy": strategy, "active": STATE["active_strategies"]}

@app.get("/api/pnl")
def get_pnl():
    """Récupère PnL"""
    total = get_total_pnl()
    return {
        "total": total,
        "daily": total,  # Simplification
        "weekly": total,
        "monthly": total
    }

@app.get("/api/trades")
def get_trades():
    """Récupère les trades"""
    return {"trades": get_recent_trades(50)}

@app.get("/api/positions")
def get_positions():
    """Positions actives"""
    # TODO: Implémenter lecture positions depuis bot
    return {"positions": []}

@app.get("/api/watchlist/coins")
def get_watchlist():
    """Récupère la watchlist"""
    return {
        "coins": STATE["watchlist"],
        "count": len(STATE["watchlist"])
    }

@app.post("/api/watchlist/add")
def add_coin(coin: str):
    """Ajoute un coin"""
    if coin not in STATE["watchlist"]:
        STATE["watchlist"].append(coin.upper())
        save_state(STATE)
    return {"success": True, "watchlist": STATE["watchlist"]}

@app.delete("/api/watchlist/remove/{coin}")
def remove_coin(coin: str):
    """Retire un coin"""
    if coin in STATE["watchlist"]:
        STATE["watchlist"].remove(coin)
        save_state(STATE)
    return {"success": True, "watchlist": STATE["watchlist"]}

@app.post("/api/emergency/stop")
def emergency_stop():
    """Arrêt d'urgence"""
    STATE["active_strategies"].clear()
    STATE["paused"] = True
    save_state(STATE)
    return {"success": True, "message": "Arrêt d'urgence activé"}

@app.post("/api/emergency/pause")
def pause_trading():
    """Pause"""
    STATE["paused"] = True
    save_state(STATE)
    return {"success": True, "paused": True}

@app.post("/api/emergency/resume")
def resume_trading():
    """Reprendre"""
    STATE["paused"] = False
    save_state(STATE)
    return {"success": True, "paused": False}

@app.get("/api/logs")
def get_logs():
    """Logs du bot"""
    signal = get_latest_signal()
    trades = get_recent_trades(5)
    
    logs = []
    if signal:
        logs.append({
            "timestamp": signal['timestamp'],
            "message": f"Signal: {signal['action']} | Régime: {signal['regime']} | Confiance: {signal['confidence']*100:.0f}%",
            "level": "info"
        })
    
    for trade in trades:
        logs.append({
            "timestamp": trade['timestamp'],
            "message": f"{trade['side']}: {trade['amount']:.6f} @ ${trade['price']:.2f} | PnL: ${trade['pnl']:.2f}",
            "level": "success" if trade['pnl'] > 0 else "warning"
        })
    
    return {"logs": logs}

if __name__ == '__main__':
    import uvicorn
    print("✅ Backend Ultimate démarré sur http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
