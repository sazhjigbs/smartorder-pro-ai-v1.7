#!/usr/bin/env python3
"""
SmartOrder PRO - Signal Memory API
===================================
API REST pour Signal Memory et Trust Score

Endpoints:
- GET /api/signals/recent - Signaux récents
- GET /api/signals/stats - Statistiques par stratégie
- GET /api/signals/trust - Trust Score
- GET /api/signals/chart - Chart performance
- POST /api/signals/record - Enregistrer signal
- POST /api/signals/result - Enregistrer résultat

Usage:
    uvicorn api.api_signal_memory:app --host 0.0.0.0 --port 8557
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.signal_memory import SignalMemory

# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title="SmartOrder PRO - Signal Memory API",
    description="API pour mémoire des signaux et Trust Score",
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

signal_memory = SignalMemory()

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class SignalCreate(BaseModel):
    """Modèle pour créer un signal"""
    symbol: str
    timeframe: str
    side: str  # BUY or SELL
    confidence: float  # 0-1
    strategy: str
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    notes: Optional[str] = None


class SignalResult(BaseModel):
    """Modèle pour résultat d'un signal"""
    signal_id: int
    success: bool
    pnl: float
    exit_price: float
    notes: Optional[str] = None


class SignalExecuted(BaseModel):
    """Modèle pour marquer signal exécuté"""
    signal_id: int
    entry_price: float


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Page d'accueil API"""
    return {
        "service": "SmartOrder PRO - Signal Memory API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "recent_signals": "/api/signals/recent",
            "strategy_stats": "/api/signals/stats",
            "trust_score": "/api/signals/trust",
            "performance_chart": "/api/signals/chart",
            "record_signal": "POST /api/signals/record",
            "mark_executed": "POST /api/signals/executed",
            "record_result": "POST /api/signals/result"
        }
    }


@app.get("/api/signals/recent")
async def get_recent_signals(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    limit: int = Query(50, ge=1, le=500, description="Nombre de signaux")
):
    """
    Récupère les signaux récents
    
    Args:
        symbol: Filtrer par symbole (optionnel)
        limit: Nombre max de signaux (1-500)
    
    Returns:
        Liste des signaux récents
    """
    try:
        signals = signal_memory.get_recent_signals(symbol=symbol, limit=limit)
        
        return {
            "signals": signals,
            "count": len(signals),
            "filtered_by_symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/stats")
async def get_strategy_stats(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    timeframe: Optional[str] = Query(None, description="Filtrer par timeframe"),
    strategy: Optional[str] = Query(None, description="Filtrer par stratégie"),
    min_trades: int = Query(0, ge=0, description="Minimum de trades")
):
    """
    Récupère statistiques des stratégies
    
    Args:
        symbol: Filtrer par symbole
        timeframe: Filtrer par timeframe
        strategy: Filtrer par stratégie
        min_trades: Minimum de trades fermés
    
    Returns:
        Liste des statistiques triées par Trust Score
    """
    try:
        stats = signal_memory.get_strategy_stats(
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy,
            min_trades=min_trades
        )
        
        return {
            "stats": stats,
            "count": len(stats),
            "filters": {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": strategy,
                "min_trades": min_trades
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/trust")
async def get_trust_score(
    symbol: str = Query(..., description="Symbole (ex: BTCUSDT)"),
    timeframe: str = Query(..., description="Timeframe (ex: 15m, 1h)"),
    strategy: str = Query(..., description="Stratégie (ex: momentum)")
):
    """
    Récupère le Trust Score d'une stratégie
    
    Args:
        symbol: Symbole
        timeframe: Timeframe
        strategy: Stratégie
    
    Returns:
        Trust Score (0-1) et détails
    """
    try:
        trust_score = signal_memory.get_trust_score(symbol, timeframe, strategy)
        
        # Récupérer stats complètes
        stats = signal_memory.get_strategy_stats(
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy
        )
        
        if stats:
            stat = stats[0]
        else:
            stat = {
                "total_signals": 0,
                "total_closed": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0
            }
        
        # Interprétation du score
        if trust_score >= 0.8:
            rating = "Excellent 🌟"
        elif trust_score >= 0.7:
            rating = "Très bon ✅"
        elif trust_score >= 0.6:
            rating = "Bon 👍"
        elif trust_score >= 0.5:
            rating = "Moyen ⚠️"
        else:
            rating = "Faible ❌"
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "strategy": strategy,
            "trust_score": trust_score,
            "rating": rating,
            "details": stat,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/chart")
async def get_performance_chart(
    symbol: str = Query(..., description="Symbole"),
    days: int = Query(30, ge=1, le=365, description="Nombre de jours")
):
    """
    Génère données pour chart de performance
    
    Args:
        symbol: Symbole
        days: Nombre de jours (1-365)
    
    Returns:
        Données chart: dates, PnL, win rate
    """
    try:
        chart_data = signal_memory.get_performance_chart(symbol, days)
        
        return {
            "symbol": symbol,
            "days": days,
            "chart": chart_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/record")
async def record_signal(signal: SignalCreate):
    """
    Enregistre un nouveau signal
    
    Args:
        signal: Données du signal
    
    Returns:
        ID du signal créé
    """
    try:
        signal_id = signal_memory.record_signal(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            side=signal.side,
            confidence=signal.confidence,
            strategy=signal.strategy,
            entry_price=signal.entry_price,
            target_price=signal.target_price,
            stop_loss=signal.stop_loss,
            notes=signal.notes
        )
        
        return {
            "success": True,
            "signal_id": signal_id,
            "message": f"Signal {signal.strategy} {signal.side} {signal.symbol} enregistré",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/executed")
async def mark_signal_executed(execution: SignalExecuted):
    """
    Marque un signal comme exécuté
    
    Args:
        execution: Signal ID + prix d'entrée réel
    
    Returns:
        Confirmation
    """
    try:
        signal_memory.mark_executed(
            signal_id=execution.signal_id,
            entry_price=execution.entry_price
        )
        
        return {
            "success": True,
            "signal_id": execution.signal_id,
            "entry_price": execution.entry_price,
            "message": f"Signal {execution.signal_id} marqué exécuté",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/result")
async def record_signal_result(result: SignalResult):
    """
    Enregistre le résultat d'un signal
    
    Args:
        result: Signal ID + résultat (win/loss, PnL, etc.)
    
    Returns:
        Confirmation + Trust Score mis à jour
    """
    try:
        signal_memory.record_result(
            signal_id=result.signal_id,
            success=result.success,
            pnl=result.pnl,
            exit_price=result.exit_price,
            notes=result.notes
        )
        
        # Récupérer signal pour Trust Score
        signals = signal_memory.get_recent_signals(limit=1)
        if signals:
            sig = signals[0]
            trust = signal_memory.get_trust_score(
                sig["symbol"],
                sig["timeframe"],
                sig["strategy"]
            )
        else:
            trust = None
        
        status = "WIN ✅" if result.success else "LOSS ❌"
        
        return {
            "success": True,
            "signal_id": result.signal_id,
            "result": status,
            "pnl": result.pnl,
            "trust_score_updated": trust,
            "message": f"Signal {result.signal_id}: {status} PnL=${result.pnl:.2f}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/summary")
async def get_summary():
    """
    Résumé global de la mémoire
    
    Returns:
        Statistiques globales
    """
    try:
        # Toutes les stats
        all_stats = signal_memory.get_strategy_stats(min_trades=0)
        
        # Récents signaux
        recent = signal_memory.get_recent_signals(limit=10)
        
        # Calculer totaux
        total_signals = sum(s["total_signals"] for s in all_stats)
        total_closed = sum(s["total_closed"] for s in all_stats)
        total_wins = sum(s["wins"] for s in all_stats)
        total_losses = sum(s["losses"] for s in all_stats)
        total_pnl = sum(s["total_pnl"] for s in all_stats)
        
        global_win_rate = (total_wins / total_closed * 100) if total_closed > 0 else 0
        
        # Meilleure stratégie
        best_strategy = max(all_stats, key=lambda x: x["trust_score"]) if all_stats else None
        
        return {
            "global": {
                "total_signals": total_signals,
                "total_closed": total_closed,
                "total_wins": total_wins,
                "total_losses": total_losses,
                "global_win_rate": round(global_win_rate, 2),
                "total_pnl": round(total_pnl, 2)
            },
            "best_strategy": best_strategy,
            "strategies_count": len(all_stats),
            "recent_signals_count": len(recent),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "signal_memory_api",
        "database": "signal_memory.db",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==============================================================================
# SHUTDOWN
# ==============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Ferme la connexion DB"""
    signal_memory.close()
    print("👋 Signal Memory API arrêtée")


# ==============================================================================
# MAIN (pour test)
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════╗
    ║  SmartOrder PRO - Signal Memory API     ║
    ║  Port: 8557                             ║
    ╚══════════════════════════════════════════╝
    
    📊 Endpoints REST:
       - GET  /api/signals/recent
       - GET  /api/signals/stats
       - GET  /api/signals/trust
       - GET  /api/signals/chart
       - GET  /api/signals/summary
       - POST /api/signals/record
       - POST /api/signals/executed
       - POST /api/signals/result
    
    🌐 Dashboard:
       - http://localhost:8557
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8557,
        log_level="info"
    )
