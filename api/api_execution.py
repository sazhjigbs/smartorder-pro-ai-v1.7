#!/usr/bin/env python3
"""
⚡ SAFELOGIC SmartOrder PRO — Smart Execution API
Endpoints pour gestion avancée des ordres
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from core.execution_engine import get_engine
from core.logger import logger

router = APIRouter(prefix="/api/execution", tags=["Smart Execution"])

# ========== MODELS ==========

class SplitOrderRequest(BaseModel):
    """Requête pour split order"""
    symbol: str = Field(..., example="BTCUSDT")
    side: str = Field(..., example="BUY")
    total_quantity: float = Field(..., gt=0, example=0.003)
    price: float = Field(..., gt=0, example=67000)
    num_splits: int = Field(default=3, ge=2, le=10, example=3)
    delay_seconds: int = Field(default=2, ge=1, le=60, example=2)

class PartialCloseRequest(BaseModel):
    """Requête fermeture partielle"""
    symbol: str = Field(..., example="BTCUSDT")
    position_size: float = Field(..., gt=0, example=0.01)
    close_percentage: float = Field(..., gt=0, le=100, example=50)
    current_price: float = Field(..., gt=0, example=67500)

class TrailingStopRequest(BaseModel):
    """Requête trailing stop"""
    symbol: str = Field(..., example="BTCUSDT")
    side: str = Field(..., example="LONG")
    entry_price: float = Field(..., gt=0, example=67000)
    trail_percent: float = Field(..., gt=0, le=10, example=2.0)
    current_price: Optional[float] = Field(None, gt=0, example=67500)

class TrailingStopUpdate(BaseModel):
    """Update prix trailing stop"""
    symbol: str = Field(..., example="BTCUSDT")
    current_price: float = Field(..., gt=0, example=68000)

# ========== ENDPOINTS ==========

@router.post("/split-order", summary="📊 Split Order")
async def create_split_order(request: SplitOrderRequest):
    """
    Split un gros ordre en plusieurs petits ordres progressifs
    
    - **symbol**: Paire de trading (BTCUSDT, ETHUSDT, etc.)
    - **side**: BUY ou SELL
    - **total_quantity**: Quantité totale à diviser
    - **price**: Prix limite
    - **num_splits**: Nombre de divisions (2-10)
    - **delay_seconds**: Délai entre chaque ordre (1-60s)
    
    Retourne la liste des ordres splits prêts à être exécutés
    """
    try:
        engine = get_engine()
        
        splits = engine.split_order(
            symbol=request.symbol,
            side=request.side,
            total_quantity=request.total_quantity,
            price=request.price,
            num_splits=request.num_splits,
            delay_seconds=request.delay_seconds
        )
        
        if not splits:
            raise HTTPException(status_code=500, detail="Failed to create split orders")
        
        return {
            "success": True,
            "symbol": request.symbol,
            "total_quantity": request.total_quantity,
            "num_splits": len(splits),
            "splits": splits,
            "message": f"Split order created: {request.total_quantity} {request.symbol} → {len(splits)} orders"
        }
        
    except Exception as e:
        logger.error(f"Split order API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/partial-close", summary="✂️ Partial Close")
async def close_partial_position(request: PartialCloseRequest):
    """
    Ferme partiellement une position
    
    - **symbol**: Paire de trading
    - **position_size**: Taille totale de la position
    - **close_percentage**: % à fermer (1-100%)
    - **current_price**: Prix actuel de fermeture
    
    Retourne les détails de la fermeture partielle
    """
    try:
        engine = get_engine()
        
        partial_info = engine.partial_close(
            symbol=request.symbol,
            position_size=request.position_size,
            close_percentage=request.close_percentage,
            current_price=request.current_price
        )
        
        if "error" in partial_info:
            raise HTTPException(status_code=500, detail=partial_info["error"])
        
        return {
            "success": True,
            "partial_close": partial_info,
            "message": f"Closed {request.close_percentage}% of {request.symbol} position"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partial close API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trailing-stop/setup", summary="🎯 Setup Trailing Stop")
async def setup_trailing(request: TrailingStopRequest):
    """
    Configure un trailing stop-loss dynamique
    
    - **symbol**: Paire de trading
    - **side**: LONG ou SHORT
    - **entry_price**: Prix d'entrée de la position
    - **trail_percent**: % de trailing (ex: 2.0 pour 2%)
    - **current_price**: Prix actuel (optionnel)
    
    Le stop suivra le prix et se déclenchera si le prix recule de trail_percent%
    """
    try:
        engine = get_engine()
        
        trail_config = engine.setup_trailing_stop(
            symbol=request.symbol,
            side=request.side,
            entry_price=request.entry_price,
            trail_percent=request.trail_percent,
            current_price=request.current_price
        )
        
        if "error" in trail_config:
            raise HTTPException(status_code=500, detail=trail_config["error"])
        
        return {
            "success": True,
            "trailing_stop": trail_config,
            "message": f"Trailing stop setup for {request.symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trailing stop setup API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trailing-stop/update", summary="🔄 Update Trailing Stop")
async def update_trailing(request: TrailingStopUpdate):
    """
    Met à jour un trailing stop avec nouveau prix
    
    - **symbol**: Paire de trading
    - **current_price**: Nouveau prix actuel
    
    Retourne si le stop a été déclenché et la config mise à jour
    """
    try:
        engine = get_engine()
        
        triggered, trail_config = engine.update_trailing_stop(
            symbol=request.symbol,
            current_price=request.current_price
        )
        
        if "error" in trail_config:
            raise HTTPException(status_code=404, detail=trail_config["error"])
        
        return {
            "success": True,
            "triggered": triggered,
            "trailing_stop": trail_config,
            "message": "Trailing stop triggered!" if triggered else "Trailing stop updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trailing stop update API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trailing-stop/{symbol}", summary="📊 Get Trailing Stop Status")
async def get_trailing_status(symbol: str):
    """
    Récupère le status d'un trailing stop actif
    
    - **symbol**: Paire de trading
    
    Retourne la configuration et l'état actuel du trailing stop
    """
    try:
        engine = get_engine()
        
        trail_config = engine.get_trailing_stop_status(symbol)
        
        if trail_config is None:
            raise HTTPException(status_code=404, detail=f"No trailing stop found for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "trailing_stop": trail_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get trailing stop API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trailing-stop", summary="📋 Get All Trailing Stops")
async def get_all_trailing():
    """
    Récupère tous les trailing stops actifs
    
    Retourne la liste complète des trailing stops configurés et actifs
    """
    try:
        engine = get_engine()
        
        all_trails = engine.get_all_trailing_stops()
        
        return {
            "success": True,
            "count": len(all_trails),
            "trailing_stops": all_trails
        }
        
    except Exception as e:
        logger.error(f"Get all trailing stops API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trailing-stop/{symbol}", summary="❌ Cancel Trailing Stop")
async def cancel_trailing(symbol: str):
    """
    Annule un trailing stop actif
    
    - **symbol**: Paire de trading
    
    Désactive le trailing stop pour cette paire
    """
    try:
        engine = get_engine()
        
        success = engine.cancel_trailing_stop(symbol)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"No trailing stop found for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "message": f"Trailing stop cancelled for {symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel trailing stop API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@router.get("/health", summary="💚 Health Check")
async def health_check():
    """Vérifie que l'API Execution Engine est opérationnelle"""
    try:
        engine = get_engine()
        return {
            "status": "healthy",
            "engine": "SmartExecutionEngine",
            "active_trailing_stops": len(engine.get_all_trailing_stops()),
            "active_split_orders": len(engine.split_orders)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Export router
__all__ = ["router"]
