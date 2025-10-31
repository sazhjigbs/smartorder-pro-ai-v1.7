"""
AI Strategy Composer
Sélectionne dynamiquement la meilleure stratégie selon le régime de marché
"""
import time
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"


class StrategyType(Enum):
    GRID_TRADING = "grid_trading"
    DCA = "dca"
    SCALPING = "scalping"
    SWING_TRADING = "swing_trading"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"


@dataclass
class StrategyPerformance:
    """Performance d'une stratégie"""
    strategy: StrategyType
    regime: MarketRegime
    win_rate: float
    avg_pnl: float
    sharpe_ratio: float
    total_trades: int
    last_updated: float


class AIStrategyComposer:
    """Compositeur de stratégies IA"""
    
    def __init__(self):
        self.strategy_performance: Dict[str, List[StrategyPerformance]] = {}
        self.current_regime = MarketRegime.RANGING
        self.active_strategy = StrategyType.GRID_TRADING
        self.regime_history: List[Dict] = []
        
        # Mapping stratégie -> régime optimal
        self.strategy_regime_mapping = {
            StrategyType.GRID_TRADING: [MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY],
            StrategyType.TREND_FOLLOWING: [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
            StrategyType.MOMENTUM: [MarketRegime.BREAKOUT, MarketRegime.TRENDING_BULL],
            StrategyType.MEAN_REVERSION: [MarketRegime.RANGING],
            StrategyType.SCALPING: [MarketRegime.LOW_VOLATILITY, MarketRegime.RANGING],
            StrategyType.DCA: [MarketRegime.TRENDING_BEAR, MarketRegime.HIGH_VOLATILITY]
        }
    
    def detect_market_regime(self, market_data: Dict) -> MarketRegime:
        """Détecte le régime de marché actuel"""
        prices = market_data.get('closes', [])
        volumes = market_data.get('volumes', [])
        
        if len(prices) < 50:
            return MarketRegime.RANGING
        
        # Calcul indicateurs
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
        trend = self._calculate_trend(prices)
        atr = self._calculate_atr(market_data.get('highs', []), market_data.get('lows', []), prices)
        
        # Détection du régime
        if volatility > 0.05:
            regime = MarketRegime.HIGH_VOLATILITY
        elif volatility < 0.02:
            regime = MarketRegime.LOW_VOLATILITY
        elif trend > 0.03:
            regime = MarketRegime.TRENDING_BULL
        elif trend < -0.03:
            regime = MarketRegime.TRENDING_BEAR
        elif atr > np.mean(prices[-20:]) * 0.04:  # ATR élevé
            regime = MarketRegime.BREAKOUT
        else:
            regime = MarketRegime.RANGING
        
        # Historique
        self.regime_history.append({
            "regime": regime,
            "timestamp": time.time(),
            "volatility": volatility,
            "trend": trend
        })
        
        self.current_regime = regime
        return regime
    
    def select_best_strategy(self, market_data: Dict) -> Dict:
        """Sélectionne la meilleure stratégie pour le régime actuel"""
        regime = self.detect_market_regime(market_data)
        
        # Trouver les stratégies adaptées à ce régime
        suitable_strategies = []
        for strategy, regimes in self.strategy_regime_mapping.items():
            if regime in regimes:
                suitable_strategies.append(strategy)
        
        if not suitable_strategies:
            suitable_strategies = [StrategyType.GRID_TRADING]  # Fallback
        
        # Sélectionner la stratégie avec les meilleures performances historiques
        best_strategy = self._select_by_performance(suitable_strategies, regime)
        
        # Vérifier si changement nécessaire
        should_switch = best_strategy != self.active_strategy
        
        if should_switch:
            old_strategy = self.active_strategy
            self.active_strategy = best_strategy
            print(f"🔄 Strategy switch: {old_strategy.value} → {best_strategy.value} (Regime: {regime.value})")
        
        return {
            "regime": regime.value,
            "selected_strategy": best_strategy.value,
            "strategy_changed": should_switch,
            "suitable_strategies": [s.value for s in suitable_strategies],
            "confidence": self._calculate_confidence(best_strategy, regime)
        }
    
    def _select_by_performance(self, strategies: List[StrategyType], regime: MarketRegime) -> StrategyType:
        """Sélectionne la stratégie basée sur les performances historiques"""
        best_strategy = strategies[0]
        best_score = 0.0
        
        for strategy in strategies:
            key = f"{strategy.value}_{regime.value}"
            performances = self.strategy_performance.get(key, [])
            
            if performances:
                # Score basé sur win rate et sharpe ratio
                latest_perf = performances[-1]
                score = latest_perf.win_rate * 0.6 + latest_perf.sharpe_ratio * 10 * 0.4
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
        
        return best_strategy
    
    def update_strategy_performance(
        self,
        strategy: StrategyType,
        regime: MarketRegime,
        win_rate: float,
        avg_pnl: float,
        sharpe_ratio: float,
        total_trades: int
    ):
        """Met à jour les performances d'une stratégie"""
        key = f"{strategy.value}_{regime.value}"
        
        perf = StrategyPerformance(
            strategy=strategy,
            regime=regime,
            win_rate=win_rate,
            avg_pnl=avg_pnl,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            last_updated=time.time()
        )
        
        if key not in self.strategy_performance:
            self.strategy_performance[key] = []
        
        self.strategy_performance[key].append(perf)
    
    def _calculate_trend(self, prices: List[float]) -> float:
        """Calcule la tendance"""
        if len(prices) < 50:
            return 0.0
        
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:])
        
        return (sma_20 - sma_50) / sma_50
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calcule l'ATR (Average True Range)"""
        if len(closes) < period + 1:
            return 0.0
        
        tr_list = []
        for i in range(1, len(closes)):
            high = highs[i] if i < len(highs) else closes[i]
            low = lows[i] if i < len(lows) else closes[i]
            prev_close = closes[i-1]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)
        
        return np.mean(tr_list[-period:])
    
    def _calculate_confidence(self, strategy: StrategyType, regime: MarketRegime) -> float:
        """Calcule la confiance dans la sélection"""
        key = f"{strategy.value}_{regime.value}"
        performances = self.strategy_performance.get(key, [])
        
        if not performances:
            return 0.5  # Confiance moyenne si pas d'historique
        
        latest = performances[-1]
        
        # Confiance basée sur win rate et nombre de trades
        confidence = (latest.win_rate / 100) * 0.7 + min(latest.total_trades / 100, 1.0) * 0.3
        
        return min(confidence, 1.0)
    
    def get_statistics(self) -> Dict:
        """Statistiques du composer"""
        return {
            "current_regime": self.current_regime.value,
            "active_strategy": self.active_strategy.value,
            "regime_changes": len(self.regime_history),
            "strategies_tracked": len(self.strategy_performance),
            "recent_regimes": [r["regime"].value for r in self.regime_history[-10:]]
        }


# Exemple d'utilisation
if __name__ == "__main__":
    composer = AIStrategyComposer()
    
    # Simuler données de marché
    prices = [50000 + i * 50 + np.random.randint(-200, 200) for i in range(100)]
    
    market_data = {
        'closes': prices,
        'highs': [p * 1.01 for p in prices],
        'lows': [p * 0.99 for p in prices],
        'volumes': [1000] * 100
    }
    
    # Sélection de stratégie
    result = composer.select_best_strategy(market_data)
    print(f"✅ Selected Strategy: {result['selected_strategy']}")
    print(f"📊 Market Regime: {result['regime']}")
    print(f"🎯 Confidence: {result['confidence']:.2%}")
    
    # Mise à jour des performances
    composer.update_strategy_performance(
        strategy=StrategyType.GRID_TRADING,
        regime=MarketRegime.RANGING,
        win_rate=75.0,
        avg_pnl=50.0,
        sharpe_ratio=1.8,
        total_trades=50
    )
    
    print(f"\n📈 Stats: {composer.get_statistics()}")
