# -*- coding: utf-8 -*-
"""Market Regime Detection"""
import logging
import numpy as np

LOG = logging.getLogger(__name__)

class MarketRegimeDetector:
    def detect(self, prices: list) -> str:
        """Detect market regime: trending/ranging/volatile"""
        if len(prices) < 20:
            return 'unknown'
        
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        trend_strength = abs(np.mean(returns))
        
        if volatility > 0.03:
            return 'volatile'
        elif trend_strength > 0.01:
            return 'trending'
        else:
            return 'ranging'
