#!/usr/bin/env python3
"""
UPDATE: Technical Indicators Module v2.1
Date: 2025-10-31
Description: Indicateurs techniques RSI, MACD, Bollinger Bands, Support/Resistance
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Calcul des indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calcule le RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
        """Calcule MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return None
        
        prices_array = np.array(prices)
        
        # EMA rapide et lente
        ema_fast = TechnicalIndicators._ema(prices_array, fast)
        ema_slow = TechnicalIndicators._ema(prices_array, slow)
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = TechnicalIndicators._ema(macd_line, signal)
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            "macd": round(macd_line[-1], 4),
            "signal": round(signal_line[-1], 4),
            "histogram": round(histogram[-1], 4)
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Optional[Dict]:
        """Calcule les Bollinger Bands"""
        if len(prices) < period:
            return None
        
        prices_array = np.array(prices[-period:])
        
        middle_band = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        current_price = prices[-1]
        position = ((current_price - lower_band) / (upper_band - lower_band)) * 100
        
        return {
            "upper": round(upper_band, 2),
            "middle": round(middle_band, 2),
            "lower": round(lower_band, 2),
            "position": round(position, 2)
        }
    
    @staticmethod
    def find_support_resistance(prices: List[float], window: int = 20) -> Dict:
        """Detecte support et resistance"""
        if len(prices) < window * 2:
            return {"support": None, "resistance": None}
        
        prices_array = np.array(prices)
        
        # Trouver les mins et maxs locaux
        local_mins = []
        local_maxs = []
        
        for i in range(window, len(prices_array) - window):
            window_data = prices_array[i-window:i+window+1]
            if prices_array[i] == np.min(window_data):
                local_mins.append(prices_array[i])
            if prices_array[i] == np.max(window_data):
                local_maxs.append(prices_array[i])
        
        support = np.mean(local_mins) if local_mins else None
        resistance = np.mean(local_maxs) if local_maxs else None
        
        return {
            "support": round(support, 2) if support else None,
            "resistance": round(resistance, 2) if resistance else None
        }
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """Calcule EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return None
        
        ema = TechnicalIndicators._ema(np.array(prices), period)
        return round(ema[-1], 2)
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calcul interne EMA"""
        multiplier = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    @staticmethod
    def analyze_market(prices: List[float]) -> Dict:
        """Analyse complete du marche"""
        analysis = {
            "rsi": TechnicalIndicators.calculate_rsi(prices),
            "macd": TechnicalIndicators.calculate_macd(prices),
            "bollinger": TechnicalIndicators.calculate_bollinger_bands(prices),
            "support_resistance": TechnicalIndicators.find_support_resistance(prices),
            "ema_20": TechnicalIndicators.calculate_ema(prices, 20),
            "ema_50": TechnicalIndicators.calculate_ema(prices, 50),
            "current_price": prices[-1] if prices else None
        }
        
        # Determination du signal
        signal = "NEUTRAL"
        
        if analysis["rsi"]:
            if analysis["rsi"] < 30:
                signal = "BUY"
            elif analysis["rsi"] > 70:
                signal = "SELL"
        
        if analysis["macd"]:
            if analysis["macd"]["histogram"] > 0 and signal != "SELL":
                signal = "BUY"
            elif analysis["macd"]["histogram"] < 0 and signal != "BUY":
                signal = "SELL"
        
        analysis["signal"] = signal
        
        return analysis

# Test du module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Generer prix fictifs
    np.random.seed(42)
    base_price = 45000
    prices = [base_price]
    
    for i in range(100):
        change = np.random.randn() * 500
        new_price = prices[-1] + change
        prices.append(max(new_price, 1000))
    
    print("=== TECHNICAL INDICATORS TEST ===")
    print(f"Prix count: {len(prices)}")
    print(f"Prix actuel: {prices[-1]:.2f}")
    print()
    
    # RSI
    rsi = TechnicalIndicators.calculate_rsi(prices)
    print(f"RSI(14): {rsi}")
    
    # MACD
    macd = TechnicalIndicators.calculate_macd(prices)
    print(f"MACD: {macd}")
    
    # Bollinger
    bb = TechnicalIndicators.calculate_bollinger_bands(prices)
    print(f"Bollinger Bands: {bb}")
    
    # Support/Resistance
    sr = TechnicalIndicators.find_support_resistance(prices)
    print(f"Support/Resistance: {sr}")
    
    # Analyse complete
    print("\n=== MARKET ANALYSIS ===")
    analysis = TechnicalIndicators.analyze_market(prices)
    print(f"Signal: {analysis['signal']}")
    print(f"RSI: {analysis['rsi']}")
    print(f"MACD: {analysis['macd']}")
