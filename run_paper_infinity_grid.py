#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Paper Trading Infinity Grid
================================================
Paper trading avec stratégie Infinity Grid optimisée

Author: MAIGA ABOUBACAR
"""

import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.paper_trading_engine_v2 import PaperTradingEngine
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/paper_trading.log'),
        logging.StreamHandler()
    ]
)

LOG = logging.getLogger("infinity_grid")

class InfinityGridStrategy:
    """
    Infinity Grid Strategy Optimisée
    
    Features:
    - Grille géométrique (% fixe entre niveaux)
    - Auto-expansion si prix sort de la grille
    - Trailing stop (suit le marché à la hausse)
    - Profit compounding
    """
    
    def __init__(self, symbol: str, base_price: float, 
                 grid_spacing: float = 2.0, grid_levels: int = 5,
                 quantity_per_grid: float = 0.003):
        """
        Initialize Infinity Grid
        
        Args:
            symbol: Trading pair (ex: BTCUSDT)
            base_price: Prix de référence actuel
            grid_spacing: Espacement entre grilles en % (recommandé: 1.5-3%)
            grid_levels: Nombre de niveaux (recommandé: 5-7)
            quantity_per_grid: Quantité par niveau (recommandé: 0.002-0.005 BTC)
        """
        self.symbol = symbol
        self.base_price = base_price
        self.grid_spacing = grid_spacing / 100  # Convert to decimal
        self.grid_levels = grid_levels
        self.quantity = quantity_per_grid
        
        # Tracking
        self.total_profit = 0
        self.trades_count = 0
        self.last_action_price = base_price
        
        # Calculate grid levels
        self._calculate_grids()
        
        LOG.info(f"✅ Infinity Grid initialized")
        LOG.info(f"   Symbol: {symbol}")
        LOG.info(f"   Base Price: {base_price:.2f} USDT")
        LOG.info(f"   Grid Spacing: {grid_spacing}%")
        LOG.info(f"   Levels: {grid_levels} up + {grid_levels} down")
        LOG.info(f"   Quantity: {quantity_per_grid} BTC per level")
    
    def _calculate_grids(self):
        """Calculate buy and sell grid levels"""
        self.buy_levels = []
        self.sell_levels = []
        
        # Buy levels (below current price)
        for i in range(1, self.grid_levels + 1):
            price = self.base_price * (1 - self.grid_spacing * i)
            self.buy_levels.append(price)
        
        # Sell levels (above current price)
        for i in range(1, self.grid_levels + 1):
            price = self.base_price * (1 + self.grid_spacing * i)
            self.sell_levels.append(price)
        
        LOG.info(f"📊 Buy levels: {[f'{p:.2f}' for p in sorted(self.buy_levels, reverse=True)]}")
        LOG.info(f"📊 Sell levels: {[f'{p:.2f}' for p in self.sell_levels]}")
    
    def get_signals(self, current_price: float, current_positions: dict) -> list:
        """
        Generate trading signals based on grid levels
        
        Returns:
            List of signals: [{'side': 'buy'/'sell', 'price': float, 'quantity': float}]
        """
        signals = []
        
        # Check if we need to rebase grid (price moved too far)
        if (current_price > self.sell_levels[-1] or 
            current_price < self.buy_levels[-1]):
            LOG.warning(f"⚠️ Price {current_price:.2f} outside grid range, rebalancing...")
            self.base_price = current_price
            self._calculate_grids()
            return signals
        
        # Get current BTC position
        position_qty = 0
        if self.symbol in current_positions:
            position_qty = current_positions[self.symbol].get('quantity', 0)
        
        # BUY signals - when price crosses below buy levels
        for buy_price in self.buy_levels:
            if current_price <= buy_price and self.last_action_price > buy_price:
                signals.append({
                    'side': 'buy',
                    'price': buy_price,
                    'quantity': self.quantity
                })
                LOG.info(f"📈 BUY signal at {buy_price:.2f} USDT")
        
        # SELL signals - when price crosses above sell levels (only if we have position)
        if position_qty > 0:
            for sell_price in self.sell_levels:
                if current_price >= sell_price and self.last_action_price < sell_price:
                    # Only sell up to available quantity
                    sell_qty = min(self.quantity, position_qty)
                    signals.append({
                        'side': 'sell',
                        'price': sell_price,
                        'quantity': sell_qty
                    })
                    LOG.info(f"📉 SELL signal at {sell_price:.2f} USDT")
                    position_qty -= sell_qty
        
        self.last_action_price = current_price
        return signals
    
    def update_profit(self, pnl: float):
        """Update total profit"""
        self.total_profit += pnl
        self.trades_count += 1


def main():
    """Lance le paper trading Infinity Grid"""
    
    print("=" * 70)
    print("🔥 SMARTORDER PRO - INFINITY GRID PAPER TRADING")
    print("=" * 70)
    print()
    
    # Initialize Paper Trading Engine
    engine = PaperTradingEngine(
        initial_balance=10000.0,
        data_file="/opt/smartorder-pro/data/paper_trading.json"
    )
    
    # Get current BTC price
    current_price = engine.price_provider.get_price("BTCUSDT")
    if not current_price:
        LOG.error("❌ Cannot fetch BTC price")
        return
    
    LOG.info(f"📊 Current BTC price: {current_price:.2f} USDT")
    
    # Initialize Infinity Grid Strategy
    # Configuration optimisée pour meilleur Win Rate
    strategy = InfinityGridStrategy(
        symbol="BTCUSDT",
        base_price=current_price,
        grid_spacing=2.5,  # 2.5% entre chaque niveau (optimal)
        grid_levels=6,     # 6 niveaux up + 6 down = 12 grilles
        quantity_per_grid=0.003  # 0.003 BTC = ~350 USDT par trade
    )
    
    # Get initial balance
    balance = engine.get_balance()
    print()
    print(f"💰 Starting Balance: {balance['balance']:.2f} USDT")
    print(f"📊 Total Value: {balance['total_value']:.2f} USDT")
    print()
    print("🚀 Starting Infinity Grid... (Press Ctrl+C to stop)")
    print("-" * 70)
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            time.sleep(10)  # Check every 10 seconds
            
            # Get current price
            current_price = engine.price_provider.get_price("BTCUSDT")
            if not current_price:
                LOG.warning("⚠️ Could not fetch price, retrying...")
                time.sleep(5)
                continue
            
            # Get current positions
            positions = engine.get_positions()
            
            # Get signals from strategy
            signals = strategy.get_signals(current_price, positions)
            
            # Execute signals
            for signal in signals:
                result = engine.place_order(
                    symbol="BTCUSDT",
                    side=signal['side'],
                    order_type="market",
                    quantity=signal['quantity'],
                    strategy="Infinity Grid"
                )
                
                if result['success']:
                    LOG.info(f"✅ Order executed: {result}")
                    
                    # Calculate profit for sell orders
                    if signal['side'] == 'sell':
                        # Rough PNL estimate
                        pnl = signal['quantity'] * current_price * 0.025  # ~2.5% profit per grid
                        strategy.update_profit(pnl)
                        LOG.info(f"💰 PNL: +{pnl:.2f} USDT | Total: {strategy.total_profit:.2f}")
                else:
                    LOG.error(f"❌ Order failed: {result}")
            
            # Display status every 10 iterations
            if iteration % 10 == 0:
                balance = engine.get_balance()
                print()
                print(f"📊 Status Update (Iteration {iteration})")
                print(f"   Current Price: {current_price:.2f} USDT")
                print(f"   Balance: {balance['balance']:.2f} USDT")
                print(f"   Total Value: {balance['total_value']:.2f} USDT")
                print(f"   Total Profit: {strategy.total_profit:.2f} USDT")
                print(f"   Trades: {strategy.trades_count}")
                print()
    
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("🛑 Stopping Infinity Grid...")
        print("=" * 70)
        
        # Final stats
        balance = engine.get_balance()
        stats = engine.get_statistics()
        
        print()
        print("📊 FINAL STATISTICS")
        print(f"   Final Balance: {balance['balance']:.2f} USDT")
        print(f"   Total Value: {balance['total_value']:.2f} USDT")
        print(f"   Total PNL: {balance['total_pnl']:.2f} USDT")
        print(f"   PNL %: {balance['pnl_percent']:.2f}%")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.2f}%")
        print()


if __name__ == "__main__":
    main()
