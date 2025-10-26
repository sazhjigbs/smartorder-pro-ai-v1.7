"""
SmartOrder PRO - Hybrid Trading System
Combine spot et futures intelligemment avec hedging automatique
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

from core.auto_spot_trader import get_auto_spot_trader
from core.auto_futures_trader import get_auto_futures_trader
from core.volatility_predictor import get_volatility_predictor
from core.sentiment_analyzer import get_sentiment_analyzer

LOG = logging.getLogger("hybrid_trader")
LOG.setLevel(logging.INFO)

class HybridTradingSystem:
    """
    Système hybride Spot + Futures avec intelligence adaptative
    
    Modes:
    1. SPOT_ONLY: Trading spot uniquement (marché stable)
    2. FUTURES_ONLY: Trading futures uniquement (tendance forte)
    3. HYBRID: Combinaison spot + futures (optimal)
    4. HEDGE: Spot long + Futures short (protection)
    
    Allocation Dynamique:
    - Marché Stable (Vol < 40): 70% Spot, 30% Futures
    - Marché Normal (Vol 40-60): 50% Spot, 50% Futures
    - Marché Volatile (Vol > 60): 30% Spot, 70% Futures
    
    Hedging Automatique:
    - Si spot en profit > 20%: Hedge avec futures short
    - Si marché baisse > 5%: Hedge positions spot
    - Funding rate arbitrage: Long spot + Short perpetual
    
    ROI Target: 80-200% APY
    """
    
    def __init__(self, total_capital: float = 10000.0):
        """
        Initialize Hybrid Trading System
        
        Args:
            total_capital: Capital total en USDT
        """
        self.total_capital = total_capital
        
        # Allocation par défaut (50/50)
        self.allocation = {
            'spot': 0.50,
            'futures': 0.50
        }
        
        # Traders
        spot_capital = total_capital * self.allocation['spot']
        futures_capital = total_capital * self.allocation['futures']
        
        self.spot_trader = get_auto_spot_trader(spot_capital)
        self.futures_trader = get_auto_futures_trader(futures_capital, max_lev=10)
        
        # Mode actuel
        self.current_mode = 'HYBRID'  # SPOT_ONLY | FUTURES_ONLY | HYBRID | HEDGE
        
        # Modules d'analyse
        self.vol_predictor = get_volatility_predictor()
        self.sentiment = get_sentiment_analyzer()
        
        # Hedge positions actives
        self.hedge_positions = {}  # {symbol: hedge_data}
        
        # Stats
        self.stats = {
            'total_profit': 0.0,
            'spot_profit': 0.0,
            'futures_profit': 0.0,
            'hedge_profit': 0.0,
            'mode_switches': 0,
            'total_hedges': 0
        }
        
        LOG.info(f"HybridTradingSystem initialized: ${total_capital:,.2f} | Mode: {self.current_mode}")
    
    def determine_optimal_mode(self, market_conditions: Dict) -> str:
        """
        Détermine le mode optimal selon conditions du marché
        
        Args:
            market_conditions: {
                'volatility_score': 0-100,
                'sentiment_score': 0-100,
                'trend_strength': 'WEAK' | 'MODERATE' | 'STRONG',
                'market_regime': 'RANGING' | 'TRENDING' | 'VOLATILE'
            }
            
        Returns:
            Mode optimal: 'SPOT_ONLY' | 'FUTURES_ONLY' | 'HYBRID' | 'HEDGE'
        """
        vol = market_conditions.get('volatility_score', 50)
        sentiment = market_conditions.get('sentiment_score', 50)
        regime = market_conditions.get('market_regime', 'UNKNOWN')
        trend = market_conditions.get('trend_strength', 'MODERATE')
        
        # Critères de décision
        
        # 1. HEDGE mode: Forte baisse ou extrême volatilité
        if vol > 80 or sentiment < 20:
            mode = 'HEDGE'
            reason = f"High risk detected (vol: {vol:.0f}, sent: {sentiment:.0f})"
        
        # 2. SPOT_ONLY: Marché stable, faible volatilité
        elif vol < 30 and regime == 'RANGING':
            mode = 'SPOT_ONLY'
            reason = "Stable ranging market, optimal for spot grid/DCA"
        
        # 3. FUTURES_ONLY: Tendance forte, haute conviction
        elif trend == 'STRONG' and 40 < vol < 70:
            mode = 'FUTURES_ONLY'
            reason = "Strong trend, optimal for leveraged futures"
        
        # 4. HYBRID: Conditions normales (défaut)
        else:
            mode = 'HYBRID'
            reason = "Normal market conditions, balanced allocation"
        
        LOG.info(f"Optimal mode determined: {mode} | {reason}")
        
        return mode
    
    def adjust_allocation(self, volatility_score: float):
        """
        Ajuste l'allocation spot/futures selon volatilité
        
        Args:
            volatility_score: Score de volatilité 0-100
        """
        old_allocation = self.allocation.copy()
        
        # Règles d'allocation
        if volatility_score < 40:
            # Marché stable: favoriser spot (moins de risque)
            self.allocation = {'spot': 0.70, 'futures': 0.30}
        elif volatility_score < 60:
            # Marché normal: équilibré
            self.allocation = {'spot': 0.50, 'futures': 0.50}
        else:
            # Marché volatile: favoriser futures (plus d'opportunités)
            self.allocation = {'spot': 0.30, 'futures': 0.70}
        
        if old_allocation != self.allocation:
            LOG.info(f"Allocation adjusted: Spot {self.allocation['spot']*100:.0f}% | "
                    f"Futures {self.allocation['futures']*100:.0f}% (vol: {volatility_score:.0f})")
    
    def should_hedge_spot_position(self, symbol: str, spot_pnl_pct: float, 
                                   market_sentiment: float) -> bool:
        """
        Détermine si on doit hedger une position spot
        
        Args:
            symbol: Symbole
            spot_pnl_pct: PnL actuel de la position spot (%)
            market_sentiment: Score de sentiment 0-100
            
        Returns:
            True si hedging recommandé
        """
        # Hedge si:
        # 1. Position en profit > 20% ET sentiment devient négatif
        if spot_pnl_pct > 20 and market_sentiment < 40:
            LOG.warning(f"Hedge trigger: {symbol} profit {spot_pnl_pct:.1f}% + bearish sentiment")
            return True
        
        # 2. Position en profit > 30% (protection des gains)
        if spot_pnl_pct > 30:
            LOG.warning(f"Hedge trigger: {symbol} large profit {spot_pnl_pct:.1f}%")
            return True
        
        # 3. Sentiment extrêmement négatif (protection)
        if market_sentiment < 20:
            LOG.warning(f"Hedge trigger: {symbol} extreme fear (sentiment: {market_sentiment:.0f})")
            return True
        
        return False
    
    def create_hedge_position(self, symbol: str, spot_quantity: float, 
                             current_price: float) -> Dict:
        """
        Crée une position de hedge (futures short)
        
        Args:
            symbol: Symbole à hedger
            spot_quantity: Quantité détenue en spot
            current_price: Prix actuel
            
        Returns:
            Résultat du hedge
        """
        # Ouvrir short futures pour hedger
        market_data = {
            'volatility_score': 50,  # Neutre pour hedge
            'sentiment_score': 50,
            'atr': 2.0
        }
        
        result = self.futures_trader.open_position(
            symbol,
            'SHORT',
            current_price,
            market_data
        )
        
        if result['success']:
            # Enregistrer hedge
            self.hedge_positions[symbol] = {
                'spot_quantity': spot_quantity,
                'futures_position': result['position'],
                'entry_price': current_price,
                'opened_at': datetime.now().isoformat()
            }
            
            self.stats['total_hedges'] += 1
            
            LOG.info(f"✅ Hedge created: {symbol} SHORT {result['position']['leverage']}x")
        
        return result
    
    def execute_hybrid_strategy(self, symbol: str, market_data: Dict) -> Dict:
        """
        Execute la stratégie hybride pour un symbole
        
        Args:
            symbol: Symbole à trader
            market_data: {
                'price': float,
                'volatility_score': float,
                'sentiment_score': float,
                'trend_strength': str,
                'market_regime': str,
                'rsi': float,
                'price_history': list
            }
            
        Returns:
            Résumé de l'exécution
        """
        result = {
            'symbol': symbol,
            'mode': self.current_mode,
            'actions': []
        }
        
        current_price = market_data['price']
        vol_score = market_data.get('volatility_score', 50)
        
        # Ajuster allocation
        self.adjust_allocation(vol_score)
        
        # Déterminer mode optimal
        optimal_mode = self.determine_optimal_mode(market_data)
        
        if optimal_mode != self.current_mode:
            LOG.info(f"Mode switch: {self.current_mode} → {optimal_mode}")
            self.current_mode = optimal_mode
            self.stats['mode_switches'] += 1
        
        # Exécuter selon mode
        if self.current_mode == 'SPOT_ONLY':
            # Activer seulement spot
            activation = self.spot_trader.activate_coin(
                symbol,
                current_price,
                market_data.get('price_history', [])
            )
            result['actions'].append(f"Spot activated: {activation['regime']}")
        
        elif self.current_mode == 'FUTURES_ONLY':
            # Trader seulement futures
            # TODO: Déterminer signal (LONG/SHORT)
            signal = 'LONG'  # Placeholder
            
            futures_result = self.futures_trader.open_position(
                symbol,
                signal,
                current_price,
                market_data
            )
            
            if futures_result['success']:
                result['actions'].append(f"Futures {signal} opened")
        
        elif self.current_mode == 'HYBRID':
            # Combiner spot + futures
            
            # 1. Activer spot
            spot_activation = self.spot_trader.activate_coin(
                symbol,
                current_price,
                market_data.get('price_history', [])
            )
            result['actions'].append(f"Spot: {spot_activation['regime']}")
            
            # 2. Ouvrir position futures si opportunité
            sentiment = market_data.get('sentiment_score', 50)
            
            if sentiment > 60:  # Bullish
                futures_result = self.futures_trader.open_position(
                    symbol, 'LONG', current_price, market_data
                )
                if futures_result['success']:
                    result['actions'].append("Futures LONG opened")
            
            elif sentiment < 40:  # Bearish
                futures_result = self.futures_trader.open_position(
                    symbol, 'SHORT', current_price, market_data
                )
                if futures_result['success']:
                    result['actions'].append("Futures SHORT opened")
        
        elif self.current_mode == 'HEDGE':
            # Mode protection: hedger toutes positions
            # TODO: Implémenter hedge de toutes positions spot
            result['actions'].append("Hedge mode activated")
        
        return result
    
    def get_combined_pnl(self) -> Dict:
        """
        Calcule le PnL combiné spot + futures
        
        Returns:
            {
                'total_pnl': float,
                'spot_pnl': float,
                'futures_pnl': float,
                'hedge_pnl': float,
                'roi': float
            }
        """
        # Spot PnL
        spot_stats = self.spot_trader.get_stats()
        spot_pnl = spot_stats.get('total_profit', 0)
        
        # Futures PnL
        futures_stats = self.futures_trader.get_stats()
        futures_pnl = futures_stats.get('net_profit', 0)
        
        # Total
        total_pnl = spot_pnl + futures_pnl
        roi = (total_pnl / self.total_capital) * 100
        
        return {
            'total_pnl': round(total_pnl, 2),
            'spot_pnl': round(spot_pnl, 2),
            'futures_pnl': round(futures_pnl, 2),
            'hedge_pnl': 0.0,  # TODO
            'roi': round(roi, 2)
        }
    
    def get_portfolio_overview(self) -> Dict:
        """Vue d'ensemble du portfolio hybride"""
        spot_summary = self.spot_trader.get_portfolio_summary({})
        futures_summary = self.futures_trader.get_position_summary()
        pnl = self.get_combined_pnl()
        
        return {
            'mode': self.current_mode,
            'total_capital': self.total_capital,
            'allocation': self.allocation,
            'spot': {
                'active_coins': spot_summary['active_coins'],
                'strategies': spot_summary['strategies']
            },
            'futures': {
                'active_positions': futures_summary['active_positions'],
                'margin_used': futures_summary['total_margin_used']
            },
            'pnl': pnl,
            'stats': self.stats
        }
    
    def get_stats(self) -> Dict:
        """Statistiques complètes"""
        pnl = self.get_combined_pnl()
        
        return {
            **self.stats,
            **pnl,
            'current_mode': self.current_mode,
            'allocation': self.allocation
        }


# Instance globale
_hybrid_trader = None

def get_hybrid_trader(capital: float = 10000.0) -> HybridTradingSystem:
    """Récupère l'instance singleton"""
    global _hybrid_trader
    if _hybrid_trader is None:
        _hybrid_trader = HybridTradingSystem(capital)
    return _hybrid_trader


if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid Trading System - Test")
    print("=" * 60)
    
    system = HybridTradingSystem(total_capital=10000.0)
    
    print(f"\n💰 Total Capital: ${system.total_capital:,.2f}")
    print(f"   Mode: {system.current_mode}")
    print(f"   Allocation: Spot {system.allocation['spot']*100:.0f}% | "
          f"Futures {system.allocation['futures']*100:.0f}%")
    
    # Test mode determination
    print(f"\n🔍 Testing Mode Determination:")
    
    test_scenarios = [
        {'volatility_score': 25, 'sentiment_score': 55, 'market_regime': 'RANGING', 'trend_strength': 'WEAK'},
        {'volatility_score': 55, 'sentiment_score': 65, 'market_regime': 'TRENDING', 'trend_strength': 'STRONG'},
        {'volatility_score': 85, 'sentiment_score': 15, 'market_regime': 'VOLATILE', 'trend_strength': 'WEAK'}
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        mode = system.determine_optimal_mode(scenario)
        print(f"   Scenario {i}: {mode} (vol: {scenario['volatility_score']}, "
              f"sent: {scenario['sentiment_score']}, regime: {scenario['market_regime']})")
    
    # Test hybrid execution
    print(f"\n🚀 Executing Hybrid Strategy for BTCUSDT...")
    
    market_data = {
        'price': 67000.0,
        'volatility_score': 45,
        'sentiment_score': 60,
        'trend_strength': 'MODERATE',
        'market_regime': 'TRENDING',
        'rsi': 55,
        'price_history': [67000 + i * 50 for i in range(-10, 10)],
        'atr': 2.5
    }
    
    result = system.execute_hybrid_strategy('BTCUSDT', market_data)
    
    print(f"   Mode: {result['mode']}")
    print(f"   Actions: {', '.join(result['actions'])}")
    
    # Portfolio overview
    print(f"\n📊 Portfolio Overview:")
    overview = system.get_portfolio_overview()
    
    print(f"   Mode: {overview['mode']}")
    print(f"   Spot active coins: {overview['spot']['active_coins']}")
    print(f"   Futures positions: {overview['futures']['active_positions']}")
    print(f"   Total PnL: ${overview['pnl']['total_pnl']:.2f}")
    print(f"   ROI: {overview['pnl']['roi']:.2f}%")
    
    # Stats
    stats = system.get_stats()
    print(f"\n📈 Stats:")
    print(f"   Mode switches: {stats['mode_switches']}")
    print(f"   Total hedges: {stats['total_hedges']}")
    print(f"   Combined ROI: {stats['roi']:.2f}%")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
