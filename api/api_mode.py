#!/usr/bin/env python3
"""
SmartOrder PRO - Mode Manager API
==================================
API REST pour gestion intelligente des modes de trading

Endpoints:
- GET  /api/mode/current           - Mode actuel
- POST /api/mode/set               - Changer de mode
- GET  /api/mode/suggestions       - Suggestions IA
- POST /api/mode/hybrid/suggest    - Créer suggestion (mode HYBRID)
- POST /api/mode/hybrid/validate   - Valider suggestion (mode HYBRID)
- GET  /api/mode/history           - Historique changements
- GET  /api/mode/strategies        - Liste des stratégies

Usage:
    uvicorn api.api_mode:app --host 0.0.0.0 --port 8560
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import mode manager
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.mode_manager import TradingModeManager

# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title="SmartOrder PRO - Mode Manager API",
    description="API pour gestion intelligente des modes de trading avec suggestions IA",
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

mode_manager = TradingModeManager()

# ==============================================================================
# MODELS PYDANTIC
# ==============================================================================

class SetModeRequest(BaseModel):
    """Requête pour changer de mode"""
    mode: str = Field(..., description="Nouveau mode (AUTO_SPOT, AUTO_FUTURES, MANUAL, HYBRID)")
    reason: Optional[str] = Field(None, description="Raison du changement")

class ValidateSuggestionRequest(BaseModel):
    """Requête pour valider une suggestion"""
    suggestion_id: str = Field(..., description="ID de la suggestion")
    approved: bool = Field(..., description="True = approuvé, False = rejeté")

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Page d'accueil API"""
    return {
        "service": "SmartOrder PRO - Mode Manager API",
        "version": "1.0.0",
        "status": "running",
        "current_mode": mode_manager.current_mode.value,
        "endpoints": {
            "current": "/api/mode/current",
            "set_mode": "/api/mode/set",
            "suggestions": "/api/mode/suggestions",
            "create_suggestion": "/api/mode/hybrid/suggest",
            "validate_suggestion": "/api/mode/hybrid/validate",
            "history": "/api/mode/history",
            "strategies": "/api/mode/strategies"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==============================================================================
# MODE ENDPOINTS
# ==============================================================================

@app.get("/api/mode/current")
async def get_current_mode():
    """
    Récupère le mode actuel
    
    Returns:
        Mode actuel avec description
    
    Example:
        ```json
        {
            "mode": "MANUAL",
            "description": "Contrôle manuel complet",
            "timestamp": "2025-01-26T13:00:00"
        }
        ```
    """
    try:
        current = mode_manager.get_current_mode()
        return {
            "success": True,
            "data": current
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/api/mode/set")
async def set_mode(request: SetModeRequest):
    """
    Change le mode de trading
    
    Modes disponibles:
    - AUTO_SPOT: Trading automatique spot uniquement
    - AUTO_FUTURES: Trading automatique futures uniquement
    - MANUAL: Contrôle manuel complet
    - HYBRID: IA suggère, vous validez
    
    Body:
        - mode: Nouveau mode
        - reason: Raison du changement (optionnel)
    
    Returns:
        Confirmation du changement
    
    Example Request:
        ```json
        {
            "mode": "HYBRID",
            "reason": "Marché volatil, préfère valider manuellement"
        }
        ```
    
    Example Response:
        ```json
        {
            "success": true,
            "data": {
                "previous_mode": "MANUAL",
                "new_mode": "HYBRID",
                "description": "IA suggère, vous validez",
                "reason": "Marché volatil, préfère valider manuellement",
                "timestamp": "2025-01-26T13:00:00"
            }
        }
        ```
    """
    try:
        result = mode_manager.set_mode(request.mode, request.reason)
        return {
            "success": result.get("success", True),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/mode/suggestions")
async def get_suggestions():
    """
    Récupère les suggestions IA basées sur le contexte marché
    
    L'IA analyse:
    - Fear & Greed Index
    - Volatilité
    - Régime de marché (BULL/BEAR/NEUTRAL/CHOPPY)
    - Score de risque global
    
    Et recommande:
    - Mode optimal
    - Stratégie de trading
    - Liste de coins à surveiller
    - Timeframes recommandés
    
    Returns:
        Suggestions complètes avec raisons détaillées
    
    Example Response:
        ```json
        {
            "success": true,
            "data": {
                "current_mode": "MANUAL",
                "suggested_mode": "AUTO_SPOT",
                "strategy": {
                    "name": "Momentum Long",
                    "description": "Tendance haussière forte - Favoriser positions LONG",
                    "risk_level": "MEDIUM",
                    "position_size_multiplier": 1.2,
                    "timeframes": ["15m", "1h", "4h"]
                },
                "confidence": 0.82,
                "reasons": [
                    "Marché BULL: Strong uptrend - Favor LONG positions",
                    "Fear & Greed: 65/100 (Greed)",
                    "Risk Score: 35/100",
                    "Stratégie recommandée: Tendance haussière forte",
                    "Mode suggéré: Trading automatique Spot uniquement"
                ],
                "recommended_coins": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
                "market_context": {...},
                "timestamp": "2025-01-26T13:00:00"
            }
        }
        ```
    """
    try:
        suggestions = mode_manager.get_suggestions()
        return {
            "success": True,
            "data": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/mode/strategies")
async def get_strategies():
    """
    Liste toutes les stratégies disponibles
    
    Returns:
        Configurations de toutes les stratégies
    
    Example Response:
        ```json
        {
            "success": true,
            "data": {
                "Momentum Long": {
                    "name": "Momentum Long",
                    "description": "Tendance haussière forte - Favoriser positions LONG",
                    "recommended_coins": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
                    "timeframes": ["15m", "1h", "4h"],
                    "risk_level": "MEDIUM",
                    "position_size_multiplier": 1.2
                },
                ...
            }
        }
        ```
    """
    try:
        strategies = {}
        for name, config in mode_manager.strategies.items():
            strategies[name] = {
                "name": config.name,
                "description": config.description,
                "recommended_coins": config.recommended_coins,
                "timeframes": config.timeframes,
                "risk_level": config.risk_level,
                "position_size_multiplier": config.position_size_multiplier
            }
        
        return {
            "success": True,
            "data": strategies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# ==============================================================================
# HYBRID MODE ENDPOINTS
# ==============================================================================

@app.post("/api/mode/hybrid/suggest")
async def create_suggestion():
    """
    Crée une nouvelle suggestion pour validation (mode HYBRID)
    
    Utilisé quand le bot est en mode HYBRID et que l'IA détecte
    une opportunité de trading. La suggestion est stockée en attente
    de validation par l'utilisateur.
    
    Returns:
        Suggestion créée avec ID unique
    
    Example Response:
        ```json
        {
            "success": true,
            "data": {
                "id": "SUGG_1706280000",
                "timestamp": "2025-01-26T13:00:00",
                "mode": "AUTO_SPOT",
                "strategy": "Momentum Long",
                "confidence": 0.85,
                "reasons": [...],
                "recommended_coins": ["BTCUSDT", "ETHUSDT"],
                "market_context": {...},
                "status": "PENDING"
            }
        }
        ```
    """
    try:
        suggestion = mode_manager.create_suggestion()
        
        return {
            "success": True,
            "data": {
                "id": suggestion.id,
                "timestamp": suggestion.timestamp,
                "mode": suggestion.mode,
                "strategy": suggestion.strategy,
                "confidence": suggestion.confidence,
                "reasons": suggestion.reasons,
                "recommended_coins": suggestion.recommended_coins,
                "market_context": suggestion.market_context,
                "status": suggestion.status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/api/mode/hybrid/validate")
async def validate_suggestion(request: ValidateSuggestionRequest):
    """
    Valide ou rejette une suggestion (mode HYBRID)
    
    L'utilisateur peut approuver ou rejeter une suggestion créée par l'IA.
    Si approuvée, le bot exécutera la stratégie recommandée.
    
    Body:
        - suggestion_id: ID de la suggestion à valider
        - approved: True = approuvé, False = rejeté
    
    Returns:
        Confirmation de la validation
    
    Example Request:
        ```json
        {
            "suggestion_id": "SUGG_1706280000",
            "approved": true
        }
        ```
    
    Example Response:
        ```json
        {
            "success": true,
            "data": {
                "suggestion_id": "SUGG_1706280000",
                "approved": true,
                "status": "APPROVED",
                "timestamp": "2025-01-26T13:05:00"
            }
        }
        ```
    """
    try:
        result = mode_manager.validate_suggestion(
            request.suggestion_id,
            request.approved
        )
        
        return {
            "success": result.get("success", True),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# ==============================================================================
# HISTORY ENDPOINTS
# ==============================================================================

@app.get("/api/mode/history")
async def get_mode_history(limit: int = 20):
    """
    Récupère l'historique des changements de mode
    
    Query params:
        - limit: Nombre max de résultats (défaut: 20)
    
    Returns:
        Historique des changements avec timestamps
    
    Example Response:
        ```json
        {
            "success": true,
            "data": [
                {
                    "previous_mode": "MANUAL",
                    "new_mode": "HYBRID",
                    "changed_at": "2025-01-26T13:00:00",
                    "reason": "Marché volatil"
                },
                {
                    "previous_mode": "AUTO_SPOT",
                    "new_mode": "MANUAL",
                    "changed_at": "2025-01-26T12:00:00",
                    "reason": "Risk score trop élevé"
                }
            ]
        }
        ```
    """
    try:
        history = mode_manager.get_mode_history(limit=limit)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# ==============================================================================
# STATS / INFO ENDPOINTS
# ==============================================================================

@app.get("/api/mode/info")
async def get_mode_info():
    """
    Informations complètes sur le système de modes
    
    Returns:
        Tous les modes disponibles avec descriptions
    """
    return {
        "success": True,
        "data": {
            "available_modes": {
                "AUTO_SPOT": {
                    "name": "Auto Spot",
                    "description": "Trading automatique spot uniquement",
                    "icon": "🤖",
                    "risk": "MEDIUM"
                },
                "AUTO_FUTURES": {
                    "name": "Auto Futures",
                    "description": "Trading automatique futures uniquement",
                    "icon": "⚡",
                    "risk": "HIGH"
                },
                "MANUAL": {
                    "name": "Manuel",
                    "description": "Contrôle manuel complet",
                    "icon": "👨‍💻",
                    "risk": "USER_CONTROLLED"
                },
                "HYBRID": {
                    "name": "Hybride",
                    "description": "IA suggère, vous validez",
                    "icon": "🤝",
                    "risk": "LOW_TO_MEDIUM"
                }
            },
            "current_mode": mode_manager.current_mode.value,
            "strategies_count": len(mode_manager.strategies),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🎯 SmartOrder PRO - Mode Manager API")
    print("=" * 70)
    print(f"\n📍 Mode actuel: {mode_manager.current_mode.value}")
    print("\n📡 Endpoints disponibles:")
    print("   GET  /api/mode/current           - Mode actuel")
    print("   POST /api/mode/set               - Changer de mode")
    print("   GET  /api/mode/suggestions       - Suggestions IA")
    print("   POST /api/mode/hybrid/suggest    - Créer suggestion")
    print("   POST /api/mode/hybrid/validate   - Valider suggestion")
    print("   GET  /api/mode/history           - Historique")
    print("   GET  /api/mode/strategies        - Liste stratégies")
    print("   GET  /api/mode/info              - Informations complètes")
    print("\n🌐 Démarrage sur http://0.0.0.0:8560")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8560,
        log_level="info"
    )
