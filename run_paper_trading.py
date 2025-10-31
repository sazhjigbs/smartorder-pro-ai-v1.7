#!/usr/bin/env python3
"""
🎮 SmartOrder PRO - Paper Trading Live
======================================
Lance le paper trading en temps réel avec Grid Strategy

Author: MAIGA ABOUBACAR
"""

import sys
import time
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.paper_trading_engine_v2 import PaperTradingEngine
from strategies.grid_trading_strategy import GridTradingStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/paper_trading.log'),
        logging.StreamHandler()
    ]
)

LOG = logging.getLogger("paper_trading_live")

def main():
    """Lance le paper trading en temps réel"""
    
    print("=" * 60)
    print("🎮 SMARTORDER PRO - PAPER TRADING LIVE")
    print("=" * 60)
    print()
    
    # Initialize Paper Trading Engine
    engine = PaperTradingEngine(
        initial_balance=10000.0,
        data_file="/opt/smartorder-pro/data/paper_trading.json"
    )
    
    # Get current BTC price
    current_price = engine.price_provider.get_price("BTCUSDT")
    if not current_price:
        LOG.error("❌ Cannot fetch BTC price. Check internet connection.")
        return
    
    LOG.info(f"📊 Current BTC price: {current_price:.2f} USDT")
    
    # Initialize Grid Strategy
    # Grid autour du prix actuel +/- 5%
    lower_price = current_price * 0.95
    upper_price = current_price * 1.05
    
    strategy = GridTradingStrategy(
        symbol="BTCUSDT",
        lower_price=lower_price,
        upper_price=upper_price,
        grid_levels=10,
        quantity_per_grid=0.001,  # ~70 USDT per grid
        mode="neutral"
    )
    
    print()
    print(f"✅ Grid Strategy initialized")
    print(f"   Symbol: BTCUSDT")
    print(f"   Price Range: {lower_price:.2f} - {upper_price:.2f} USDT")
    print(f"   Grid Levels: 10")
    print(f"   Quantity per grid: 0.001 BTC")
    print(f"   Grid Spacing: {strategy.grid_spacing:.2f} USDT")
    print()
    
    # Get initial balance
    balance = engine.get_balance()
    print(f"💰 Starting Balance: {balance['balance']:.2f} USDT")
    print(f"📊 Total Value: {balance['total_value']:.2f} USDT")
    print()
    print("🚀 Starting live paper trading... (Press Ctrl+C to stop)")
    print("-" * 60)
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Get current price
            current_price = engine.price_provider.get_price("BTCUSDT")
            if not current_price:
                LOG.warning("⚠️ Could not fetch price, retrying...")
                time.sleep(5)
                continue
            
            # Get signals from strategy
            signals = strategy.get_signals(current_price)
            
            # Execute signals
            for signal in signals:
                LOG.info(f"📤 Signal: {signal['type'].upper()} @ {signal['price']:.2f}")
                
                result = engine.place_order(
                    symbol="BTCUSDT",
                    side=signal['type'],
                    order_type='market',
                    quantity=signal['quantity'],
                    strategy='Grid Trading'
                )
                
                if result['success']:
                    LOG.info(f"✅ Order executed: {result}")
                    strategy.on_fill(
                        signal['type'],
                        result['price'],
                        signal['quantity']
                    )
                else:
                    LOG.error(f"❌ Order failed: {result}")
            
            # Display stats every 10 iterations (5 minutes)
            if iteration % 10 == 0:
                balance = engine.get_balance()
                positions = engine.get_positions()
                strat_stats = strategy.get_stats()
                
                print()
                print(f"📊 Stats Update (Iteration {iteration})")
                print(f"   Current Price: {current_price:.2f} USDT")
                print(f"   Balance: {balance['balance']:.2f} USDT")
                print(f"   Total Value: {balance['total_value']:.2f} USDT")
                print(f"   PNL: {balance['pnl']:.2f} USDT ({balance['pnl_percent']:.2f}%)")
                print(f"   Open Positions: {len(positions)}")
                print(f"   Total Trades: {strat_stats['trades_count']}")
                print(f"   Strategy PNL: {strat_stats['total_pnl']:.2f} USDT")
                print()
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("🛑 Paper Trading stopped by user")
        print("=" * 60)
        print()
        
        # Final stats
        balance = engine.get_balance()
        positions = engine.get_positions()
        trades = engine.get_trades()
        strat_stats = strategy.get_stats()
        
        print("📊 FINAL STATISTICS")
        print("-" * 60)
        print(f"Starting Balance: {balance['initial_balance']:.2f} USDT")
        print(f"Final Balance: {balance['balance']:.2f} USDT")
        print(f"Total Value: {balance['total_value']:.2f} USDT")
        print(f"Total PNL: {balance['pnl']:.2f} USDT ({balance['pnl_percent']:.2f}%)")
        print()
        print(f"Total Trades: {len(trades)}")
        print(f"Open Positions: {len(positions)}")
        print()
        print(f"Strategy Stats:")
        print(f"  Grid Levels: {strat_stats['grid_levels']}")
        print(f"  Active Buy Grids: {strat_stats['active_buy_grids']}")
        print(f"  Active Sell Grids: {strat_stats['active_sell_grids']}")
        print(f"  Strategy PNL: {strat_stats['total_pnl']:.2f} USDT")
        print()
        
        if positions:
            print("Open Positions:")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['quantity']} @ {pos['entry_price']:.2f} | PNL: {pos['pnl']:.2f} ({pos['pnl_percent']:.2f}%)")
        
        print()
        print("✅ Paper trading session ended successfully")
        print()


if __name__ == "__main__":
    main()
