#!/usr/bin/env python3
"""
🌐 SAFELOGIC SmartOrder PRO — API PNL Live
Endpoints FastAPI pour WebSocket PNL temps réel
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime

# Import WebSocket PNL
try:
    from core.pnl_websocket import get_live_pnl, get_position_pnl, start_websocket_pnl
except ImportError:
    # Fallback si module pas encore chargé
    def get_live_pnl(): return {"error": "WebSocket not initialized"}
    def get_position_pnl(symbol): return None
    def start_websocket_pnl(): pass

router = APIRouter(prefix="/api/pnl", tags=["PNL Live"])

# Auto-start WebSocket au load du module
try:
    start_websocket_pnl()
except Exception as e:
    print(f"⚠️ WebSocket PNL auto-start failed: {e}")

@router.get("/live")
async def get_pnl_live():
    """
    📡 PNL Live WebSocket
    
    Retourne toutes les positions avec PNL temps réel
    
    Response:
    {
        "success": true,
        "data": {
            "positions": {
                "BTCUSDT": {
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "size": 0.001,
                    "entry_price": 67000,
                    "last_price": 67500,
                    "pnl_pct": 1.49,
                    "pnl_usdt": 0.50,
                    "leverage": 2,
                    "timestamp": "2025-10-26T00:30:00"
                }
            },
            "latency_ms": 120,
            "status": "connected",
            "last_update": "00:30:15"
        }
    }
    """
    try:
        pnl_data = get_live_pnl()
        
        return {
            "success": True,
            "data": pnl_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live/{symbol}")
async def get_pnl_symbol(symbol: str):
    """
    📈 PNL d'un symbole spécifique
    
    Args:
        symbol: BTCUSDT, ETHUSDT, etc.
    
    Response:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "pnl_pct": 1.49,
            "pnl_usdt": 0.50,
            ...
        }
    }
    """
    try:
        pos = get_position_pnl(symbol.upper())
        
        if pos is None:
            return {
                "success": False,
                "error": f"Position {symbol} not found",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "data": pos,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latency")
async def get_latency():
    """
    ⏱️ Latence WebSocket
    
    Response:
    {
        "latency_ms": 120,
        "status": "connected"
    }
    """
    try:
        pnl_data = get_live_pnl()
        
        return {
            "latency_ms": pnl_data.get("latency_ms", 0),
            "status": pnl_data.get("status", "unknown"),
            "last_update": pnl_data.get("last_update"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_pnl_summary():
    """
    📊 Résumé PNL global
    
    Response:
    {
        "total_positions": 3,
        "total_pnl_usdt": 12.50,
        "avg_pnl_pct": 2.15,
        "winning_positions": 2,
        "losing_positions": 1
    }
    """
    try:
        pnl_data = get_live_pnl()
        positions = pnl_data.get("positions", {})
        
        if not positions:
            return {
                "success": True,
                "data": {
                    "total_positions": 0,
                    "total_pnl_usdt": 0,
                    "avg_pnl_pct": 0,
                    "winning_positions": 0,
                    "losing_positions": 0
                }
            }
        
        # Calculs
        total_pnl_usdt = sum(p["pnl_usdt"] for p in positions.values())
        avg_pnl_pct = sum(p["pnl_pct"] for p in positions.values()) / len(positions)
        winning = sum(1 for p in positions.values() if p["pnl_usdt"] > 0)
        losing = sum(1 for p in positions.values() if p["pnl_usdt"] < 0)
        
        return {
            "success": True,
            "data": {
                "total_positions": len(positions),
                "total_pnl_usdt": round(total_pnl_usdt, 2),
                "avg_pnl_pct": round(avg_pnl_pct, 2),
                "winning_positions": winning,
                "losing_positions": losing,
                "status": pnl_data.get("status"),
                "latency_ms": pnl_data.get("latency_ms")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
async def restart_websocket():
    """
    🔄 Redémarre WebSocket PNL
    
    Utile si connexion perdue
    """
    try:
        # Stop + restart
        start_websocket_pnl()
        
        return {
            "success": True,
            "message": "WebSocket PNL restarted",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ["router"]
