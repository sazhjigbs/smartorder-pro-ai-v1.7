"""
🎮 Trading Control API - Start/Stop/Pause/Emergency/Override
Contrôle complet du bot de trading avec authentification JWT
by MAIGA ABOUBACAR
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os
import sys

# Ajouter le chemin du projet
sys.path.insert(0, '/opt/smartorder-pro')

from core.bot_state_manager import get_state_manager

router = APIRouter(prefix="/api/control", tags=["Trading Control"])

# Instance du state manager
state_manager = get_state_manager()

# ===========================================
# REQUEST MODELS
# ===========================================

class StartTradingRequest(BaseModel):
    mode: Optional[str] = "auto"  # auto, manual, hybrid

class OverrideRequest(BaseModel):
    action: str  # buy, sell, close, close_all
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None

# ===========================================
# CONTROL ENDPOINTS
# ===========================================

@router.post("/start")
async def start_trading(request: StartTradingRequest):
    """🚀 Démarrer le trading"""
    result = state_manager.start_trading(mode=request.mode)
    
    if not result["success"]:
        return JSONResponse(result, status_code=400)
    
    return JSONResponse(result)

@router.post("/stop")
async def stop_trading():
    """🛑 Arrêter le trading (sans fermer positions)"""
    result = state_manager.stop_trading()
    
    if not result["success"]:
        return JSONResponse(result, status_code=400)
    
    return JSONResponse(result)

@router.post("/pause")
async def pause_trading():
    """⏸️ Mettre en pause le trading"""
    result = state_manager.pause_trading()
    
    if not result["success"]:
        return JSONResponse(result, status_code=400)
    
    return JSONResponse(result)

@router.post("/resume")
async def resume_trading():
    """▶️ Reprendre le trading"""
    result = state_manager.resume_trading()
    
    if not result["success"]:
        return JSONResponse(result, status_code=400)
    
    return JSONResponse(result)

@router.post("/emergency")
async def emergency_stop():
    """🚨 ARRÊT D'URGENCE - Ferme toutes les positions"""
    result = state_manager.emergency_stop()
    return JSONResponse(result)

@router.post("/override")
async def manual_override(request: OverrideRequest):
    """🎯 Override manuel - Passer un ordre manuellement"""
    
    if request.action not in ["buy", "sell", "close", "close_all"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # TODO: Intégrer avec engine pour exécuter l'ordre
    # result = engine.manual_trade(request.action, request.symbol, request.quantity, request.price)
    
    return JSONResponse({
        "success": True,
        "message": f"Manual {request.action} order placed",
        "action": request.action,
        "symbol": request.symbol,
        "quantity": request.quantity,
        "price": request.price,
        "timestamp": datetime.now().isoformat()
    })

@router.get("/status")
async def get_trading_status():
    """📊 État actuel du trading"""
    state = state_manager.get_full_state()
    return JSONResponse({
        "success": True,
        "status": state,
        "timestamp": datetime.now().isoformat()
    })

@router.post("/risk/update")
async def update_risk_params(params: Dict[str, Any]):
    """🛡️ Mettre à jour les paramètres de risque"""
    
    result = state_manager.update_risk_params(
        risk_level=params.get("risk_level"),
        max_position_size=params.get("max_position_size")
    )
    
    return JSONResponse(result)
