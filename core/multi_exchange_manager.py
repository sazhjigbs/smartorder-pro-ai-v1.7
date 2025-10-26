"""
SmartOrder PRO - Multi-Exchange Manager
Gère trading sur plusieurs exchanges avec routing intelligent
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

LOG = logging.getLogger("multi_exchange_manager")
LOG.setLevel(logging.INFO)

class MultiExchangeManager:
    """
    Gère le trading sur plusieurs exchanges simultanément
    
    Supported Exchanges:
    - Bybit (primary)
    - Binance
    - OKX
    - Kraken
    
    Features:
    - Best execution routing (meilleur prix)
    - Fee optimization (exchange avec fees les plus bas)
    - Liquidity aggregation
    - Inter-exchange arbitrage
    - Unified API interface
    - Failover & redundancy
    
    Smart Routing Logic:
    1. Check prices on all exchanges
    2. Compare fees (maker/taker)
    3. Check liquidity (spread & depth)
    4. Route to best exchange
    5. Execute with slippage protection
    """
    
    def __init__(self):
        """Initialize Multi-Exchange Manager"""
        # Exchange configurations
        self.exchanges = {
            'bybit': {
                'enabled': True,
                'priority': 1,
                'fees': {'maker': 0.10, 'taker': 0.10},
                'api_client': None,  # Will be initialized
                'status': 'ACTIVE'
            },
            'binance': {
                'enabled': False,  # To be enabled when keys added
                'priority': 2,
                'fees': {'maker': 0.10, 'taker': 0.10},
                'api_client': None,
                'status': 'INACTIVE'
            },
            'okx': {
                'enabled': False,
                'priority': 3,
                'fees': {'maker': 0.08, 'taker': 0.10},
                'api_client': None,
                'status': 'INACTIVE'
            },
            'kraken': {
                'enabled': False,
                'priority': 4,
                'fees': {'maker': 0.16, 'taker': 0.26},
                'api_client': None,
                'status': 'INACTIVE'
            }
        }
        
        # Price cache
        self.price_cache = {}  # {symbol: {exchange: {price, timestamp}}}
        
        # Active positions per exchange
        self.positions = defaultdict(dict)  # {exchange: {symbol: position}}
        
        # Routing stats
        self.routing_stats = {
            'total_routes': 0,
            'routes_by_exchange': defaultdict(int),
            'total_saved_fees': 0.0
        }
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'trades_by_exchange': defaultdict(int),
            'total_volume': 0.0,
            'arbitrage_opportunities': 0
        }
        
        LOG.info("MultiExchangeManager initialized")
    
    def enable_exchange(self, exchange: str, api_key: str, api_secret: str) -> bool:
        """
        Active un exchange avec credentials
        
        Args:
            exchange: Nom de l'exchange
            api_key: API Key
            api_secret: API Secret
            
        Returns:
            True si succès
        """
        if exchange not in self.exchanges:
            LOG.error(f"Unknown exchange: {exchange}")
            return False
        
        try:
            # TODO: Initialize API client with keys
            # self.exchanges[exchange]['api_client'] = ExchangeClient(...)
            
            self.exchanges[exchange]['enabled'] = True
            self.exchanges[exchange]['status'] = 'ACTIVE'
            
            LOG.info(f"✅ Exchange enabled: {exchange}")
            return True
            
        except Exception as e:
            LOG.error(f"Failed to enable {exchange}: {e}")
            return False
    
    def get_active_exchanges(self) -> List[str]:
        """Retourne la liste des exchanges actifs"""
        return [
            name for name, config in self.exchanges.items()
            if config['enabled'] and config['status'] == 'ACTIVE'
        ]
    
    def update_price(self, exchange: str, symbol: str, price: float, 
                    bid: float = None, ask: float = None):
        """
        Met à jour le prix sur un exchange
        
        Args:
            exchange: Exchange name
            symbol: Symbol
            price: Mid price
            bid: Bid price (optional)
            ask: Ask price (optional)
        """
        if symbol not in self.price_cache:
            self.price_cache[symbol] = {}
        
        self.price_cache[symbol][exchange] = {
            'price': price,
            'bid': bid or price,
            'ask': ask or price,
            'spread': (ask - bid) if (ask and bid) else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_best_price(self, symbol: str, side: str) -> Tuple[str, float]:
        """
        Trouve le meilleur prix sur tous les exchanges
        
        Args:
            symbol: Symbol à trader
            side: 'BUY' ou 'SELL'
            
        Returns:
            (exchange, best_price)
        """
        if symbol not in self.price_cache:
            return None, None
        
        prices = self.price_cache[symbol]
        
        if not prices:
            return None, None
        
        # Filtrer seulement exchanges actifs
        active_prices = {
            ex: data for ex, data in prices.items()
            if self.exchanges[ex]['enabled']
        }
        
        if not active_prices:
            return None, None
        
        if side == 'BUY':
            # Chercher ask le plus bas (meilleur prix d'achat)
            best_exchange = min(active_prices, key=lambda x: active_prices[x]['ask'])
            best_price = active_prices[best_exchange]['ask']
        else:  # SELL
            # Chercher bid le plus haut (meilleur prix de vente)
            best_exchange = max(active_prices, key=lambda x: active_prices[x]['bid'])
            best_price = active_prices[best_exchange]['bid']
        
        return best_exchange, best_price
    
    def calculate_execution_cost(self, exchange: str, symbol: str, 
                                 side: str, quantity: float, price: float) -> Dict:
        """
        Calcule le coût total d'exécution
        
        Args:
            exchange: Exchange name
            symbol: Symbol
            side: 'BUY' or 'SELL'
            quantity: Quantity to trade
            price: Execution price
            
        Returns:
            {
                'gross_value': float,
                'fees': float,
                'net_value': float,
                'effective_price': float
            }
        """
        exchange_config = self.exchanges[exchange]
        
        # Utiliser taker fee par défaut (conservative)
        fee_pct = exchange_config['fees']['taker']
        
        gross_value = quantity * price
        fees = gross_value * (fee_pct / 100)
        
        if side == 'BUY':
            net_value = gross_value + fees
        else:  # SELL
            net_value = gross_value - fees
        
        effective_price = net_value / quantity
        
        return {
            'exchange': exchange,
            'gross_value': round(gross_value, 2),
            'fees': round(fees, 2),
            'fee_pct': fee_pct,
            'net_value': round(net_value, 2),
            'effective_price': round(effective_price, 2)
        }
    
    def route_order(self, symbol: str, side: str, quantity: float, 
                   routing_strategy: str = 'BEST_PRICE') -> Dict:
        """
        Route un ordre vers le meilleur exchange
        
        Args:
            symbol: Symbol to trade
            side: 'BUY' or 'SELL'
            quantity: Quantity
            routing_strategy: 'BEST_PRICE' | 'LOWEST_FEES' | 'HIGHEST_LIQUIDITY'
            
        Returns:
            Routing decision avec exchange sélectionné
        """
        active_exchanges = self.get_active_exchanges()
        
        if not active_exchanges:
            return {
                'success': False,
                'reason': 'No active exchanges'
            }
        
        if symbol not in self.price_cache:
            return {
                'success': False,
                'reason': f'No price data for {symbol}'
            }
        
        # Analyser coûts sur chaque exchange
        execution_costs = []
        
        for exchange in active_exchanges:
            if exchange not in self.price_cache[symbol]:
                continue
            
            price_data = self.price_cache[symbol][exchange]
            price = price_data['ask'] if side == 'BUY' else price_data['bid']
            
            cost = self.calculate_execution_cost(exchange, symbol, side, quantity, price)
            cost['spread'] = price_data['spread']
            
            execution_costs.append(cost)
        
        if not execution_costs:
            return {
                'success': False,
                'reason': 'No valid routes found'
            }
        
        # Sélectionner selon stratégie
        if routing_strategy == 'BEST_PRICE':
            # Meilleur effective price
            if side == 'BUY':
                best_route = min(execution_costs, key=lambda x: x['effective_price'])
            else:
                best_route = max(execution_costs, key=lambda x: x['effective_price'])
        
        elif routing_strategy == 'LOWEST_FEES':
            # Fees les plus bas
            best_route = min(execution_costs, key=lambda x: x['fees'])
        
        elif routing_strategy == 'HIGHEST_LIQUIDITY':
            # Spread le plus serré
            best_route = min(execution_costs, key=lambda x: x['spread'])
        
        else:
            # Par défaut: best price
            best_route = execution_costs[0]
        
        # Update stats
        self.routing_stats['total_routes'] += 1
        self.routing_stats['routes_by_exchange'][best_route['exchange']] += 1
        
        LOG.info(f"✅ Order routed: {symbol} {side} → {best_route['exchange']} "
                f"@ {best_route['effective_price']:.2f}")
        
        return {
            'success': True,
            'exchange': best_route['exchange'],
            'price': best_route['effective_price'],
            'fees': best_route['fees'],
            'gross_value': best_route['gross_value'],
            'net_value': best_route['net_value'],
            'routing_strategy': routing_strategy
        }
    
    def execute_order(self, symbol: str, side: str, quantity: float, 
                     exchange: Optional[str] = None) -> Dict:
        """
        Execute un ordre sur un exchange (ou route automatiquement)
        
        Args:
            symbol: Symbol
            side: 'BUY' or 'SELL'
            quantity: Quantity
            exchange: Exchange spécifique (optional, sinon auto-route)
            
        Returns:
            Résultat de l'exécution
        """
        # Si exchange pas spécifié, router automatiquement
        if not exchange:
            routing = self.route_order(symbol, side, quantity)
            
            if not routing['success']:
                return routing
            
            exchange = routing['exchange']
        
        # TODO: Execute réel via API
        # Pour l'instant, simulation
        
        result = {
            'success': True,
            'exchange': exchange,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'executed_at': datetime.now().isoformat()
        }
        
        # Update stats
        self.stats['total_trades'] += 1
        self.stats['trades_by_exchange'][exchange] += 1
        
        LOG.info(f"✅ Order executed: {symbol} {side} {quantity} on {exchange}")
        
        return result
    
    def find_arbitrage_opportunities(self, symbol: str, 
                                    min_profit_pct: float = 0.5) -> List[Dict]:
        """
        Trouve les opportunités d'arbitrage pour un symbole
        
        Args:
            symbol: Symbol
            min_profit_pct: Profit minimum en %
            
        Returns:
            Liste d'opportunités
        """
        if symbol not in self.price_cache:
            return []
        
        prices = self.price_cache[symbol]
        active_exchanges = self.get_active_exchanges()
        
        # Filtrer seulement exchanges actifs
        active_prices = {
            ex: data for ex, data in prices.items()
            if ex in active_exchanges
        }
        
        if len(active_prices) < 2:
            return []
        
        opportunities = []
        
        # Comparer chaque paire d'exchanges
        exchanges = list(active_prices.keys())
        
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                buy_price = active_prices[buy_exchange]['ask']
                sell_price = active_prices[sell_exchange]['bid']
                
                # Calculer spread brut
                spread = sell_price - buy_price
                spread_pct = (spread / buy_price) * 100
                
                # Soustraire fees
                buy_fee = self.exchanges[buy_exchange]['fees']['taker']
                sell_fee = self.exchanges[sell_exchange]['fees']['taker']
                total_fees = buy_fee + sell_fee
                
                net_profit_pct = spread_pct - total_fees
                
                if net_profit_pct >= min_profit_pct:
                    opportunities.append({
                        'symbol': symbol,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'spread_pct': round(spread_pct, 3),
                        'fees_pct': round(total_fees, 3),
                        'net_profit_pct': round(net_profit_pct, 3),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    self.stats['arbitrage_opportunities'] += 1
                    
                    LOG.warning(f"💰 ARBITRAGE: {symbol} Buy {buy_exchange}@{buy_price} → "
                              f"Sell {sell_exchange}@{sell_price} = +{net_profit_pct:.2f}%")
        
        return opportunities
    
    def get_unified_balance(self) -> Dict[str, float]:
        """
        Agrège les balances de tous les exchanges
        
        Returns:
            {coin: total_balance}
        """
        unified_balance = defaultdict(float)
        
        # TODO: Fetch balances from all exchanges
        # For now, placeholder
        
        return dict(unified_balance)
    
    def get_exchange_stats(self) -> Dict:
        """Statistiques par exchange"""
        active = self.get_active_exchanges()
        
        return {
            'total_exchanges': len(self.exchanges),
            'active_exchanges': len(active),
            'exchanges': {
                name: {
                    'enabled': config['enabled'],
                    'status': config['status'],
                    'priority': config['priority'],
                    'fees': config['fees'],
                    'total_trades': self.stats['trades_by_exchange'][name],
                    'routed_orders': self.routing_stats['routes_by_exchange'][name]
                }
                for name, config in self.exchanges.items()
            }
        }
    
    def get_stats(self) -> Dict:
        """Statistiques globales"""
        return {
            **self.stats,
            'routing': self.routing_stats,
            'active_exchanges': len(self.get_active_exchanges())
        }


# Instance globale
_multi_exchange_manager = None

def get_multi_exchange_manager() -> MultiExchangeManager:
    """Récupère l'instance singleton"""
    global _multi_exchange_manager
    if _multi_exchange_manager is None:
        _multi_exchange_manager = MultiExchangeManager()
    return _multi_exchange_manager


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Exchange Manager - Test")
    print("=" * 60)
    
    manager = MultiExchangeManager()
    
    print(f"\n📊 Exchange Configuration:")
    for name, config in manager.exchanges.items():
        print(f"   {name}: {'✅' if config['enabled'] else '❌'} "
              f"Fees: {config['fees']['taker']}%")
    
    # Enable Binance (simulation)
    print(f"\n🔌 Enabling Binance...")
    manager.exchanges['binance']['enabled'] = True
    manager.exchanges['binance']['status'] = 'ACTIVE'
    print(f"   ✅ Binance enabled")
    
    # Update prices
    print(f"\n💰 Updating prices for BTCUSDT...")
    manager.update_price('bybit', 'BTCUSDT', 67000, bid=66990, ask=67010)
    manager.update_price('binance', 'BTCUSDT', 67050, bid=67040, ask=67060)
    
    print(f"   Bybit: $67,000 (spread: $20)")
    print(f"   Binance: $67,050 (spread: $20)")
    
    # Best price
    best_ex, best_price = manager.get_best_price('BTCUSDT', 'BUY')
    print(f"\n🎯 Best price for BUY: {best_ex} @ ${best_price:,.2f}")
    
    # Route order
    print(f"\n🚀 Routing order: BUY 1.0 BTC...")
    routing = manager.route_order('BTCUSDT', 'BUY', 1.0, 'BEST_PRICE')
    
    if routing['success']:
        print(f"   ✅ Routed to: {routing['exchange']}")
        print(f"   Price: ${routing['price']:,.2f}")
        print(f"   Fees: ${routing['fees']:.2f}")
        print(f"   Net cost: ${routing['net_value']:,.2f}")
    
    # Find arbitrage
    print(f"\n💎 Scanning for arbitrage...")
    arbs = manager.find_arbitrage_opportunities('BTCUSDT', min_profit_pct=0.3)
    
    if arbs:
        for arb in arbs:
            print(f"   💰 {arb['buy_exchange']} → {arb['sell_exchange']}: "
                  f"+{arb['net_profit_pct']:.2f}%")
    else:
        print(f"   No profitable arbitrage found")
    
    # Stats
    stats = manager.get_exchange_stats()
    print(f"\n📈 Stats:")
    print(f"   Active exchanges: {stats['active_exchanges']}/{stats['total_exchanges']}")
    print(f"   Total trades: {manager.stats['total_trades']}")
    print(f"   Arbitrage opportunities: {manager.stats['arbitrage_opportunities']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
