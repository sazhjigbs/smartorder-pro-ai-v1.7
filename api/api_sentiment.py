#!/usr/bin/env python3
"""
SmartOrder PRO - Market Sentiment API
======================================
API REST pour analyse du sentiment et contexte marché

Endpoints:
- GET /api/sentiment/fear_greed - Fear & Greed Index
- GET /api/sentiment/btc_dominance - Dominance BTC
- GET /api/sentiment/volatility - Volatilité marché
- GET /api/sentiment/regime - Régime de marché
- GET /api/sentiment/context - Contexte global complet
- POST /api/sentiment/should_trade - Décision de trading
- POST /api/sentiment/clear_cache - Vider cache

Usage:
    uvicorn api.api_sentiment:app --host 0.0.0.0 --port 8558
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

# Import module sentiment
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.sentiment import MarketSentiment

# ==============================================================================
# FASTAPI APP
# ==============================================================================

app = FastAPI(
    title="SmartOrder PRO - Market Sentiment API",
    description="API pour analyse sentiment et contexte marché crypto",
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

sentiment_engine = MarketSentiment()

# ==============================================================================
# MODELS PYDANTIC
# ==============================================================================

class TradeDecisionRequest(BaseModel):
    """Requête pour décision de trading"""
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance du signal (0-1)")
    symbol: str = Field(..., description="Symbole tradé (ex: BTCUSDT)")
    min_confidence: float = Field(0.70, ge=0.0, le=1.0, description="Confiance minimum requise")
    max_risk_score: int = Field(75, ge=0, le=100, description="Risk score maximum accepté")

class TradeDecisionResponse(BaseModel):
    """Réponse pour décision de trading"""
    should_trade: bool
    reasons: list[str]
    signal_confidence: float
    market_context: Dict[str, Any]
    timestamp: str

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Page d'accueil API"""
    return {
        "service": "SmartOrder PRO - Market Sentiment API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "fear_greed": "/api/sentiment/fear_greed",
            "btc_dominance": "/api/sentiment/btc_dominance",
            "volatility": "/api/sentiment/volatility",
            "regime": "/api/sentiment/regime",
            "context": "/api/sentiment/context",
            "should_trade": "/api/sentiment/should_trade",
            "clear_cache": "/api/sentiment/clear_cache"
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
# SENTIMENT ENDPOINTS
# ==============================================================================

@app.get("/api/sentiment/fear_greed")
async def get_fear_greed_index():
    """
    Récupère le Fear & Greed Index
    
    Returns:
        Fear & Greed Index (0-100) avec classification et recommandation
    
    Example:
        ```json
        {
            "value": 45,
            "classification": "Fear",
            "level": "Fear",
            "recommendation": "Accumulate",
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        data = sentiment_engine.get_fear_greed_index()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Fear & Greed: {str(e)}")

@app.get("/api/sentiment/btc_dominance")
async def get_btc_dominance():
    """
    Récupère la dominance BTC
    
    Returns:
        Dominance BTC en pourcentage
    
    Example:
        ```json
        {
            "btc_dominance": 52.3,
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        dominance = sentiment_engine.get_btc_dominance()
        return {
            "success": True,
            "data": {
                "btc_dominance": dominance,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur BTC dominance: {str(e)}")

@app.get("/api/sentiment/volatility")
async def get_market_volatility():
    """
    Récupère la volatilité du marché
    
    Returns:
        Volatilité basée sur BTC 24h avec niveau de risque
    
    Example:
        ```json
        {
            "volatility_percent": 4.2,
            "level": "Medium",
            "risk_level": 3,
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        data = sentiment_engine.get_market_volatility()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur volatility: {str(e)}")

@app.get("/api/sentiment/regime")
async def get_market_regime():
    """
    Détermine le régime de marché actuel
    
    Returns:
        Régime de marché (BULL/BEAR/NEUTRAL/CHOPPY) avec stratégie recommandée
    
    Example:
        ```json
        {
            "regime": "BULL",
            "description": "Strong uptrend - Favor LONG positions",
            "strategy": "Trend following, momentum",
            "change_7d": 12.5,
            "confidence": 0.82,
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        data = sentiment_engine.get_market_regime()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur market regime: {str(e)}")

@app.get("/api/sentiment/context")
async def get_market_context():
    """
    Récupère le contexte global du marché
    
    Combine tous les indicateurs:
    - Fear & Greed Index
    - BTC Dominance
    - Volatilité
    - Régime de marché
    - Score de risque global
    
    Returns:
        Contexte complet du marché avec recommandation globale
    
    Example:
        ```json
        {
            "fear_greed": {...},
            "btc_dominance": 52.3,
            "volatility": {...},
            "market_regime": {...},
            "global_risk_score": 45,
            "recommendation": "⚠️ Medium risk - Reduce position sizes",
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        data = sentiment_engine.get_market_context()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur market context: {str(e)}")

@app.post("/api/sentiment/should_trade")
async def should_trade_signal(request: TradeDecisionRequest):
    """
    Décide si un signal doit être tradé selon le contexte marché
    
    Analyse:
    - Confiance du signal
    - Risk score global
    - Fear & Greed extremes
    - Conditions de marché (choppy, volatilité...)
    
    Body:
        - signal_confidence: Confiance du signal (0-1)
        - symbol: Symbole tradé
        - min_confidence: Confiance minimum (défaut: 0.70)
        - max_risk_score: Risk score max (défaut: 75)
    
    Returns:
        Décision (should_trade: bool) avec raisons détaillées
    
    Example Request:
        ```json
        {
            "signal_confidence": 0.85,
            "symbol": "BTCUSDT",
            "min_confidence": 0.70,
            "max_risk_score": 75
        }
        ```
    
    Example Response:
        ```json
        {
            "should_trade": true,
            "reasons": [
                "All market conditions favorable",
                "Risk score: 45/100 (acceptable)",
                "Regime: BULL"
            ],
            "signal_confidence": 0.85,
            "market_context": {...},
            "timestamp": "2024-01-15T12:00:00"
        }
        ```
    """
    try:
        decision = sentiment_engine.should_trade_signal(
            signal_confidence=request.signal_confidence,
            symbol=request.symbol,
            min_confidence=request.min_confidence,
            max_risk_score=request.max_risk_score
        )
        
        return {
            "success": True,
            "data": decision
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur trade decision: {str(e)}")

@app.post("/api/sentiment/clear_cache")
async def clear_cache():
    """
    Vide le cache du sentiment engine
    
    Force le refresh de toutes les données au prochain appel.
    Utile pour obtenir les données les plus récentes.
    
    Returns:
        Message de confirmation
    """
    try:
        sentiment_engine.clear_cache()
        return {
            "success": True,
            "message": "Cache vidé avec succès",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur clear cache: {str(e)}")

# ==============================================================================
# STATS / DEBUG ENDPOINTS
# ==============================================================================

@app.get("/api/sentiment/stats")
async def get_sentiment_stats():
    """
    Statistiques sur le sentiment engine
    
    Returns:
        Info sur cache, durée, dernière mise à jour
    """
    try:
        return {
            "success": True,
            "data": {
                "cache_duration_seconds": sentiment_engine.cache_duration,
                "cached_items": list(sentiment_engine.cache.keys()),
                "last_update": sentiment_engine.last_update.isoformat() if sentiment_engine.last_update else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur stats: {str(e)}")

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 SmartOrder PRO - Market Sentiment API")
    print("=" * 70)
    print("\n📡 Endpoints disponibles:")
    print("   GET  /api/sentiment/fear_greed    - Fear & Greed Index")
    print("   GET  /api/sentiment/btc_dominance - Dominance BTC")
    print("   GET  /api/sentiment/volatility    - Volatilité marché")
    print("   GET  /api/sentiment/regime        - Régime de marché")
    print("   GET  /api/sentiment/context       - Contexte global")
    print("   POST /api/sentiment/should_trade  - Décision de trading")
    print("   POST /api/sentiment/clear_cache   - Vider cache")
    print("   GET  /api/sentiment/stats         - Statistiques")
    print("\n🌐 Démarrage sur http://0.0.0.0:8558")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8558,
        log_level="info"
    )
