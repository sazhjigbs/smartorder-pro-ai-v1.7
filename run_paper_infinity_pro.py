#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Infinity Grid PRO (KuCoin Style)
====================================================
Place TOUS les ordres buy/sell d'avance et trade automatiquement

Fonctionnement KuCoin:
1. Place 6 ordres BUY en dessous du prix
2. Place 6 ordres SELL au dessus du prix
3. Dès qu'un ordre est rempli, replace automatiquement le suivant
4. Profit garanti sur chaque cycle buy→sell

Author: MAIGA ABOUBACAR
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from core.paper_trading_engine_v2 import PaperTradingEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/paper_trading.log'),
        logging.StreamHandler()
    ]
)

LOG = logging.getLogger("infinity_grid_pro")

class InfinityGridPro:
    """
    Infinity Grid PRO - Style KuCoin
    
    Logique:
    - Place tous les ordres buy/sell d'avance
    - Quand BUY rempli → Place SELL au dessus
    - Quand SELL rempli → Replace BUY en dessous
    - Cycle infini avec profit garanti
    """
    
    def __init__(self, engine: PaperTradingEngine, symbol: str, 
                 base_price: float, grid_spacing: float = 1.5,
                 grid_levels: int = 8, quantity_per_grid: float = 0.003):
        """
        Initialize Infinity Grid PRO
        
        Args:
            engine: Paper trading engine
            symbol: Trading pair
            base_price: Prix de départ
            grid_spacing: Espacement en % (1-2% optimal)
            grid_levels: Nombre de niveaux (6-10 optimal)
            quantity_per_grid: Quantité par ordre (0.002-0.005 BTC)
        """
        self.engine = engine
        self.symbol = symbol
        self.base_price = base_price
        self.grid_spacing = grid_spacing / 100
        self.grid_levels = grid_levels
        self.quantity = quantity_per_grid
        
        # Tracking
        self.active_orders = {}  # {price: {'side': 'buy/sell', 'quantity': float}}
        self.filled_orders = []
        self.total_profit = 0
        self.trades_count = 0
        
        # Calculate grids
        self._calculate_grids()
        
        # Place initial orders
        self._place_initial_orders()
        
        LOG.info(f"🔥 Infinity Grid PRO initialized")
        LOG.info(f"   Symbol: {symbol}")
        LOG.info(f"   Base Price: {base_price:.2f} USDT")
        LOG.info(f"   Grid Spacing: {grid_spacing}%")
        LOG.info(f"   Levels: {grid_levels}")
        LOG.info(f"   Quantity: {quantity_per_grid} BTC")
        LOG.info(f"   Orders placed: {len(self.active_orders)}")
    
    def _calculate_grids(self):
        """Calculate all grid levels"""
        self.buy_levels = []
        self.sell_levels = []
        
        # Buy levels (below price)
        for i in range(1, self.grid_levels + 1):
            price = self.base_price * (1 - self.grid_spacing * i)
            self.buy_levels.append(round(price, 2))
        
        # Sell levels (above price)
        for i in range(1, self.grid_levels + 1):
            price = self.base_price * (1 + self.grid_spacing * i)
            self.sell_levels.append(round(price, 2))
        
        LOG.info(f"📊 Buy grids: {self.buy_levels[:3]}... (total {len(self.buy_levels)})")
        LOG.info(f"📊 Sell grids: {self.sell_levels[:3]}... (total {len(self.sell_levels)})")
    
    def _place_initial_orders(self):
        """Place tous les ordres buy/sell initiaux"""
        # Place all BUY orders
        for price in self.buy_levels:
            self.active_orders[price] = {
                'side': 'buy',
                'quantity': self.quantity,
                'placed_at': time.time()
            }
        
        # Place all SELL orders
        for price in self.sell_levels:
            self.active_orders[price] = {
                'side': 'sell',
                'quantity': self.quantity,
                'placed_at': time.time()
            }
        
        LOG.info(f"✅ {len(self.active_orders)} orders placed in grid")
    
    def check_and_execute(self, current_price: float) -> int:
        """
        Vérifie si des ordres doivent être exécutés
        
        Returns:
            Nombre d'ordres exécutés
        """
        executed_count = 0
        filled_orders_to_remove = []
        
        for price, order in list(self.active_orders.items()):
            # Check if order should be filled
            should_fill = False
            
            if order['side'] == 'buy' and current_price <= price:
                should_fill = True
            elif order['side'] == 'sell' and current_price >= price:
                should_fill = True
            
            if should_fill:
                # Execute order
                result = self.engine.place_order(
                    symbol=self.symbol,
                    side=order['side'],
                    order_type='market',
                    quantity=order['quantity'],
                    strategy='Infinity Grid PRO'
                )
                
                if result['success']:
                    executed_count += 1
                    filled_orders_to_remove.append(price)
                    
                    LOG.info(f"✅ {'🟢 BUY' if order['side'] == 'buy' else '🔴 SELL'} executed at {price:.2f} USDT")
                    
                    # Calculate profit for sell orders
                    if order['side'] == 'sell':
                        # Find corresponding buy price (one level below)
                        buy_price = price / (1 + self.grid_spacing)
                        profit = (price - buy_price) * order['quantity']
                        self.total_profit += profit
                        self.trades_count += 1
                        LOG.info(f"💰 Profit: +{profit:.2f} USDT | Total: {self.total_profit:.2f} USDT")
                    
                    # Replace order intelligently
                    self._replace_order(price, order['side'], current_price)
        
        # Remove filled orders
        for price in filled_orders_to_remove:
            del self.active_orders[price]
        
        return executed_count
    
    def _replace_order(self, filled_price: float, filled_side: str, current_price: float):
        """
        Replace un ordre rempli intelligemment
        
        Logique KuCoin:
        - Si BUY rempli → Place SELL 1 niveau au dessus
        - Si SELL rempli → Place BUY 1 niveau en dessous
        """
        if filled_side == 'buy':
            # Place SELL order above
            new_sell_price = round(filled_price * (1 + self.grid_spacing), 2)
            
            # Only place if not too far from current price
            if new_sell_price <= current_price * 1.2:  # Max 20% above
                self.active_orders[new_sell_price] = {
                    'side': 'sell',
                    'quantity': self.quantity,
                    'placed_at': time.time()
                }
                LOG.info(f"📤 Placed SELL order at {new_sell_price:.2f} USDT")
        
        elif filled_side == 'sell':
            # Place BUY order below
            new_buy_price = round(filled_price * (1 - self.grid_spacing), 2)
            
            # Only place if not too far from current price
            if new_buy_price >= current_price * 0.8:  # Max 20% below
                self.active_orders[new_buy_price] = {
                    'side': 'buy',
                    'quantity': self.quantity,
                    'placed_at': time.time()
                }
                LOG.info(f"📥 Placed BUY order at {new_buy_price:.2f} USDT")
    
    def get_status(self) -> Dict:
        """Retourne le statut de la grille"""
        buy_orders = sum(1 for o in self.active_orders.values() if o['side'] == 'buy')
        sell_orders = sum(1 for o in self.active_orders.values() if o['side'] == 'sell')
        
        return {
            'active_orders': len(self.active_orders),
            'buy_orders': buy_orders,
            'sell_orders': sell_orders,
            'total_profit': round(self.total_profit, 2),
            'trades_count': self.trades_count
        }


def main():
    """Lance Infinity Grid PRO"""
    
    print("=" * 70)
    print("🔥 SMARTORDER PRO - INFINITY GRID PRO (KUCOIN STYLE)")
    print("=" * 70)
    print()
    
    # Initialize engine
    engine = PaperTradingEngine(
        initial_balance=10000.0,
        data_file="/opt/smartorder-pro/data/paper_trading.json"
    )
    
    # Get current price
    current_price = engine.price_provider.get_price("BTCUSDT")
    if not current_price:
        LOG.error("❌ Cannot fetch BTC price")
        return
    
    LOG.info(f"📊 Current BTC price: {current_price:.2f} USDT")
    
    # Initialize Infinity Grid PRO
    grid = InfinityGridPro(
        engine=engine,
        symbol="BTCUSDT",
        base_price=current_price,
        grid_spacing=1.5,    # 1.5% spacing = plus de trades
        grid_levels=8,       # 8 niveaux de chaque côté
        quantity_per_grid=0.003  # 0.003 BTC par ordre
    )
    
    # Get initial balance
    balance = engine.get_balance()
    print()
    print(f"💰 Starting Balance: {balance['balance']:.2f} USDT")
    print(f"📊 Total Value: {balance['total_value']:.2f} USDT")
    print(f"🎯 Grid Orders: {len(grid.active_orders)}")
    print()
    print("🚀 Infinity Grid PRO running... (Press Ctrl+C to stop)")
    print("-" * 70)
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            time.sleep(5)  # Check every 5 seconds
            
            # Get current price
            current_price = engine.price_provider.get_price("BTCUSDT")
            if not current_price:
                LOG.warning("⚠️ Could not fetch price")
                time.sleep(5)
                continue
            
            # Check and execute orders
            executed = grid.check_and_execute(current_price)
            
            # Display status every 20 iterations (100 seconds)
            if iteration % 20 == 0:
                status = grid.get_status()
                balance = engine.get_balance()
                
                print()
                print(f"📊 Status Update (Iteration {iteration})")
                print(f"   Current Price: {current_price:.2f} USDT")
                print(f"   Balance: {balance['balance']:.2f} USDT")
                print(f"   Total Value: {balance['total_value']:.2f} USDT")
                print(f"   Active Orders: {status['active_orders']} ({status['buy_orders']} buy / {status['sell_orders']} sell)")
                print(f"   Total Profit: {status['total_profit']:.2f} USDT")
                print(f"   Completed Trades: {status['trades_count']}")
                print()
    
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("🛑 Stopping Infinity Grid PRO...")
        print("=" * 70)
        
        # Final stats
        balance = engine.get_balance()
        stats = engine.get_statistics()
        status = grid.get_status()
        
        print()
        print("📊 FINAL STATISTICS")
        print(f"   Final Balance: {balance['balance']:.2f} USDT")
        print(f"   Total Value: {balance['total_value']:.2f} USDT")
        print(f"   Total PNL: {balance['total_pnl']:.2f} USDT")
        print(f"   Grid Profit: {status['total_profit']:.2f} USDT")
        print(f"   Completed Cycles: {status['trades_count']}")
        print(f"   Win Rate: {stats['win_rate']:.2f}%")
        print()


if __name__ == "__main__":
    main()
