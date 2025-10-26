"""
SmartOrder PRO - DCA (Dollar Cost Averaging) Strategy
Accumulation progressive avec timing optimal
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
import time

LOG = logging.getLogger("dca_strategy")
LOG.setLevel(logging.INFO)

class DCAStrategy:
    """
    DCA intelligent: Accumule progressivement avec timing optimal
    
    Types:
    1. Time-based DCA: Achats réguliers (quotidien, hebdo)
    2. Dip-buying DCA: Achète plus lors des baisses
    3. Smart DCA: Combine prix + indicators pour timing
    
    Example:
    - Budget: $1000/mois
    - Stratégie: Acheter plus quand RSI < 30
    - Résultat: Prix moyen d'entrée optimisé
    """
    
    def __init__(self, symbol: str, total_budget: float, num_orders: int = 10):
        self.symbol = symbol
        self.total_budget = total_budget
        self.num_orders = num_orders
        self.order_size = total_budget / num_orders
        
        self.orders_executed = []
        self.remaining_budget = total_budget
        
        self.stats = {
            'orders_executed': 0,
            'total_invested': 0.0,
            'avg_entry_price': 0.0,
            'total_quantity': 0.0
        }
        
        LOG.info(f"DCAStrategy initialized: {symbol} ${total_budget} over {num_orders} orders")
    
    def should_execute_order(self, current_price: float, rsi: float, price_drop_pct: float) -> bool:
        """Détermine si on doit exécuter un ordre DCA maintenant"""
        # Toujours acheter si prix baisse de plus de 5%
        if price_drop_pct <= -5.0:
            return True
        
        # Acheter si RSI < 35 (oversold)
        if rsi < 35:
            return True
        
        # Sinon, acheter à intervalle régulier
        time_based = len(self.orders_executed) < self.num_orders
        return time_based
    
    def execute_order(self, current_price: float) -> Dict:
        """Execute un ordre DCA"""
        if self.remaining_budget <= 0:
            return {'success': False, 'reason': 'Budget exhausted'}
        
        amount = min(self.order_size, self.remaining_budget)
        quantity = amount / current_price
        
        order = {
            'timestamp': datetime.now().isoformat(),
            'price': current_price,
            'amount': amount,
            'quantity': quantity
        }
        
        self.orders_executed.append(order)
        self.remaining_budget -= amount
        
        # Update stats
        self.stats['orders_executed'] += 1
        self.stats['total_invested'] += amount
        self.stats['total_quantity'] += quantity
        
        total_cost = sum(o['amount'] for o in self.orders_executed)
        total_qty = sum(o['quantity'] for o in self.orders_executed)
        self.stats['avg_entry_price'] = total_cost / total_qty if total_qty > 0 else 0
        
        LOG.info(f"DCA order executed: ${amount:.2f} @ {current_price} | Avg: {self.stats['avg_entry_price']:.2f}")
        
        return {'success': True, 'order': order}
    
    def get_stats(self) -> Dict:
        return {**self.stats, 'remaining_budget': self.remaining_budget}


_dca_strategies = {}

def get_dca_strategy(symbol: str, budget: float, orders: int = 10) -> DCAStrategy:
    key = f"{symbol}_{budget}"
    if key not in _dca_strategies:
        _dca_strategies[key] = DCAStrategy(symbol, budget, orders)
    return _dca_strategies[key]
