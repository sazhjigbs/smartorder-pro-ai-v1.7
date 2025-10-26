#!/usr/bin/env python3
"""
🧠 SAFELOGIC SmartOrder PRO — API Signal Memory
Endpoints FastAPI pour Trust Score historique
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

# Import Signal Memory
try:
    from ai.signal_memory import get_trust_score, get_recent_signals, get_stats, add_signal, close_signal
except ImportError:
    def get_trust_score(*args, **kwargs): return {"error": "Not initialized"}
    def get_recent_signals(*args, **kwargs): return []
    def get_stats(): return {}
    def add_signal(*args, **kwargs): return -1
    def close_signal(*args, **kwargs): return False

router = APIRouter(prefix="/api/signal", tags=["Signal Memory"])

@router.get("/trust/{symbol}")
async def get_signal_trust(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="15m, 1h, 4h, etc."),
    last_n: int = Query(50, description="Last N signals")
):
    """
    🎯 Trust Score d'un symbole
    
    Calcule fiabilité basée sur historique
    
    Args:
        symbol: BTCUSDT, ETHUSDT, etc.
        timeframe: 15m, 1h, 4h (optionnel)
        last_n: Nombre de signaux récents (défaut 50)
    
    Response:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "trust_score": 78.5,
            "total_signals": 50,
            "wins": 35,
            "losses": 12,
            "neutrals": 3,
            "win_rate": 70.0,
            "avg_pnl_pct": 1.25
        }
    }
    """
    try:
        trust_data = get_trust_score(symbol.upper(), timeframe, last_n)
        
        return {
            "success": True,
            "data": trust_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}")
async def get_signal_history(
    symbol: str,
    limit: int = Query(20, description="Number of signals")
):
    """
    📜 Historique signaux d'un symbole
    
    Response:
    {
        "success": true,
        "data": [
            {
                "id": 123,
                "symbol": "BTCUSDT",
                "signal_type": "LONG",
                "entry_price": 67000,
                "exit_price": 67500,
                "pnl_pct": 1.49,
                "outcome": "WIN",
                "timestamp": 1729901234
            }
        ]
    }
    """
    try:
        signals = get_recent_signals(symbol.upper(), limit)
        
        return {
            "success": True,
            "data": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_all_history(
    limit: int = Query(50, description="Number of signals")
):
    """
    📜 Historique global tous symboles
    """
    try:
        signals = get_recent_signals(None, limit)
        
        return {
            "success": True,
            "data": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_signal_stats():
    """
    📊 Statistiques globales
    
    Response:
    {
        "total_signals": 500,
        "wins": 350,
        "losses": 120,
        "pending": 30,
        "win_rate": 70.0,
        "avg_pnl_pct": 1.25,
        "total_pnl_usdt": 1250.50
    }
    """
    try:
        stats = get_stats()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_new_signal(
    symbol: str,
    timeframe: str,
    signal_type: str,  # BUY, SELL, LONG, SHORT
    entry_price: float,
    confidence: float = 75.0,
    leverage: int = 1
):
    """
    ➕ Ajoute nouveau signal
    
    Request:
    {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "signal_type": "LONG",
        "entry_price": 67000,
        "confidence": 85.0,
        "leverage": 2
    }
    
    Response:
    {
        "success": true,
        "signal_id": 123
    }
    """
    try:
        signal_id = add_signal(
            symbol.upper(),
            timeframe,
            signal_type.upper(),
            entry_price,
            confidence,
            leverage
        )
        
        if signal_id < 0:
            raise HTTPException(status_code=500, detail="Failed to add signal")
        
        return {
            "success": True,
            "signal_id": signal_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/close/{signal_id}")
async def close_existing_signal(
    signal_id: int,
    exit_price: float,
    pnl_usdt: Optional[float] = None
):
    """
    ✅ Ferme un signal avec résultat
    
    Request:
    {
        "exit_price": 67500,
        "pnl_usdt": 5.0
    }
    
    Response:
    {
        "success": true,
        "message": "Signal closed"
    }
    """
    try:
        success = close_signal(signal_id, exit_price, pnl_usdt)
        
        if not success:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return {
            "success": True,
            "message": "Signal closed",
            "signal_id": signal_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top")
async def get_top_signals(
    limit: int = Query(10, description="Top N symbols")
):
    """
    🏆 Top symboles par Trust Score
    """
    try:
        # Récupère tous symboles uniques
        from ai.signal_memory import get_memory
        mem = get_memory()
        
        cursor = mem.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol FROM signals_history
            WHERE outcome IN ('WIN', 'LOSS', 'NEUTRAL')
        """)
        
        symbols = [row[0] for row in cursor.fetchall()]
        
        # Calcule trust score pour chaque
        results = []
        for symbol in symbols:
            trust = get_trust_score(symbol, None, 50)
            if trust.get("status") == "ok":
                results.append(trust)
        
        # Trie par trust_score
        results.sort(key=lambda x: x["trust_score"], reverse=True)
        
        return {
            "success": True,
            "data": results[:limit],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ["router"]
