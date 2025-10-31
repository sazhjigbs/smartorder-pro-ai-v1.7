"""
AI Strategy Composer - Version RÉELLE
Sélection intelligente de stratégie basée sur analyse multi-timeframe
"""
import time
import numpy as np
import ccxt
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("ai_composer_real")


class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"


class StrategyType(Enum):
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    GRID_TRADING = "grid_trading"
    SCALPING = "scalping"


@dataclass
class MarketAnalysis:
    regime: MarketRegime
    confidence: float  # 0-1
    timeframe_consensus: Dict[str, str]  # Consensus par TF
    indicators: Dict
    recommended_strategy: StrategyType
    entry_signal: str  # buy, sell, hold
    risk_level: str  # low, medium, high


class AIStrategyComposerReal:
    """Compositeur IA avec données CCXT multi-timeframe"""
    
    def __init__(self, exchange_name: str = "bybit"):
        self.exchange = self._init_exchange(exchange_name)
        self.timeframes = ['15m', '1h', '4h', '1d']
        self.analysis_history: List[MarketAnalysis] = []
        
        LOG.info(f"✅ AI Strategy Composer REAL initialisé")
        LOG.info(f"   Exchange: {exchange_name}")
        LOG.info(f"   Timeframes: {self.timeframes}")
    
    def _init_exchange(self, name: str) -> ccxt.Exchange:
        """Initialise exchange"""
        try:
            if name == "bybit":
                exchange = ccxt.bybit({'enableRateLimit': True})
            elif name == "binance":
                exchange = ccxt.binance({'enableRateLimit': True})
            else:
                exchange = ccxt.bybit({'enableRateLimit': True})
            
            exchange.load_markets()
            return exchange
        except Exception as e:
            LOG.error(f"❌ Erreur connexion: {e}")
            raise
    
    def fetch_multi_timeframe_data(self, symbol: str = "BTC/USDT") -> Dict:
        """Récupère données OHLCV sur tous les timeframes"""
        LOG.info(f"📥 Récupération données multi-TF pour {symbol}")
        
        data = {}
        
        for tf in self.timeframes:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=tf,
                    limit=100
                )
                
                data[tf] = {
                    'ohlcv': ohlcv,
                    'close': np.array([x[4] for x in ohlcv], dtype=float),
                    'high': np.array([x[2] for x in ohlcv], dtype=float),
                    'low': np.array([x[3] for x in ohlcv], dtype=float),
                    'volume': np.array([x[5] for x in ohlcv], dtype=float)
                }
                
                time.sleep(self.exchange.rateLimit / 1000)
            
            except Exception as e:
                LOG.error(f"❌ Erreur fetch {tf}: {e}")
                continue
        
        LOG.info(f"✅ {len(data)} timeframes récupérés")
        return data
    
    def calculate_indicators_all_tf(self, mtf_data: Dict) -> Dict:
        """Calcule indicateurs pour tous les timeframes"""
        from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
        from ta.momentum import RSIIndicator
        from ta.volatility import BollingerBands, AverageTrueRange
        
        indicators = {}
        
        for tf, data in mtf_data.items():
            close = data['close']
            high = data['high']
            low = data['low']
            
            # RSI
            rsi = RSIIndicator(close, window=14)
            rsi_val = rsi.rsi().iloc[-1] if len(rsi.rsi()) > 0 else 50
            
            # MACD
            macd = MACD(close)
            macd_val = macd.macd().iloc[-1] if len(macd.macd()) > 0 else 0
            macd_signal = macd.macd_signal().iloc[-1] if len(macd.macd_signal()) > 0 else 0
            
            # ADX (force tendance)
            adx = ADXIndicator(high, low, close, window=14)
            adx_val = adx.adx().iloc[-1] if len(adx.adx()) > 0 else 0
            
            # Bollinger Bands
            bb = BollingerBands(close, window=20)
            bb_upper = bb.bollinger_hband().iloc[-1] if len(bb.bollinger_hband()) > 0 else close[-1] * 1.02
            bb_lower = bb.bollinger_lband().iloc[-1] if len(bb.bollinger_lband()) > 0 else close[-1] * 0.98
            bb_middle = bb.bollinger_mavg().iloc[-1] if len(bb.bollinger_mavg()) > 0 else close[-1]
            
            # EMA
            ema_20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1] if len(close) >= 20 else close[-1]
            ema_50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1] if len(close) >= 50 else close[-1]
            
            # ATR (volatilité)
            atr = AverageTrueRange(high, low, close, window=14)
            atr_val = atr.average_true_range().iloc[-1] if len(atr.average_true_range()) > 0 else 0
            
            indicators[tf] = {
                'rsi': float(rsi_val),
                'macd': float(macd_val),
                'macd_signal': float(macd_signal),
                'macd_bullish': macd_val > macd_signal,
                'adx': float(adx_val),
                'bb_upper': float(bb_upper),
                'bb_middle': float(bb_middle),
                'bb_lower': float(bb_lower),
                'bb_position': (close[-1] - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5,
                'ema_20': float(ema_20),
                'ema_50': float(ema_50),
                'ema_bullish': ema_20 > ema_50,
                'atr': float(atr_val),
                'volatility': (atr_val / close[-1]) if close[-1] > 0 else 0,
                'current_price': float(close[-1])
            }
        
        return indicators
    
    def detect_regime_per_tf(self, indicators: Dict) -> Dict[str, MarketRegime]:
        """Détecte régime de marché par timeframe"""
        regimes = {}
        
        for tf, ind in indicators.items():
            rsi = ind['rsi']
            adx = ind['adx']
            macd_bullish = ind['macd_bullish']
            ema_bullish = ind['ema_bullish']
            volatility = ind['volatility']
            bb_pos = ind['bb_position']
            
            # Trending fort (ADX > 25)
            if adx > 25:
                if macd_bullish and ema_bullish and rsi > 50:
                    regimes[tf] = MarketRegime.TRENDING_BULL
                elif not macd_bullish and not ema_bullish and rsi < 50:
                    regimes[tf] = MarketRegime.TRENDING_BEAR
                else:
                    regimes[tf] = MarketRegime.TRENDING_BULL if rsi > 50 else MarketRegime.TRENDING_BEAR
            
            # Breakout détection
            elif bb_pos > 0.95:  # Prix proche BB supérieure
                regimes[tf] = MarketRegime.BREAKOUT_UP
            elif bb_pos < 0.05:  # Prix proche BB inférieure
                regimes[tf] = MarketRegime.BREAKOUT_DOWN
            
            # Volatilité élevée
            elif volatility > 0.03:
                regimes[tf] = MarketRegime.VOLATILE
            
            # Ranging par défaut
            else:
                regimes[tf] = MarketRegime.RANGING
        
        return regimes
    
    def calculate_confluence(self, regimes: Dict[str, MarketRegime]) -> tuple:
        """
        Calcule confluence entre timeframes
        Returns: (regime_dominant, confidence)
        """
        # Compte occurrences
        from collections import Counter
        regime_counts = Counter(regimes.values())
        
        # Régime le plus fréquent
        dominant_regime = regime_counts.most_common(1)[0][0]
        
        # Confidence = % de TF en accord
        confidence = regime_counts[dominant_regime] / len(regimes)
        
        # Bonus si les TF longs (4h, 1d) sont alignés
        long_tf_aligned = (
            regimes.get('4h') == dominant_regime and
            regimes.get('1d') == dominant_regime
        )
        
        if long_tf_aligned:
            confidence = min(confidence + 0.2, 1.0)
        
        return dominant_regime, confidence
    
    def select_strategy(self, regime: MarketRegime, confidence: float) -> StrategyType:
        """Sélectionne stratégie optimale selon régime"""
        
        strategy_map = {
            MarketRegime.TRENDING_BULL: StrategyType.TREND_FOLLOWING,
            MarketRegime.TRENDING_BEAR: StrategyType.TREND_FOLLOWING,
            MarketRegime.RANGING: StrategyType.GRID_TRADING,
            MarketRegime.VOLATILE: StrategyType.SCALPING,
            MarketRegime.BREAKOUT_UP: StrategyType.BREAKOUT,
            MarketRegime.BREAKOUT_DOWN: StrategyType.BREAKOUT
        }
        
        strategy = strategy_map.get(regime, StrategyType.GRID_TRADING)
        
        # Si confiance faible, préfère Grid (plus sûr)
        if confidence < 0.5:
            strategy = StrategyType.GRID_TRADING
        
        return strategy
    
    def generate_entry_signal(
        self,
        regime: MarketRegime,
        indicators: Dict,
        confidence: float
    ) -> str:
        """Génère signal d'entrée buy/sell/hold"""
        
        # Prend indicateurs du TF 1h (trading)
        ind_1h = indicators.get('1h', {})
        rsi = ind_1h.get('rsi', 50)
        macd_bullish = ind_1h.get('macd_bullish', False)
        bb_pos = ind_1h.get('bb_position', 0.5)
        
        # Seulement si confidence > 60%
        if confidence < 0.6:
            return 'hold'
        
        # Trending Bull
        if regime == MarketRegime.TRENDING_BULL:
            if rsi < 60 and macd_bullish:  # Pas encore suracheté
                return 'buy'
        
        # Trending Bear
        elif regime == MarketRegime.TRENDING_BEAR:
            if rsi > 40 and not macd_bullish:  # Pas encore survendu
                return 'sell'
        
        # Breakout Up
        elif regime == MarketRegime.BREAKOUT_UP:
            if bb_pos > 0.9:
                return 'buy'
        
        # Breakout Down
        elif regime == MarketRegime.BREAKOUT_DOWN:
            if bb_pos < 0.1:
                return 'sell'
        
        # Ranging / Mean Reversion
        elif regime == MarketRegime.RANGING:
            if rsi < 30:  # Survendu
                return 'buy'
            elif rsi > 70:  # Suracheté
                return 'sell'
        
        return 'hold'
    
    def calculate_risk_level(self, indicators: Dict, confidence: float) -> str:
        """Calcule niveau de risque"""
        
        # Volatilité moyenne sur tous TF
        volatilities = [ind['volatility'] for ind in indicators.values()]
        avg_volatility = np.mean(volatilities)
        
        # ADX moyen (force tendance)
        adxs = [ind['adx'] for ind in indicators.values()]
        avg_adx = np.mean(adxs)
        
        # Risque élevé si:
        # - Volatilité haute (>3%)
        # - Confiance faible (<50%)
        # - Tendance faible (ADX < 20)
        
        if avg_volatility > 0.03 or confidence < 0.5:
            return 'high'
        elif avg_volatility > 0.02 or avg_adx < 20:
            return 'medium'
        else:
            return 'low'
    
    def analyze_market(self, symbol: str = "BTC/USDT") -> MarketAnalysis:
        """
        Analyse complète du marché multi-timeframe
        Returns: MarketAnalysis avec recommandations
        """
        LOG.info(f"🔍 Analyse marché pour {symbol}")
        
        try:
            # 1. Récupère données multi-TF
            mtf_data = self.fetch_multi_timeframe_data(symbol)
            
            # 2. Calcule indicateurs
            indicators = self.calculate_indicators_all_tf(mtf_data)
            
            # 3. Détecte régime par TF
            regimes = self.detect_regime_per_tf(indicators)
            
            # 4. Calcule confluence
            dominant_regime, confidence = self.calculate_confluence(regimes)
            
            # 5. Sélectionne stratégie
            strategy = self.select_strategy(dominant_regime, confidence)
            
            # 6. Génère signal
            entry_signal = self.generate_entry_signal(dominant_regime, indicators, confidence)
            
            # 7. Calcule risque
            risk_level = self.calculate_risk_level(indicators, confidence)
            
            analysis = MarketAnalysis(
                regime=dominant_regime,
                confidence=confidence,
                timeframe_consensus={tf: r.value for tf, r in regimes.items()},
                indicators=indicators,
                recommended_strategy=strategy,
                entry_signal=entry_signal,
                risk_level=risk_level
            )
            
            self.analysis_history.append(analysis)
            
            LOG.info(f"✅ Analyse terminée")
            LOG.info(f"   Régime: {dominant_regime.value} ({confidence*100:.0f}%)")
            LOG.info(f"   Stratégie: {strategy.value}")
            LOG.info(f"   Signal: {entry_signal}")
            LOG.info(f"   Risque: {risk_level}")
            
            return analysis
        
        except Exception as e:
            LOG.error(f"❌ Erreur analyse: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """Statistiques du composer"""
        if not self.analysis_history:
            return {'total_analyses': 0}
        
        regimes_count = {}
        strategies_count = {}
        
        for analysis in self.analysis_history:
            regime = analysis.regime.value
            strategy = analysis.recommended_strategy.value
            
            regimes_count[regime] = regimes_count.get(regime, 0) + 1
            strategies_count[strategy] = strategies_count.get(strategy, 0) + 1
        
        avg_confidence = np.mean([a.confidence for a in self.analysis_history])
        
        return {
            'total_analyses': len(self.analysis_history),
            'avg_confidence': avg_confidence,
            'regimes_distribution': regimes_count,
            'strategies_distribution': strategies_count,
            'last_regime': self.analysis_history[-1].regime.value,
            'last_strategy': self.analysis_history[-1].recommended_strategy.value
        }


if __name__ == "__main__":
    # Test
    composer = AIStrategyComposerReal(exchange_name="bybit")
    
    # Analyse marché
    LOG.info("\n" + "=" * 50)
    LOG.info("TEST: Analyse Multi-Timeframe")
    LOG.info("=" * 50)
    
    analysis = composer.analyze_market("BTC/USDT")
    
    print(f"\n📊 Résultats Analyse:")
    print(f"   Régime: {analysis.regime.value}")
    print(f"   Confiance: {analysis.confidence*100:.0f}%")
    print(f"   Stratégie recommandée: {analysis.recommended_strategy.value}")
    print(f"   Signal d'entrée: {analysis.entry_signal}")
    print(f"   Niveau de risque: {analysis.risk_level}")
    
    print(f"\n🕐 Consensus par TF:")
    for tf, regime in analysis.timeframe_consensus.items():
        print(f"   {tf}: {regime}")
    
    print(f"\n📈 Indicateurs 1h:")
    ind_1h = analysis.indicators.get('1h', {})
    print(f"   RSI: {ind_1h.get('rsi', 0):.1f}")
    print(f"   ADX: {ind_1h.get('adx', 0):.1f}")
    print(f"   Volatilité: {ind_1h.get('volatility', 0)*100:.2f}%")
    print(f"   Prix: {ind_1h.get('current_price', 0):.2f}")
    
    # Stats
    stats = composer.get_statistics()
    print(f"\n📊 Stats Composer:")
    print(f"   Analyses: {stats['total_analyses']}")
    print(f"   Confiance moyenne: {stats['avg_confidence']*100:.0f}%")
