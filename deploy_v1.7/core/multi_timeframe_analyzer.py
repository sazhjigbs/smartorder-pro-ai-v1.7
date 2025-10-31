"""
Multi-Timeframe Analyzer
Analyse plusieurs timeframes pour confluence
"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class Timeframe(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class Trend(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class TimeframeAnalysis:
    timeframe: Timeframe
    trend: Trend
    strength: float  # 0-100
    indicators: Dict


class MultiTimeframeAnalyzer:
    """Analyseur multi-timeframe"""
    
    def __init__(self):
        self.analyses: Dict[str, List[TimeframeAnalysis]] = {}
    
    def analyze_timeframe(self, symbol: str, timeframe: Timeframe, data: Dict) -> TimeframeAnalysis:
        """Analyse un timeframe"""
        prices = data.get('closes', [])
        volumes = data.get('volumes', [])
        
        if len(prices) < 50:
            return None
        
        # Calcul des indicateurs
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:])
        current_price = prices[-1]
        
        # RSI
        rsi = self._calculate_rsi(prices)
        
        # MACD
        macd_line, signal_line = self._calculate_macd(prices)
        
        # Déterminer la tendance
        trend = self._determine_trend(current_price, sma_20, sma_50, rsi, macd_line, signal_line)
        strength = self._calculate_strength(current_price, sma_20, sma_50, rsi)
        
        analysis = TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            strength=strength,
            indicators={
                'sma_20': sma_20,
                'sma_50': sma_50,
                'rsi': rsi,
                'macd': macd_line,
                'signal': signal_line,
                'current_price': current_price
            }
        )
        
        if symbol not in self.analyses:
            self.analyses[symbol] = []
        self.analyses[symbol].append(analysis)
        
        return analysis
    
    def get_confluence(self, symbol: str) -> Dict:
        """Analyse la confluence entre timeframes"""
        if symbol not in self.analyses or not self.analyses[symbol]:
            return {"confluence": "none", "strength": 0}
        
        analyses = self.analyses[symbol]
        
        bullish_count = sum(1 for a in analyses if 'bullish' in a.trend.value.lower())
        bearish_count = sum(1 for a in analyses if 'bearish' in a.trend.value.lower())
        total = len(analyses)
        
        avg_strength = np.mean([a.strength for a in analyses])
        
        if bullish_count >= total * 0.7:
            confluence = "strong_bullish"
        elif bullish_count >= total * 0.5:
            confluence = "bullish"
        elif bearish_count >= total * 0.7:
            confluence = "strong_bearish"
        elif bearish_count >= total * 0.5:
            confluence = "bearish"
        else:
            confluence = "mixed"
        
        return {
            "confluence": confluence,
            "strength": avg_strength,
            "bullish_timeframes": bullish_count,
            "bearish_timeframes": bearish_count,
            "total_timeframes": total,
            "details": [
                {
                    "timeframe": a.timeframe.value,
                    "trend": a.trend.value,
                    "strength": a.strength
                }
                for a in analyses
            ]
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcule le RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """Calcule MACD"""
        if len(prices) < 26:
            return 0.0, 0.0
        
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        macd_line = ema_12 - ema_26
        
        # Signal approximatif
        signal_line = macd_line * 0.9
        
        return macd_line, signal_line
    
    def _ema(self, prices: List[float], period: int) -> float:
        """Calcule EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _determine_trend(self, price, sma_20, sma_50, rsi, macd, signal) -> Trend:
        """Détermine la tendance"""
        bullish_signals = 0
        bearish_signals = 0
        
        if price > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if sma_20 > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if rsi > 50:
            bullish_signals += 1
        elif rsi < 50:
            bearish_signals += 1
        
        if macd > signal:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if bullish_signals >= 4:
            return Trend.STRONG_BULLISH
        elif bullish_signals == 3:
            return Trend.BULLISH
        elif bearish_signals >= 4:
            return Trend.STRONG_BEARISH
        elif bearish_signals == 3:
            return Trend.BEARISH
        else:
            return Trend.NEUTRAL
    
    def _calculate_strength(self, price, sma_20, sma_50, rsi) -> float:
        """Calcule la force de la tendance"""
        strength = 50.0
        
        # Distance des moyennes mobiles
        if sma_20 != 0:
            dist_20 = abs((price - sma_20) / sma_20) * 100
            strength += min(dist_20 * 2, 20)
        
        # RSI
        if rsi > 70 or rsi < 30:
            strength += 15
        elif rsi > 60 or rsi < 40:
            strength += 10
        
        return min(strength, 100.0)


if __name__ == "__main__":
    analyzer = MultiTimeframeAnalyzer()
    
    # Données simulées
    prices = [50000 + i * 100 + np.random.randint(-200, 200) for i in range(100)]
    
    data_h1 = {'closes': prices, 'volumes': [100] * 100}
    data_h4 = {'closes': prices[::4], 'volumes': [100] * 25}
    data_d1 = {'closes': prices[::24], 'volumes': [100] * 5}
    
    analyzer.analyze_timeframe("BTCUSDT", Timeframe.H1, data_h1)
    analyzer.analyze_timeframe("BTCUSDT", Timeframe.H4, data_h4)
    analyzer.analyze_timeframe("BTCUSDT", Timeframe.D1, data_d1)
    
    confluence = analyzer.get_confluence("BTCUSDT")
    print(f"✅ Confluence: {confluence['confluence']}")
    print(f"📊 Strength: {confluence['strength']:.2f}%")
    print(f"📈 Details: {confluence['details']}")
