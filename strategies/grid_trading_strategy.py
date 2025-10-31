#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Grid Trading Strategy
==========================================
Stratégie Grid Trading professionnelle avec grille dynamique

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

LOG = logging.getLogger("grid_trading")

@dataclass
class GridLevel:
    """Niveau de grille"""
    price: float
    quantity: float
    order_id: Optional[str] = None
    filled: bool = False

class GridTradingStrategy:
    """
    Grid Trading Strategy
    
    Place des ordres d'achat et de vente à intervalles réguliers
    pour profiter des fluctuations de prix
    """
    
    def __init__(self, 
                 symbol: str,
                 lower_price: float,
                 upper_price: float,
                 grid_levels: int,
                 quantity_per_grid: float,
                 mode: str = "neutral"):
        """
        Initialize Grid Trading Strategy
        
        Args:
            symbol: Trading pair (ex: BTCUSDT)
            lower_price: Prix le plus bas de la grille
            upper_price: Prix le plus haut de la grille
            grid_levels: Nombre de niveaux de grille
            quantity_per_grid: Quantité par niveau
            mode: 'neutral', 'long', 'short'
        """
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_levels = grid_levels
        self.quantity_per_grid = quantity_per_grid
        self.mode = mode
        
        # Calculate grid spacing
        self.grid_spacing = (upper_price - lower_price) / (grid_levels - 1)
        
        # Initialize grids
        self.buy_grids = []
        self.sell_grids = []
        
        self._setup_grids()
        
        # Stats
        self.trades_count = 0
        self.total_pnl = 0.0
        
        LOG.info(f"✅ Grid Trading initialized | {symbol} | Levels: {grid_levels} | Range: {lower_price}-{upper_price}")
    
    def _setup_grids(self):
        """Configure les niveaux de grille"""
        for i in range(self.grid_levels):
            price = self.lower_price + (i * self.grid_spacing)
            
            # Buy grids (below current price)
            self.buy_grids.append(GridLevel(
                price=price,
                quantity=self.quantity_per_grid
            ))
            
            # Sell grids (above current price)
            if i > 0:  # Skip first level for sell
                self.sell_grids.append(GridLevel(
                    price=price,
                    quantity=self.quantity_per_grid
                ))
    
    def get_signals(self, current_price: float) -> List[Dict]:
        """
        Génère les signaux de trading
        
        Args:
            current_price: Prix actuel
            
        Returns:
            Liste de signaux [{type, price, quantity}]
        """
        signals = []
        
        # Check buy grids
        for grid in self.buy_grids:
            if not grid.filled and current_price <= grid.price:
                signals.append({
                    'type': 'buy',
                    'price': grid.price,
                    'quantity': grid.quantity,
                    'grid_level': grid.price
                })
        
        # Check sell grids
        for grid in self.sell_grids:
            if not grid.filled and current_price >= grid.price:
                signals.append({
                    'type': 'sell',
                    'price': grid.price,
                    'quantity': grid.quantity,
                    'grid_level': grid.price
                })
        
        return signals
    
    def on_fill(self, order_type: str, price: float, quantity: float):
        """
        Callback quand un ordre est exécuté
        
        Args:
            order_type: 'buy' ou 'sell'
            price: Prix d'exécution
            quantity: Quantité exécutée
        """
        self.trades_count += 1
        
        # Mark grid as filled
        grids = self.buy_grids if order_type == 'buy' else self.sell_grids
        for grid in grids:
            if abs(grid.price - price) < 0.01:  # Tolerance
                grid.filled = True
                LOG.info(f"✅ Grid filled: {order_type.upper()} @ {price}")
                break
        
        # Calculate PNL for sell orders
        if order_type == 'sell':
            # Simple PNL calculation (buy at previous grid)
            buy_price = price - self.grid_spacing
            pnl = (price - buy_price) * quantity
            self.total_pnl += pnl
            LOG.info(f"💰 PNL: +{pnl:.2f} USDT | Total: {self.total_pnl:.2f}")
    
    def reset_grid(self, grid_level: float):
        """Reset un niveau de grille pour permettre re-trading"""
        for grid in self.buy_grids + self.sell_grids:
            if abs(grid.price - grid_level) < 0.01:
                grid.filled = False
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques"""
        return {
            'trades_count': self.trades_count,
            'total_pnl': self.total_pnl,
            'grid_levels': self.grid_levels,
            'price_range': f"{self.lower_price}-{self.upper_price}",
            'grid_spacing': self.grid_spacing,
            'active_buy_grids': sum(1 for g in self.buy_grids if not g.filled),
            'active_sell_grids': sum(1 for g in self.sell_grids if not g.filled)
        }
    
    def adjust_grid_range(self, new_lower: float, new_upper: float):
        """Ajuste dynamiquement la range de la grille"""
        self.lower_price = new_lower
        self.upper_price = new_upper
        self.grid_spacing = (new_upper - new_lower) / (self.grid_levels - 1)
        
        self.buy_grids.clear()
        self.sell_grids.clear()
        self._setup_grids()
        
        LOG.info(f"🔄 Grid range adjusted: {new_lower}-{new_upper}")


# Factory function
def create_grid_strategy(config: Dict) -> GridTradingStrategy:
    """
    Crée une stratégie Grid Trading depuis config
    
    Args:
        config: {
            'symbol': 'BTCUSDT',
            'lower_price': 50000,
            'upper_price': 60000,
            'grid_levels': 10,
            'quantity_per_grid': 0.01,
            'mode': 'neutral'
        }
    
    Returns:
        GridTradingStrategy instance
    """
    return GridTradingStrategy(
        symbol=config['symbol'],
        lower_price=config['lower_price'],
        upper_price=config['upper_price'],
        grid_levels=config['grid_levels'],
        quantity_per_grid=config['quantity_per_grid'],
        mode=config.get('mode', 'neutral')
    )


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    strategy = GridTradingStrategy(
        symbol="BTCUSDT",
        lower_price=50000,
        upper_price=60000,
        grid_levels=10,
        quantity_per_grid=0.01
    )
    
    # Simulate price movements
    prices = [55000, 54000, 53000, 54000, 55000, 56000]
    
    for price in prices:
        signals = strategy.get_signals(price)
        print(f"\nPrice: {price} | Signals: {len(signals)}")
        for signal in signals:
            print(f"  {signal}")
            strategy.on_fill(signal['type'], signal['price'], signal['quantity'])
    
    print(f"\nStats: {strategy.get_stats()}")
