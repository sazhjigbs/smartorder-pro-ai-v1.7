"""
Market Scanner - Détection de patterns, volume spikes, breakouts
"""
import time
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    DOJI = "doji"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    VOLUME_SPIKE = "volume_spike"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"


@dataclass
class ScanResult:
    """Résultat du scan"""
    symbol: str
    pattern: PatternType
    confidence: float  # 0-100
    price: float
    timestamp: float
    timeframe: str
    metadata: Dict


class MarketScanner:
    """Scanner de marché pour détecter opportunités"""
    
    def __init__(self):
        self.scan_history: List[ScanResult] = []
        self.watchlist: List[str] = []
    
    def scan_candlestick_patterns(self, symbol: str, candles: List[Dict]) -> List[ScanResult]:
        """Scanne les patterns de chandeliers"""
        results = []
        
        if len(candles) < 3:
            return results
        
        # Derniers candles
        c1 = candles[-3] if len(candles) >= 3 else None
        c2 = candles[-2] if len(candles) >= 2 else None
        c3 = candles[-1]
        
        # Hammer
        if self._is_hammer(c3):
            results.append(ScanResult(
                symbol=symbol,
                pattern=PatternType.HAMMER,
                confidence=75.0,
                price=c3['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={"candle": c3}
            ))
        
        # Shooting Star
        if self._is_shooting_star(c3):
            results.append(ScanResult(
                symbol=symbol,
                pattern=PatternType.SHOOTING_STAR,
                confidence=75.0,
                price=c3['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={"candle": c3}
            ))
        
        # Doji
        if self._is_doji(c3):
            results.append(ScanResult(
                symbol=symbol,
                pattern=PatternType.DOJI,
                confidence=70.0,
                price=c3['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={"candle": c3}
            ))
        
        if c2:
            # Bullish Engulfing
            if self._is_bullish_engulfing(c2, c3):
                results.append(ScanResult(
                    symbol=symbol,
                    pattern=PatternType.BULLISH_ENGULFING,
                    confidence=80.0,
                    price=c3['close'],
                    timestamp=time.time(),
                    timeframe="1h",
                    metadata={"candles": [c2, c3]}
                ))
            
            # Bearish Engulfing
            if self._is_bearish_engulfing(c2, c3):
                results.append(ScanResult(
                    symbol=symbol,
                    pattern=PatternType.BEARISH_ENGULFING,
                    confidence=80.0,
                    price=c3['close'],
                    timestamp=time.time(),
                    timeframe="1h",
                    metadata={"candles": [c2, c3]}
                ))
        
        if c1 and c2:
            # Three White Soldiers
            if self._is_three_white_soldiers([c1, c2, c3]):
                results.append(ScanResult(
                    symbol=symbol,
                    pattern=PatternType.THREE_WHITE_SOLDIERS,
                    confidence=85.0,
                    price=c3['close'],
                    timestamp=time.time(),
                    timeframe="1h",
                    metadata={"candles": [c1, c2, c3]}
                ))
            
            # Three Black Crows
            if self._is_three_black_crows([c1, c2, c3]):
                results.append(ScanResult(
                    symbol=symbol,
                    pattern=PatternType.THREE_BLACK_CROWS,
                    confidence=85.0,
                    price=c3['close'],
                    timestamp=time.time(),
                    timeframe="1h",
                    metadata={"candles": [c1, c2, c3]}
                ))
        
        self.scan_history.extend(results)
        return results
    
    def scan_volume_spike(self, symbol: str, candles: List[Dict], threshold: float = 2.0) -> Optional[ScanResult]:
        """Détecte les spikes de volume"""
        if len(candles) < 20:
            return None
        
        volumes = [c['volume'] for c in candles]
        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]
        
        if current_volume > avg_volume * threshold:
            result = ScanResult(
                symbol=symbol,
                pattern=PatternType.VOLUME_SPIKE,
                confidence=90.0,
                price=candles[-1]['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                    "ratio": current_volume / avg_volume
                }
            )
            self.scan_history.append(result)
            return result
        
        return None
    
    def scan_breakout(self, symbol: str, candles: List[Dict], lookback: int = 20) -> Optional[ScanResult]:
        """Détecte les breakouts/breakdowns"""
        if len(candles) < lookback + 1:
            return None
        
        highs = [c['high'] for c in candles[-lookback-1:-1]]
        lows = [c['low'] for c in candles[-lookback-1:-1]]
        
        resistance = max(highs)
        support = min(lows)
        
        current = candles[-1]
        
        # Breakout (cassure de résistance)
        if current['close'] > resistance * 1.005:  # 0.5% au-dessus
            result = ScanResult(
                symbol=symbol,
                pattern=PatternType.BREAKOUT,
                confidence=85.0,
                price=current['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={
                    "resistance": resistance,
                    "breakout_price": current['close'],
                    "breakout_percent": ((current['close'] - resistance) / resistance) * 100
                }
            )
            self.scan_history.append(result)
            return result
        
        # Breakdown (cassure de support)
        if current['close'] < support * 0.995:  # 0.5% en dessous
            result = ScanResult(
                symbol=symbol,
                pattern=PatternType.BREAKDOWN,
                confidence=85.0,
                price=current['close'],
                timestamp=time.time(),
                timeframe="1h",
                metadata={
                    "support": support,
                    "breakdown_price": current['close'],
                    "breakdown_percent": ((support - current['close']) / support) * 100
                }
            )
            self.scan_history.append(result)
            return result
        
        return None
    
    def scan_all(self, symbols: List[str], candles_data: Dict[str, List[Dict]]) -> List[ScanResult]:
        """Scanne tous les symboles pour tous les patterns"""
        all_results = []
        
        for symbol in symbols:
            candles = candles_data.get(symbol, [])
            if not candles:
                continue
            
            # Patterns chandeliers
            all_results.extend(self.scan_candlestick_patterns(symbol, candles))
            
            # Volume spike
            vol_result = self.scan_volume_spike(symbol, candles)
            if vol_result:
                all_results.append(vol_result)
            
            # Breakout/Breakdown
            break_result = self.scan_breakout(symbol, candles)
            if break_result:
                all_results.append(break_result)
        
        return all_results
    
    # ===== Pattern Detection Functions =====
    
    def _is_hammer(self, candle: Dict) -> bool:
        """Détecte un Hammer"""
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (
            lower_shadow >= body * 2 and
            upper_shadow <= body * 0.3 and
            candle['close'] > candle['open']
        )
    
    def _is_shooting_star(self, candle: Dict) -> bool:
        """Détecte une Shooting Star"""
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        return (
            upper_shadow >= body * 2 and
            lower_shadow <= body * 0.3 and
            candle['close'] < candle['open']
        )
    
    def _is_doji(self, candle: Dict) -> bool:
        """Détecte un Doji"""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        return body <= total_range * 0.1
    
    def _is_bullish_engulfing(self, c1: Dict, c2: Dict) -> bool:
        """Détecte un Bullish Engulfing"""
        return (
            c1['close'] < c1['open'] and  # C1 est bearish
            c2['close'] > c2['open'] and  # C2 est bullish
            c2['open'] < c1['close'] and  # C2 ouvre sous C1
            c2['close'] > c1['open']      # C2 ferme au-dessus de C1
        )
    
    def _is_bearish_engulfing(self, c1: Dict, c2: Dict) -> bool:
        """Détecte un Bearish Engulfing"""
        return (
            c1['close'] > c1['open'] and  # C1 est bullish
            c2['close'] < c2['open'] and  # C2 est bearish
            c2['open'] > c1['close'] and  # C2 ouvre au-dessus C1
            c2['close'] < c1['open']      # C2 ferme en dessous de C1
        )
    
    def _is_three_white_soldiers(self, candles: List[Dict]) -> bool:
        """Détecte Three White Soldiers"""
        if len(candles) < 3:
            return False
        
        return all(
            c['close'] > c['open'] and  # Tous bullish
            c['close'] > candles[i-1]['close'] if i > 0 else True  # Progression
            for i, c in enumerate(candles)
        )
    
    def _is_three_black_crows(self, candles: List[Dict]) -> bool:
        """Détecte Three Black Crows"""
        if len(candles) < 3:
            return False
        
        return all(
            c['close'] < c['open'] and  # Tous bearish
            c['close'] < candles[i-1]['close'] if i > 0 else True  # Progression
            for i, c in enumerate(candles)
        )
    
    def get_top_opportunities(self, min_confidence: float = 75.0, limit: int = 10) -> List[ScanResult]:
        """Retourne les meilleures opportunités récentes"""
        filtered = [r for r in self.scan_history if r.confidence >= min_confidence]
        sorted_results = sorted(filtered, key=lambda x: (x.confidence, x.timestamp), reverse=True)
        return sorted_results[:limit]
    
    def get_statistics(self) -> Dict:
        """Stats du scanner"""
        if not self.scan_history:
            return {"total_scans": 0}
        
        by_pattern = {}
        for result in self.scan_history:
            pattern = result.pattern.value
            by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
        
        return {
            "total_scans": len(self.scan_history),
            "by_pattern": by_pattern,
            "avg_confidence": np.mean([r.confidence for r in self.scan_history])
        }


# Exemple d'utilisation
if __name__ == "__main__":
    scanner = MarketScanner()
    
    # Données simulées
    candles_btc = [
        {"open": 49000, "high": 49500, "low": 48500, "close": 49200, "volume": 100},
        {"open": 49200, "high": 49800, "low": 49000, "close": 49600, "volume": 120},
        {"open": 49600, "high": 50200, "low": 49500, "close": 50000, "volume": 250}  # Volume spike
    ]
    
    results = scanner.scan_candlestick_patterns("BTCUSDT", candles_btc)
    vol_spike = scanner.scan_volume_spike("BTCUSDT", candles_btc, threshold=2.0)
    
    print(f"✅ {len(results)} patterns détectés")
    for r in results:
        print(f"  - {r.pattern.value} @ {r.price} (confidence: {r.confidence}%)")
    
    if vol_spike:
        print(f"🚀 Volume Spike détecté! Ratio: {vol_spike.metadata['ratio']:.2f}x")
