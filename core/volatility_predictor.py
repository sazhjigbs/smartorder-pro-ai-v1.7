"""
SmartOrder PRO - Volatility Predictor Module
Prédit la volatilité future avec modèles statistiques et ML
"""

import time
import logging
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import math

LOG = logging.getLogger("volatility_predictor")
LOG.setLevel(logging.INFO)

class VolatilityPredictor:
    """
    Prédit la volatilité future des cryptos pour optimiser:
    - Taille de position (plus petite en haute volatilité)
    - Leverage (réduit en haute volatilité)
    - Stop Loss (élargi en haute volatilité)
    - Stratégie (scalping en basse vol, swing en haute vol)
    
    Méthodes:
    1. Historical Volatility (écart-type des rendements)
    2. Parkinson Estimator (High-Low range)
    3. ATR (Average True Range)
    4. EWMA (Exponentially Weighted Moving Average)
    5. GARCH-like prediction (simplifié)
    
    Output: Volatility Score 0-100
    - 0-20: Très faible (consolidation)
    - 20-40: Faible (marché calme)
    - 40-60: Modérée (normal)
    - 60-80: Haute (tendance forte)
    - 80-100: Extrême (panique/euphorie)
    """
    
    def __init__(self, lookback_periods: int = 24):
        """
        Initialize Volatility Predictor
        
        Args:
            lookback_periods: Nombre de périodes pour calculs (défaut: 24h)
        """
        self.lookback_periods = lookback_periods
        self.price_data = {}  # {symbol: deque([{timestamp, open, high, low, close, volume}])}
        self.volatility_history = {}  # {symbol: deque([{timestamp, volatility}])}
        
        # Paramètres EWMA
        self.ewma_lambda = 0.94  # Lambda de RiskMetrics
        
        # Cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        LOG.info("VolatilityPredictor initialized")
    
    def add_candle(self, symbol: str, candle: Dict):
        """
        Ajoute une bougie OHLCV à l'historique
        
        Args:
            symbol: Symbole (ex: 'BTCUSDT')
            candle: {timestamp, open, high, low, close, volume}
        """
        if symbol not in self.price_data:
            self.price_data[symbol] = deque(maxlen=self.lookback_periods * 2)
        
        self.price_data[symbol].append(candle)
        
        # Invalider le cache
        if symbol in self.cache:
            del self.cache[symbol]
    
    def add_price_tick(self, symbol: str, price: float, volume: float = 0, timestamp: Optional[float] = None):
        """
        Ajoute un tick de prix (alternative simplifiée)
        
        Args:
            symbol: Symbole
            price: Prix actuel
            volume: Volume (optionnel)
            timestamp: Timestamp Unix
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Créer une pseudo-bougie
        candle = {
            'timestamp': timestamp,
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': volume
        }
        
        self.add_candle(symbol, candle)
    
    def _get_returns(self, symbol: str) -> List[float]:
        """Calcule les rendements logarithmiques"""
        if symbol not in self.price_data:
            return []
        
        candles = list(self.price_data[symbol])
        if len(candles) < 2:
            return []
        
        returns = []
        for i in range(1, len(candles)):
            prev_close = candles[i-1]['close']
            curr_close = candles[i]['close']
            
            if prev_close > 0:
                # Rendement logarithmique
                ret = math.log(curr_close / prev_close)
                returns.append(ret)
        
        return returns
    
    def calculate_historical_volatility(self, symbol: str, periods: Optional[int] = None) -> float:
        """
        Calcule la volatilité historique (écart-type des rendements)
        
        Returns:
            Volatilité annualisée en %
        """
        if periods is None:
            periods = self.lookback_periods
        
        returns = self._get_returns(symbol)
        
        if len(returns) < 2:
            return 0.0
        
        # Prendre seulement les N dernières périodes
        recent_returns = returns[-periods:]
        
        # Écart-type
        std_dev = statistics.stdev(recent_returns) if len(recent_returns) > 1 else 0.0
        
        # Annualiser (supposant périodes = heures, donc 24*365 = 8760)
        annualized_vol = std_dev * math.sqrt(8760) * 100
        
        return round(annualized_vol, 2)
    
    def calculate_parkinson_volatility(self, symbol: str, periods: Optional[int] = None) -> float:
        """
        Parkinson's High-Low Volatility Estimator
        Plus efficace que la volatilité close-to-close
        
        Returns:
            Volatilité annualisée en %
        """
        if periods is None:
            periods = self.lookback_periods
        
        if symbol not in self.price_data:
            return 0.0
        
        candles = list(self.price_data[symbol])[-periods:]
        
        if len(candles) < 2:
            return 0.0
        
        # Parkinson formula: sqrt(1/(4*N*ln(2)) * sum(ln(H/L)^2))
        sum_sq_hl = 0
        for candle in candles:
            high = candle['high']
            low = candle['low']
            
            if low > 0 and high > 0:
                ln_hl = math.log(high / low)
                sum_sq_hl += ln_hl ** 2
        
        N = len(candles)
        
        if N == 0:
            return 0.0
        
        parkinson_vol = math.sqrt(sum_sq_hl / (4 * N * math.log(2)))
        
        # Annualiser
        annualized_vol = parkinson_vol * math.sqrt(8760) * 100
        
        return round(annualized_vol, 2)
    
    def calculate_atr(self, symbol: str, periods: int = 14) -> float:
        """
        Average True Range (ATR)
        
        Returns:
            ATR en % du prix
        """
        if symbol not in self.price_data:
            return 0.0
        
        candles = list(self.price_data[symbol])[-periods:]
        
        if len(candles) < 2:
            return 0.0
        
        true_ranges = []
        
        for i in range(1, len(candles)):
            prev_close = candles[i-1]['close']
            curr_high = candles[i]['high']
            curr_low = candles[i]['low']
            
            # True Range = max(H-L, |H-Cp|, |L-Cp|)
            tr = max(
                curr_high - curr_low,
                abs(curr_high - prev_close),
                abs(curr_low - prev_close)
            )
            
            true_ranges.append(tr)
        
        if not true_ranges:
            return 0.0
        
        # Moyenne des TR
        atr = sum(true_ranges) / len(true_ranges)
        
        # Convertir en % du prix actuel
        current_price = candles[-1]['close']
        
        if current_price > 0:
            atr_pct = (atr / current_price) * 100
            return round(atr_pct, 2)
        
        return 0.0
    
    def calculate_ewma_volatility(self, symbol: str) -> float:
        """
        EWMA Volatility (RiskMetrics approach)
        Donne plus de poids aux observations récentes
        
        Returns:
            Volatilité EWMA annualisée en %
        """
        returns = self._get_returns(symbol)
        
        if len(returns) < 2:
            return 0.0
        
        lambda_ = self.ewma_lambda
        
        # Variance initiale = variance simple
        variance = statistics.variance(returns) if len(returns) > 1 else 0.0
        
        # EWMA: σ²_t = λ * σ²_{t-1} + (1-λ) * r²_{t-1}
        for ret in returns:
            variance = lambda_ * variance + (1 - lambda_) * (ret ** 2)
        
        # Écart-type
        std_dev = math.sqrt(variance)
        
        # Annualiser
        annualized_vol = std_dev * math.sqrt(8760) * 100
        
        return round(annualized_vol, 2)
    
    def predict_volatility(self, symbol: str) -> Dict:
        """
        Prédit la volatilité future en combinant plusieurs méthodes
        
        Returns:
            {
                'volatility_score': 0-100,
                'level': 'VERY_LOW' | 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME',
                'historical_vol': float,
                'parkinson_vol': float,
                'atr': float,
                'ewma_vol': float,
                'recommendation': {
                    'position_size_multiplier': 0.5-1.5,
                    'leverage_multiplier': 0.5-1.2,
                    'sl_multiplier': 1.0-2.0,
                    'strategy': 'scalp' | 'swing' | 'hold'
                }
            }
        """
        # Vérifier cache
        cache_key = symbol
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        # Calculer toutes les volatilités
        hist_vol = self.calculate_historical_volatility(symbol)
        park_vol = self.calculate_parkinson_volatility(symbol)
        atr = self.calculate_atr(symbol)
        ewma_vol = self.calculate_ewma_volatility(symbol)
        
        # Combiner avec poids (EWMA > Parkinson > Historical > ATR)
        if ewma_vol > 0:
            combined_vol = (
                ewma_vol * 0.4 +
                park_vol * 0.3 +
                hist_vol * 0.2 +
                atr * 10 * 0.1  # ATR est en %, le multiplier pour échelle
            )
        else:
            combined_vol = (hist_vol + park_vol) / 2
        
        # Convertir en score 0-100
        # Supposons que 200% de vol annualisée = score 100
        volatility_score = min(100, (combined_vol / 200) * 100)
        
        # Niveau
        if volatility_score < 20:
            level = "VERY_LOW"
        elif volatility_score < 40:
            level = "LOW"
        elif volatility_score < 60:
            level = "MODERATE"
        elif volatility_score < 80:
            level = "HIGH"
        else:
            level = "EXTREME"
        
        # Recommandations de trading
        recommendation = self._get_trading_recommendation(volatility_score)
        
        result = {
            'symbol': symbol,
            'volatility_score': round(volatility_score, 1),
            'level': level,
            'historical_vol': hist_vol,
            'parkinson_vol': park_vol,
            'atr': atr,
            'ewma_vol': ewma_vol,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
        
        # Mettre en cache
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': result
        }
        
        # Stocker dans historique
        if symbol not in self.volatility_history:
            self.volatility_history[symbol] = deque(maxlen=100)
        
        self.volatility_history[symbol].append({
            'timestamp': time.time(),
            'volatility': volatility_score
        })
        
        LOG.info(f"Volatility prediction for {symbol}: {volatility_score:.1f} ({level})")
        
        return result
    
    def _get_trading_recommendation(self, volatility_score: float) -> Dict:
        """
        Génère des recommandations de trading basées sur la volatilité
        
        Args:
            volatility_score: Score 0-100
            
        Returns:
            Recommandations de multiplicateurs et stratégie
        """
        # Position size: plus petit en haute volatilité
        if volatility_score < 20:
            pos_mult = 1.5  # Augmenter 50%
        elif volatility_score < 40:
            pos_mult = 1.2
        elif volatility_score < 60:
            pos_mult = 1.0
        elif volatility_score < 80:
            pos_mult = 0.7
        else:
            pos_mult = 0.5  # Réduire 50%
        
        # Leverage: réduire en haute volatilité
        if volatility_score < 30:
            lev_mult = 1.2
        elif volatility_score < 50:
            lev_mult = 1.0
        elif volatility_score < 70:
            lev_mult = 0.8
        else:
            lev_mult = 0.5
        
        # Stop Loss: élargir en haute volatilité
        if volatility_score < 30:
            sl_mult = 1.0
        elif volatility_score < 50:
            sl_mult = 1.2
        elif volatility_score < 70:
            sl_mult = 1.5
        else:
            sl_mult = 2.0
        
        # Stratégie recommandée
        if volatility_score < 30:
            strategy = "scalp"  # Scalping en marché calme
        elif volatility_score < 70:
            strategy = "swing"  # Swing trading normal
        else:
            strategy = "hold"   # Hold et réduire trading actif
        
        return {
            'position_size_multiplier': pos_mult,
            'leverage_multiplier': lev_mult,
            'sl_multiplier': sl_mult,
            'strategy': strategy
        }
    
    def get_volatility_trend(self, symbol: str, periods: int = 10) -> str:
        """
        Détermine la tendance de volatilité (croissante/décroissante)
        
        Returns:
            'INCREASING' | 'DECREASING' | 'STABLE'
        """
        if symbol not in self.volatility_history:
            return "STABLE"
        
        history = list(self.volatility_history[symbol])[-periods:]
        
        if len(history) < 3:
            return "STABLE"
        
        # Comparer première et seconde moitié
        mid = len(history) // 2
        first_half = [h['volatility'] for h in history[:mid]]
        second_half = [h['volatility'] for h in history[mid:]]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        diff_pct = ((avg_second - avg_first) / max(avg_first, 1)) * 100
        
        if diff_pct > 10:
            return "INCREASING"
        elif diff_pct < -10:
            return "DECREASING"
        else:
            return "STABLE"
    
    def get_stats(self, symbol: str) -> Dict:
        """Retourne les statistiques pour un symbole"""
        if symbol not in self.volatility_history:
            return {}
        
        history = list(self.volatility_history[symbol])
        
        if not history:
            return {}
        
        vols = [h['volatility'] for h in history]
        
        return {
            'symbol': symbol,
            'data_points': len(history),
            'current_volatility': vols[-1] if vols else 0,
            'avg_volatility': round(sum(vols) / len(vols), 1),
            'min_volatility': min(vols),
            'max_volatility': max(vols),
            'trend': self.get_volatility_trend(symbol)
        }


# Instance globale
_volatility_predictor = None

def get_volatility_predictor() -> VolatilityPredictor:
    """Récupère l'instance singleton"""
    global _volatility_predictor
    if _volatility_predictor is None:
        _volatility_predictor = VolatilityPredictor()
    return _volatility_predictor


if __name__ == "__main__":
    # Test du module
    print("=" * 60)
    print("Volatility Predictor - Test")
    print("=" * 60)
    
    predictor = VolatilityPredictor(lookback_periods=20)
    
    symbol = "BTCUSDT"
    base_price = 67000
    
    # Simuler 20 bougies avec volatilité croissante
    print(f"\n📊 Simulation de {predictor.lookback_periods} périodes...")
    
    for i in range(predictor.lookback_periods):
        # Volatilité faible au début, forte à la fin
        volatility_factor = 1 + (i / predictor.lookback_periods) * 0.1
        
        # Prix avec mouvement aléatoire
        import random
        random.seed(i)  # Pour reproductibilité
        price_change = random.uniform(-0.02, 0.02) * volatility_factor
        price = base_price * (1 + price_change)
        
        candle = {
            'timestamp': time.time() + i * 3600,
            'open': price * 0.999,
            'high': price * 1.005 * volatility_factor,
            'low': price * 0.995 * volatility_factor,
            'close': price,
            'volume': random.uniform(100, 1000)
        }
        
        predictor.add_candle(symbol, candle)
        base_price = price  # Prix suivant
    
    print(f"   ✅ {len(predictor.price_data[symbol])} bougies ajoutées")
    
    # Prédiction
    print(f"\n🔮 Prédiction de volatilité pour {symbol}...")
    prediction = predictor.predict_volatility(symbol)
    
    print(f"\n📈 Résultats:")
    print(f"   Score: {prediction['volatility_score']:.1f}/100")
    print(f"   Niveau: {prediction['level']}")
    print(f"   Historical Vol: {prediction['historical_vol']:.2f}%")
    print(f"   Parkinson Vol: {prediction['parkinson_vol']:.2f}%")
    print(f"   ATR: {prediction['atr']:.2f}%")
    print(f"   EWMA Vol: {prediction['ewma_vol']:.2f}%")
    
    rec = prediction['recommendation']
    print(f"\n💡 Recommandations:")
    print(f"   Position Size: {rec['position_size_multiplier']}x")
    print(f"   Leverage: {rec['leverage_multiplier']}x")
    print(f"   Stop Loss: {rec['sl_multiplier']}x")
    print(f"   Strategy: {rec['strategy']}")
    
    # Tendance
    trend = predictor.get_volatility_trend(symbol)
    print(f"\n📊 Tendance: {trend}")
    
    # Stats
    stats = predictor.get_stats(symbol)
    print(f"\n📊 Stats:")
    print(f"   Data points: {stats['data_points']}")
    print(f"   Avg volatility: {stats['avg_volatility']:.1f}")
    print(f"   Range: {stats['min_volatility']:.1f} - {stats['max_volatility']:.1f}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
