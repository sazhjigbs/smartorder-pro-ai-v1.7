#!/usr/bin/env python3
"""
SmartOrder PRO - Smart Execution API
=====================================
API REST pour exécution intelligente des ordres

Endpoints:
- POST /api/execution/split - Split order
- POST /api/execution/partial-close - Partial close
- POST /api/execution/trailing-stop - Trailing stop-loss
- POST /api/execution/trailing-tp - Trailing take-profit
- POST /api/execution/breakeven - Move to break-even
- POST /api/execution/pyramid - Pyramid in
- GET /api/execution/trailing-stops - Active trailing stops
- GET /api/execution/stats - Statistics

Usage:
    uvicorn api.api_execution_smart:app --host 0.0.0.0 --port 8558
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.execution_smart import SmartExecutor

# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title="SmartOrder PRO - Smart Execution API",
    description="API pour exécution intelligente des ordres",
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

smart_executor = SmartExecutor()

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class SplitOrderRequest(BaseModel):
    """Requête split order"""
    symbol: str = Field(..., example="BTCUSDT")
    side: str = Field(..., example="BUY")
    total_quantity: float = Field(..., example=0.3)
    num_splits: int = Field(3, ge=2, le=10, example=3)
    price_levels: Optional[List[float]] = None
    time_delay_seconds: int = Field(5, ge=0, le=60, example=5)


class PartialCloseRequest(BaseModel):
    """Requête partial close"""
    symbol: str = Field(..., example="BTCUSDT")
    percent: float = Field(..., ge=1, le=100, example=50)
    current_position_size: Optional[float] = None


class TrailingStopRequest(BaseModel):
    """Requête trailing stop"""
    symbol: str = Field(..., example="BTCUSDT")
    trail_percent: float = Field(..., ge=0.1, le=50, example=2.0)
    initial_price: Optional[float] = None
    side: str = Field("LONG", example="LONG")


class TrailingTPRequest(BaseModel):
    """Requête trailing take-profit"""
    symbol: str = Field(..., example="BTCUSDT")
    trail_percent: float = Field(..., ge=0.1, le=20, example=1.0)
    activation_percent: float = Field(..., ge=1, le=100, example=5.0)
    initial_price: Optional[float] = None
    side: str = Field("LONG", example="LONG")


class BreakevenRequest(BaseModel):
    """Requête break-even"""
    symbol: str = Field(..., example="BTCUSDT")
    entry_price: float = Field(..., example=67000)
    current_price: float = Field(..., example=68500)
    min_profit_percent: float = Field(2.0, ge=0.5, le=20, example=2.0)


class PyramidRequest(BaseModel):
    """Requête pyramiding"""
    symbol: str = Field(..., example="BTCUSDT")
    side: str = Field(..., example="BUY")
    additional_quantity: float = Field(..., example=0.05)
    min_profit_percent: float = Field(3.0, ge=1, le=20, example=3.0)
    entry_price: Optional[float] = None
    current_price: Optional[float] = None


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Page d'accueil API"""
    return {
        "service": "SmartOrder PRO - Smart Execution API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Split Orders",
            "Partial Close",
            "Trailing Stop-Loss",
            "Trailing Take-Profit",
            "Break-even",
            "Pyramiding"
        ],
        "endpoints": {
            "split_order": "POST /api/execution/split",
            "partial_close": "POST /api/execution/partial-close",
            "trailing_stop": "POST /api/execution/trailing-stop",
            "trailing_tp": "POST /api/execution/trailing-tp",
            "breakeven": "POST /api/execution/breakeven",
            "pyramid": "POST /api/execution/pyramid",
            "active_trailing": "GET /api/execution/trailing-stops",
            "statistics": "GET /api/execution/stats"
        }
    }


@app.post("/api/execution/split")
async def split_order(request: SplitOrderRequest):
    """
    Split un ordre en plusieurs parties
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "total_quantity": 0.3,
            "num_splits": 3,
            "time_delay_seconds": 5
        }
        ```
    """
    try:
        result = smart_executor.split_order(
            symbol=request.symbol,
            side=request.side,
            total_quantity=request.total_quantity,
            num_splits=request.num_splits,
            price_levels=request.price_levels,
            time_delay_seconds=request.time_delay_seconds
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/partial-close")
async def partial_close(request: PartialCloseRequest):
    """
    Ferme partiellement une position
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "percent": 50,
            "current_position_size": 0.3
        }
        ```
    """
    try:
        result = smart_executor.partial_close(
            symbol=request.symbol,
            percent=request.percent,
            current_position_size=request.current_position_size
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/trailing-stop")
async def set_trailing_stop(request: TrailingStopRequest):
    """
    Active un trailing stop-loss
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "trail_percent": 2.0,
            "initial_price": 67000,
            "side": "LONG"
        }
        ```
    """
    try:
        result = smart_executor.set_trailing_stop(
            symbol=request.symbol,
            trail_percent=request.trail_percent,
            initial_price=request.initial_price,
            side=request.side
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/trailing-tp")
async def set_trailing_takeprofit(request: TrailingTPRequest):
    """
    Active un trailing take-profit
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "trail_percent": 1.0,
            "activation_percent": 5.0,
            "initial_price": 67000,
            "side": "LONG"
        }
        ```
    """
    try:
        result = smart_executor.set_trailing_takeprofit(
            symbol=request.symbol,
            trail_percent=request.trail_percent,
            activation_percent=request.activation_percent,
            initial_price=request.initial_price,
            side=request.side
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/breakeven")
async def move_to_breakeven(request: BreakevenRequest):
    """
    Déplace stop-loss au prix d'entrée (break-even)
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "entry_price": 67000,
            "current_price": 68500,
            "min_profit_percent": 2.0
        }
        ```
    """
    try:
        result = smart_executor.move_to_breakeven(
            symbol=request.symbol,
            entry_price=request.entry_price,
            current_price=request.current_price,
            min_profit_percent=request.min_profit_percent
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/pyramid")
async def pyramid_in(request: PyramidRequest):
    """
    Ajoute à une position gagnante (pyramiding)
    
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "additional_quantity": 0.05,
            "min_profit_percent": 3.0,
            "entry_price": 67000,
            "current_price": 69000
        }
        ```
    """
    try:
        result = smart_executor.pyramid_in(
            symbol=request.symbol,
            side=request.side,
            additional_quantity=request.additional_quantity,
            min_profit_percent=request.min_profit_percent,
            entry_price=request.entry_price,
            current_price=request.current_price
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/execution/trailing-stops")
async def get_active_trailing_stops():
    """
    Récupère tous les trailing stops actifs
    
    Returns:
        Liste des trailing stops avec leur configuration
    """
    try:
        active_stops = smart_executor.get_active_trailing_stops()
        
        return {
            "active_stops": active_stops,
            "count": len(active_stops),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/execution/stats")
async def get_statistics():
    """
    Statistiques du Smart Executor
    
    Returns:
        Compteurs des différentes opérations
    """
    try:
        stats = smart_executor.get_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/execution/quick-actions")
async def get_quick_actions():
    """
    Retourne les quick actions disponibles
    
    Returns:
        Actions rapides prédéfinies
    """
    return {
        "quick_actions": [
            {
                "name": "Close 25%",
                "description": "Fermer 25% de la position",
                "action": "partial_close",
                "params": {"percent": 25}
            },
            {
                "name": "Close 50%",
                "description": "Fermer 50% de la position",
                "action": "partial_close",
                "params": {"percent": 50}
            },
            {
                "name": "Close 75%",
                "description": "Fermer 75% de la position",
                "action": "partial_close",
                "params": {"percent": 75}
            },
            {
                "name": "Close 100%",
                "description": "Fermer toute la position",
                "action": "partial_close",
                "params": {"percent": 100}
            },
            {
                "name": "Trailing Stop 2%",
                "description": "Activer trailing stop 2%",
                "action": "trailing_stop",
                "params": {"trail_percent": 2.0}
            },
            {
                "name": "Trailing Stop 3%",
                "description": "Activer trailing stop 3%",
                "action": "trailing_stop",
                "params": {"trail_percent": 3.0}
            },
            {
                "name": "Break-even",
                "description": "Déplacer SL au prix d'entrée",
                "action": "breakeven",
                "params": {"min_profit_percent": 2.0}
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "smart_execution_api",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==============================================================================
# MAIN (pour test)
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════╗
    ║  SmartOrder PRO - Smart Execution API   ║
    ║  Port: 8558                             ║
    ╚══════════════════════════════════════════╝
    
    🎯 Features:
       - Split Orders
       - Partial Close (25%, 50%, 75%, 100%)
       - Trailing Stop-Loss
       - Trailing Take-Profit
       - Break-even
       - Pyramiding
    
    📊 Endpoints POST:
       - /api/execution/split
       - /api/execution/partial-close
       - /api/execution/trailing-stop
       - /api/execution/trailing-tp
       - /api/execution/breakeven
       - /api/execution/pyramid
    
    📊 Endpoints GET:
       - /api/execution/trailing-stops
       - /api/execution/stats
       - /api/execution/quick-actions
    
    🌐 Dashboard:
       - http://localhost:8558
       - http://localhost:8558/docs (Swagger)
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8558,
        log_level="info"
    )
