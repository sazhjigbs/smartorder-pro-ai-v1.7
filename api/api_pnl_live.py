#!/usr/bin/env python3
"""
SmartOrder PRO - PnL Live API
==============================
API REST + WebSocket pour PnL temps réel

Endpoints:
- GET /api/pnl/positions - Positions avec PnL live
- GET /api/pnl/portfolio - PnL global du portfolio
- GET /api/pnl/statistics - Statistiques complètes
- GET /api/pnl/daily - PnL journalier (30 jours)
- WS /ws/pnl - WebSocket pour updates temps réel

Usage:
    uvicorn api.api_pnl_live:app --host 0.0.0.0 --port 8556
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime

# Import nos modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pnl_engine import PnLEngine, Position
from web.portal_v5_pro.ws_private import PrivateWSClient

# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title="SmartOrder PRO - PnL Live API",
    description="API temps réel pour suivi PnL et positions",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

# PnL Engine
pnl_engine = PnLEngine(initial_balance=10000)  # À adapter selon balance réelle

# WebSocket client Bybit
ws_client = None
ws_connected = False

# WebSocket connections (pour broadcast)
active_ws_connections: List[WebSocket] = []


# ==============================================================================
# STARTUP / SHUTDOWN
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Démarrage: Connecte au WebSocket Bybit"""
    global ws_client, ws_connected
    
    try:
        ws_client = PrivateWSClient()
        
        # Callbacks pour updates temps réel
        async def on_position_update(position):
            """Callback quand position update"""
            # Broadcast aux clients WebSocket connectés
            await broadcast_position_update(position)
        
        async def on_wallet_update(wallet):
            """Callback quand wallet update"""
            # Update balance dans PnL engine
            if wallet["coin"] == "USDT":
                pnl_engine.current_balance = wallet["wallet_balance"]
        
        ws_client.on_position = on_position_update
        ws_client.on_wallet = on_wallet_update
        
        # Connecter
        await ws_client.connect()
        await asyncio.sleep(2)  # Attendre auth
        
        # Souscrire
        await ws_client.subscribe_all()
        
        ws_connected = True
        print("✅ PnL Live API démarrée - WebSocket Bybit connecté")
        
    except Exception as e:
        print(f"❌ Erreur démarrage WebSocket: {e}")
        ws_connected = False


@app.on_event("shutdown")
async def shutdown_event():
    """Arrêt: Ferme WebSocket"""
    global ws_client, ws_connected
    
    if ws_client:
        await ws_client.close()
        ws_connected = False
    
    print("👋 PnL Live API arrêtée")


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

async def broadcast_position_update(position: Dict[str, Any]):
    """Broadcast update position à tous les clients WS connectés"""
    if not active_ws_connections:
        return
    
    message = {
        "type": "position_update",
        "data": position,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Envoyer à tous les clients
    disconnected = []
    for ws in active_ws_connections:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    # Retirer les déconnectés
    for ws in disconnected:
        active_ws_connections.remove(ws)


def convert_ws_position_to_dataclass(ws_pos: Dict[str, Any]) -> Position:
    """Convertit position du WS client en dataclass Position"""
    return Position(
        symbol=ws_pos["symbol"],
        side=ws_pos["side"],
        size=ws_pos["size"],
        entry_price=ws_pos["entry_price"],
        mark_price=ws_pos["mark_price"],
        leverage=int(ws_pos["leverage"])
    )


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Page d'accueil API"""
    return {
        "service": "SmartOrder PRO - PnL Live API",
        "version": "1.0.0",
        "status": "running",
        "ws_connected": ws_connected,
        "endpoints": {
            "positions": "/api/pnl/positions",
            "portfolio": "/api/pnl/portfolio",
            "statistics": "/api/pnl/statistics",
            "daily_pnl": "/api/pnl/daily",
            "websocket": "/ws/pnl"
        }
    }


@app.get("/api/pnl/positions")
async def get_positions_with_pnl():
    """
    Retourne toutes les positions avec PnL live
    
    Returns:
        Liste des positions avec PnL calculé
    """
    if not ws_client:
        raise HTTPException(status_code=503, detail="WebSocket non connecté")
    
    positions_dict = ws_client.get_positions()
    
    if not positions_dict:
        return {
            "positions": [],
            "count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Calculer PnL enrichi pour chaque position
    enriched_positions = []
    
    for symbol, pos in positions_dict.items():
        # PnL détaillé
        pnl_detail = pnl_engine.calculate_position_pnl(
            entry_price=pos["entry_price"],
            mark_price=pos["mark_price"],
            size=pos["size"],
            side=pos["side"],
            leverage=pos["leverage"]
        )
        
        # Prix liquidation
        liq_price = pnl_engine.calculate_liquidation_price(
            entry_price=pos["entry_price"],
            leverage=pos["leverage"],
            side=pos["side"]
        )
        
        # Distance à liquidation %
        current_price = pos["mark_price"]
        liq_distance_pct = abs((current_price - liq_price) / current_price) * 100
        
        enriched_positions.append({
            "symbol": symbol,
            "side": pos["side"],
            "size": pos["size"],
            "entry_price": pos["entry_price"],
            "mark_price": pos["mark_price"],
            "leverage": pos["leverage"],
            "pnl_usd": pnl_detail["pnl_usd"],
            "pnl_percent": pnl_detail["pnl_percent"],
            "roi_percent": pnl_detail["roi_percent"],
            "margin_used": pnl_detail["margin_used"],
            "position_value": pnl_detail["position_value"],
            "liq_price": liq_price,
            "liq_distance_pct": round(liq_distance_pct, 2),
            "timestamp": pos["timestamp"]
        })
    
    return {
        "positions": enriched_positions,
        "count": len(enriched_positions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/pnl/portfolio")
async def get_portfolio_pnl():
    """
    Retourne PnL global du portfolio
    
    Returns:
        Métriques globales (PnL total, ROI, balance, etc.)
    """
    if not ws_client:
        raise HTTPException(status_code=503, detail="WebSocket non connecté")
    
    positions_dict = ws_client.get_positions()
    
    if not positions_dict:
        return {
            "total_pnl_usd": 0.0,
            "total_margin_used": 0.0,
            "roi_percent": 0.0,
            "positions_count": 0,
            "long_count": 0,
            "short_count": 0,
            "current_balance": pnl_engine.current_balance,
            "effective_balance": pnl_engine.current_balance,
            "position_details": [],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Convertir en Position objects
    positions = [
        convert_ws_position_to_dataclass(pos)
        for pos in positions_dict.values()
    ]
    
    # Calculer portfolio PnL
    portfolio = pnl_engine.calculate_portfolio_pnl(positions)
    portfolio["timestamp"] = datetime.utcnow().isoformat()
    
    return portfolio


@app.get("/api/pnl/statistics")
async def get_trading_statistics():
    """
    Retourne statistiques complètes de trading
    
    Returns:
        Stats: win rate, profit factor, drawdown, best/worst, etc.
    """
    stats = pnl_engine.get_statistics()
    
    # Ajouter Sharpe ratio
    sharpe = pnl_engine.calculate_sharpe_ratio()
    stats["sharpe_ratio"] = sharpe
    
    # Ajouter timestamp
    stats["timestamp"] = datetime.utcnow().isoformat()
    
    return stats


@app.get("/api/pnl/daily")
async def get_daily_pnl(days: int = 30):
    """
    Retourne PnL journalier
    
    Args:
        days: Nombre de jours (défaut 30)
    
    Returns:
        Liste {date, pnl} des N derniers jours
    """
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days doit être entre 1 et 365")
    
    daily = pnl_engine.get_daily_pnl(days=days)
    
    return {
        "daily_pnl": daily,
        "days": days,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/pnl/latency")
async def get_latency():
    """
    Retourne latence WebSocket
    
    Returns:
        Latence en ms
    """
    if not ws_client or not ws_connected:
        return {
            "connected": False,
            "latency_ms": None
        }
    
    # Calculer latence approximative
    import time
    last_pong = ws_client.last_pong
    current_time = time.time()
    latency_ms = (current_time - last_pong) * 1000
    
    return {
        "connected": True,
        "latency_ms": round(latency_ms, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "pnl_live_api",
        "ws_connected": ws_connected,
        "active_ws_clients": len(active_ws_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


# ==============================================================================
# WEBSOCKET ENDPOINT
# ==============================================================================

@app.websocket("/ws/pnl")
async def websocket_pnl(websocket: WebSocket):
    """
    WebSocket endpoint pour updates PnL temps réel
    
    Le client reçoit:
    - Updates positions (chaque changement)
    - Updates portfolio (toutes les 10s)
    - Updates balance (changements wallet)
    """
    await websocket.accept()
    active_ws_connections.append(websocket)
    
    try:
        # Message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "message": "PnL Live WebSocket connecté",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Boucle de maintien + envoi périodique
        while True:
            # Envoyer portfolio update toutes les 10s
            await asyncio.sleep(10)
            
            if ws_client:
                positions_dict = ws_client.get_positions()
                
                if positions_dict:
                    positions = [
                        convert_ws_position_to_dataclass(pos)
                        for pos in positions_dict.values()
                    ]
                    
                    portfolio = pnl_engine.calculate_portfolio_pnl(positions)
                    
                    await websocket.send_json({
                        "type": "portfolio_update",
                        "data": portfolio,
                        "timestamp": datetime.utcnow().isoformat()
                    })
    
    except WebSocketDisconnect:
        active_ws_connections.remove(websocket)
        print(f"Client WebSocket déconnecté. Restants: {len(active_ws_connections)}")
    
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        if websocket in active_ws_connections:
            active_ws_connections.remove(websocket)


# ==============================================================================
# MAIN (pour test)
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════╗
    ║  SmartOrder PRO - PnL Live API          ║
    ║  Port: 8556                             ║
    ╚══════════════════════════════════════════╝
    
    📊 Endpoints REST:
       - GET  /api/pnl/positions
       - GET  /api/pnl/portfolio
       - GET  /api/pnl/statistics
       - GET  /api/pnl/daily
       - GET  /api/pnl/latency
    
    🔌 WebSocket:
       - WS   /ws/pnl
    
    🌐 Dashboard:
       - http://localhost:8556
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8556,
        log_level="info"
    )
