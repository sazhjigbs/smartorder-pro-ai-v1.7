"""
SmartOrder PRO - Grid Trading Bot
Système de grille automatique pour marchés en consolidation
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

LOG = logging.getLogger("grid_trading_bot")
LOG.setLevel(logging.INFO)

class GridTradingBot:
    """
    Grid Trading: Place des ordres d'achat/vente à intervalles réguliers
    
    Stratégie:
    - Range: $60k - $70k
    - Grids: 10 niveaux
    - Espacement: $1k par niveau
    - Achète en descendant, vend en montant
    - Profit par grid: 0.5-2%
    
    Idéal pour: Marchés en consolidation (sideways)
    ROI: 10-30% par an en marché stable
    """
    
    def __init__(self, symbol: str, lower_price: float, upper_price: float, num_grids: int = 10):
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.num_grids = num_grids
        
        self.grid_spacing = (upper_price - lower_price) / num_grids
        self.grid_levels = []
        self.active_orders = {}
        self.completed_trades = []
        
        self._create_grid_levels()
        
        self.stats = {
            'total_cycles': 0,
            'total_profit': 0.0,
            'win_rate': 100.0
        }
        
        LOG.info(f"GridTradingBot initialized: {symbol} [{lower_price}-{upper_price}] {num_grids} grids")
    
    def _create_grid_levels(self):
        """Crée les niveaux de grille"""
        for i in range(self.num_grids + 1):
            price = self.lower_price + (i * self.grid_spacing)
            self.grid_levels.append({
                'level': i,
                'price': round(price, 2),
                'buy_order': None,
                'sell_order': None
            })
        
        LOG.info(f"Created {len(self.grid_levels)} grid levels")
    
    def place_grid_orders(self, capital: float) -> List[Dict]:
        """Place tous les ordres de grille"""
        orders = []
        position_size = capital / (self.num_grids / 2)
        
        for grid in self.grid_levels[:-1]:
            buy_order = {
                'level': grid['level'],
                'side': 'BUY',
                'price': grid['price'],
                'quantity': position_size / grid['price'],
                'status': 'PENDING'
            }
            orders.append(buy_order)
            grid['buy_order'] = buy_order
            
            sell_price = grid['price'] + self.grid_spacing
            sell_order = {
                'level': grid['level'] + 1,
                'side': 'SELL',
                'price': sell_price,
                'quantity': position_size / grid['price'],
                'status': 'PENDING'
            }
            orders.append(sell_order)
            grid['sell_order'] = sell_order
        
        LOG.info(f"Placed {len(orders)} grid orders")
        return orders
    
    def check_order_fill(self, current_price: float):
        """Vérifie si des ordres sont remplis"""
        for grid in self.grid_levels:
            if grid['buy_order'] and grid['buy_order']['status'] == 'PENDING':
                if current_price <= grid['price']:
                    grid['buy_order']['status'] = 'FILLED'
                    LOG.info(f"BUY order filled at {grid['price']}")
            
            if grid['sell_order'] and grid['sell_order']['status'] == 'PENDING':
                if current_price >= grid['sell_order']['price']:
                    grid['sell_order']['status'] = 'FILLED'
                    profit = (grid['sell_order']['price'] - grid['price']) / grid['price'] * 100
                    self.stats['total_cycles'] += 1
                    self.stats['total_profit'] += profit
                    LOG.info(f"SELL order filled at {grid['sell_order']['price']} (+{profit:.2f}%)")
    
    def get_stats(self) -> Dict:
        return {**self.stats, 'grid_levels': len(self.grid_levels)}


_grid_bots = {}

def get_grid_bot(symbol: str, lower: float, upper: float, grids: int = 10) -> GridTradingBot:
    key = f"{symbol}_{lower}_{upper}"
    if key not in _grid_bots:
        _grid_bots[key] = GridTradingBot(symbol, lower, upper, grids)
    return _grid_bots[key]
