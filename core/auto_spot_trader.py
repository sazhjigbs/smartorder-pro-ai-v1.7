"""
SmartOrder PRO - Multi-Layer Auto Spot Trader
Combine Grid Trading + DCA + Portfolio Rebalancing automatiquement
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

from core.grid_trading_bot import GridTradingBot
from core.dca_strategy import DCAStrategy
from core.portfolio_rebalancer import PortfolioRebalancer
from core.volatility_predictor import get_volatility_predictor
from core.sentiment_analyzer import get_sentiment_analyzer

LOG = logging.getLogger("auto_spot_trader")
LOG.setLevel(logging.INFO)

class AutoSpotTrader:
    """
    Système de trading spot automatique multi-couches
    
    Layers:
    1. Grid Trading: Profit en marchés sideways (40% capital)
    2. DCA: Accumulation progressive (30% capital)
    3. Rebalancing: Maintain allocation (30% capital)
    
    Intelligence:
    - Détecte le régime de marché (trending/ranging)
    - Active la stratégie optimale selon conditions
    - Ajuste allocation selon volatilité
    
    Mode AUTO:
    - Surveille 24/7
    - Execute ordres automatiquement
    - Rebalance hebdomadaire
    - DCA quotidien
    """
    
    def __init__(self, total_capital: float = 10000.0):
        """
        Initialize Auto Spot Trader
        
        Args:
            total_capital: Capital total en USDT
        """
        self.total_capital = total_capital
        self.available_capital = total_capital
        
        # Allocation du capital par stratégie
        self.allocation = {
            'grid': 0.40,      # 40% pour grid trading
            'dca': 0.30,       # 30% pour DCA
            'rebalance': 0.30  # 30% pour rebalancing
        }
        
        # Instances des stratégies
        self.grid_bots = {}        # {symbol: GridTradingBot}
        self.dca_strategies = {}   # {symbol: DCAStrategy}
        self.rebalancer = None
        
        # État du marché
        self.market_regime = 'UNKNOWN'  # TRENDING | RANGING | VOLATILE
        
        # Modules d'analyse
        self.vol_predictor = get_volatility_predictor()
        self.sentiment = get_sentiment_analyzer()
        
        # Active coins
        self.active_coins = []
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'grid_trades': 0,
            'dca_trades': 0,
            'rebalance_trades': 0,
            'total_profit': 0.0,
            'grid_profit': 0.0,
            'dca_profit': 0.0,
            'last_rebalance': None
        }
        
        LOG.info(f"AutoSpotTrader initialized with ${total_capital:,.2f}")
    
    def detect_market_regime(self, symbol: str, price_history: List[float]) -> str:
        """
        Détecte le régime de marché actuel
        
        Args:
            symbol: Symbole à analyser
            price_history: Historique des prix (dernières 24h)
            
        Returns:
            'TRENDING' | 'RANGING' | 'VOLATILE'
        """
        if len(price_history) < 20:
            return 'UNKNOWN'
        
        # Calculer volatilité
        vol_data = self.vol_predictor.predict_volatility(symbol)
        volatility = vol_data.get('volatility_score', 50)
        
        # Calculer range
        high = max(price_history)
        low = min(price_history)
        range_pct = ((high - low) / low) * 100
        
        # Détection
        if volatility > 70:
            regime = 'VOLATILE'
        elif range_pct < 5:
            regime = 'RANGING'  # Bon pour grid
        else:
            regime = 'TRENDING'  # Bon pour DCA
        
        self.market_regime = regime
        LOG.info(f"Market regime detected: {regime} (vol: {volatility:.1f}, range: {range_pct:.1f}%)")
        
        return regime
    
    def setup_grid_bot(self, symbol: str, lower_price: float, upper_price: float, 
                      num_grids: int = 10) -> GridTradingBot:
        """
        Configure un grid bot pour un symbole
        
        Args:
            symbol: Symbole (ex: 'BTCUSDT')
            lower_price: Prix bas de la range
            upper_price: Prix haut de la range
            num_grids: Nombre de niveaux
        """
        grid_capital = self.total_capital * self.allocation['grid']
        
        grid_bot = GridTradingBot(symbol, lower_price, upper_price, num_grids)
        
        # Placer les ordres
        orders = grid_bot.place_grid_orders(grid_capital)
        
        self.grid_bots[symbol] = grid_bot
        
        LOG.info(f"Grid bot setup for {symbol}: {len(orders)} orders placed")
        
        return grid_bot
    
    def setup_dca_strategy(self, symbol: str, budget: float, num_orders: int = 10) -> DCAStrategy:
        """
        Configure une stratégie DCA pour un symbole
        
        Args:
            symbol: Symbole
            budget: Budget DCA total
            num_orders: Nombre d'ordres DCA
        """
        dca = DCAStrategy(symbol, budget, num_orders)
        self.dca_strategies[symbol] = dca
        
        LOG.info(f"DCA strategy setup for {symbol}: ${budget:.2f} over {num_orders} orders")
        
        return dca
    
    def setup_portfolio_rebalancer(self, target_allocation: Dict[str, float]):
        """
        Configure le rebalancer de portfolio
        
        Args:
            target_allocation: {'BTC': 40, 'ETH': 30, 'USDT': 30}
        """
        self.rebalancer = PortfolioRebalancer(target_allocation)
        
        LOG.info(f"Portfolio rebalancer setup: {target_allocation}")
    
    def activate_coin(self, symbol: str, current_price: float, 
                     price_history: List[float]) -> Dict:
        """
        Active le trading automatique pour un coin
        
        Args:
            symbol: Symbole à activer
            current_price: Prix actuel
            price_history: Historique des prix
            
        Returns:
            Status de l'activation
        """
        # Détecter régime
        regime = self.detect_market_regime(symbol, price_history)
        
        result = {
            'symbol': symbol,
            'regime': regime,
            'strategies_active': []
        }
        
        # Activer stratégies selon régime
        if regime == 'RANGING':
            # Grid trading idéal
            lower = current_price * 0.95
            upper = current_price * 1.05
            
            self.setup_grid_bot(symbol, lower, upper, num_grids=10)
            result['strategies_active'].append('GRID')
            
            LOG.info(f"✅ {symbol}: Grid Trading activated (ranging market)")
        
        elif regime == 'TRENDING':
            # DCA idéal
            dca_budget = self.total_capital * self.allocation['dca']
            self.setup_dca_strategy(symbol, dca_budget, num_orders=10)
            result['strategies_active'].append('DCA')
            
            LOG.info(f"✅ {symbol}: DCA Strategy activated (trending market)")
        
        elif regime == 'VOLATILE':
            # Réduire exposition, attendre stabilisation
            LOG.warning(f"⚠️ {symbol}: High volatility, waiting for stabilization")
        
        # Ajouter à la liste active
        if symbol not in self.active_coins:
            self.active_coins.append(symbol)
        
        return result
    
    def execute_auto_trading_cycle(self, market_data: Dict[str, Dict]) -> Dict:
        """
        Execute un cycle de trading automatique
        
        Args:
            market_data: {
                'BTCUSDT': {
                    'price': 67000,
                    'rsi': 45,
                    'volume': 1000000,
                    'price_history': [...]
                }
            }
            
        Returns:
            Résumé du cycle
        """
        cycle_start = time.time()
        
        cycle_result = {
            'timestamp': datetime.now().isoformat(),
            'symbols_processed': 0,
            'orders_executed': 0,
            'strategies': {
                'grid': {'active': 0, 'filled': 0},
                'dca': {'active': 0, 'executed': 0},
                'rebalance': {'needed': False, 'executed': False}
            }
        }
        
        # 1. Process Grid Bots
        for symbol, grid_bot in self.grid_bots.items():
            if symbol in market_data:
                current_price = market_data[symbol]['price']
                grid_bot.check_order_fill(current_price)
                
                cycle_result['strategies']['grid']['active'] += 1
                cycle_result['symbols_processed'] += 1
        
        # 2. Process DCA Strategies
        for symbol, dca in self.dca_strategies.items():
            if symbol in market_data:
                current_price = market_data[symbol]['price']
                rsi = market_data[symbol].get('rsi', 50)
                
                # Calculer drop depuis dernier ordre
                price_drop = -2.0  # Placeholder
                
                if dca.should_execute_order(current_price, rsi, price_drop):
                    result = dca.execute_order(current_price)
                    
                    if result.get('success'):
                        cycle_result['strategies']['dca']['executed'] += 1
                        cycle_result['orders_executed'] += 1
                        self.stats['dca_trades'] += 1
                
                cycle_result['strategies']['dca']['active'] += 1
                cycle_result['symbols_processed'] += 1
        
        # 3. Check Rebalancing (une fois par jour)
        if self.rebalancer:
            # TODO: Implémenter logique de rebalancing
            pass
        
        # Update stats
        self.stats['total_trades'] += cycle_result['orders_executed']
        
        cycle_duration = time.time() - cycle_start
        cycle_result['duration_ms'] = round(cycle_duration * 1000, 2)
        
        LOG.info(f"Auto trading cycle completed: {cycle_result['orders_executed']} orders in {cycle_duration:.2f}s")
        
        return cycle_result
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """
        Génère un résumé du portfolio
        
        Args:
            current_prices: {'BTC': 67000, 'ETH': 3500}
        """
        summary = {
            'total_capital': self.total_capital,
            'available_capital': self.available_capital,
            'active_coins': len(self.active_coins),
            'strategies': {
                'grid_bots': len(self.grid_bots),
                'dca_strategies': len(self.dca_strategies),
                'rebalancer': self.rebalancer is not None
            },
            'stats': self.stats,
            'market_regime': self.market_regime
        }
        
        return summary
    
    def stop_all_strategies(self):
        """Arrête toutes les stratégies actives"""
        LOG.info("Stopping all strategies...")
        
        # Clear all strategies
        self.grid_bots.clear()
        self.dca_strategies.clear()
        self.active_coins.clear()
        
        LOG.info("All strategies stopped")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques complètes"""
        return {
            **self.stats,
            'active_coins': len(self.active_coins),
            'grid_bots': len(self.grid_bots),
            'dca_strategies': len(self.dca_strategies),
            'total_capital': self.total_capital,
            'available_capital': self.available_capital
        }


# Instance globale
_auto_spot_trader = None

def get_auto_spot_trader(capital: float = 10000.0) -> AutoSpotTrader:
    """Récupère l'instance singleton"""
    global _auto_spot_trader
    if _auto_spot_trader is None:
        _auto_spot_trader = AutoSpotTrader(capital)
    return _auto_spot_trader


if __name__ == "__main__":
    print("=" * 60)
    print("Auto Spot Trader - Test")
    print("=" * 60)
    
    trader = AutoSpotTrader(total_capital=10000.0)
    
    print(f"\n💰 Capital: ${trader.total_capital:,.2f}")
    print(f"   Grid: {trader.allocation['grid']*100:.0f}%")
    print(f"   DCA: {trader.allocation['dca']*100:.0f}%")
    print(f"   Rebalance: {trader.allocation['rebalance']*100:.0f}%")
    
    # Simuler activation de BTC
    print(f"\n🚀 Activating BTCUSDT...")
    
    btc_price_history = [67000 + i * 50 for i in range(-10, 10)]
    
    activation = trader.activate_coin(
        'BTCUSDT',
        current_price=67000.0,
        price_history=btc_price_history
    )
    
    print(f"   Regime: {activation['regime']}")
    print(f"   Strategies: {', '.join(activation['strategies_active'])}")
    
    # Simuler cycle de trading
    print(f"\n⚡ Executing auto trading cycle...")
    
    market_data = {
        'BTCUSDT': {
            'price': 67000.0,
            'rsi': 35,
            'volume': 1000000,
            'price_history': btc_price_history
        }
    }
    
    cycle = trader.execute_auto_trading_cycle(market_data)
    
    print(f"   Symbols processed: {cycle['symbols_processed']}")
    print(f"   Orders executed: {cycle['orders_executed']}")
    print(f"   Duration: {cycle['duration_ms']}ms")
    
    # Portfolio summary
    print(f"\n📊 Portfolio Summary:")
    summary = trader.get_portfolio_summary({'BTC': 67000, 'ETH': 3500})
    
    print(f"   Active coins: {summary['active_coins']}")
    print(f"   Grid bots: {summary['strategies']['grid_bots']}")
    print(f"   DCA strategies: {summary['strategies']['dca_strategies']}")
    print(f"   Market regime: {summary['market_regime']}")
    
    # Stats
    stats = trader.get_stats()
    print(f"\n📈 Stats:")
    print(f"   Total trades: {stats['total_trades']}")
    print(f"   Grid trades: {stats['grid_trades']}")
    print(f"   DCA trades: {stats['dca_trades']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
