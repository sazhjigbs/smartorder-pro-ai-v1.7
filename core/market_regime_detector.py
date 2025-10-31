#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Market Regime Detector
===========================================
Détection automatique des régimes de marché
by MAIGA ABOUBACAR
"""

import logging
from typing import Dict, List, Tuple
from enum import Enum

LOG = logging.getLogger("market_regime")
LOG.setLevel(logging.INFO)

class MarketRegime(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    RANGING = "ranging"
    VOLATILE = "volatile"

class MarketRegimeDetector:
    def __init__(self):
        LOG.info("✅ Market Regime Detector initialized")
    
    def detect_regime(self, price_data: Dict, indicators: Dict) -> Dict:
        current_price = price_data.get("current_price", 0)
        sma_20 = indicators.get("sma_20", current_price)
        sma_50 = indicators.get("sma_50", current_price)
        volatility = indicators.get("volatility", 0)
        
        trend_score = self._calculate_trend_score(current_price, sma_20, sma_50)
        
        if volatility > 15:
            regime = MarketRegime.VOLATILE
            strength = 0.8
        elif trend_score >= 60:
            regime = MarketRegime.UPTREND
            strength = 0.9
        elif trend_score <= -60:
            regime = MarketRegime.DOWNTREND
            strength = 0.9
        elif abs(trend_score) < 30:
            regime = MarketRegime.RANGING
            strength = 0.7
        else:
            regime = MarketRegime.SIDEWAYS
            strength = 0.6
        
        return {
            "regime": regime.value,
            "strength": strength,
            "volatility": volatility,
            "trend_score": trend_score
        }
    
    def _calculate_trend_score(self, price: float, sma_20: float, sma_50: float) -> float:
        score = 0.0
        if price > sma_20:
            score += 50
        else:
            score -= 50
        if sma_20 > sma_50:
            score += 50
        else:
            score -= 50
        return score

_detector = None
def get_market_regime_detector():
    global _detector
    if _detector is None:
        _detector = MarketRegimeDetector()
    return _detector
