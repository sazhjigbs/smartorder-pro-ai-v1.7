#!/usr/bin/env python3
"""
🚀 SMARTORDER PRO - ALL STRATEGIES PAPER TRADING
Teste toutes les stratégies du dashboard en mode simulation
"""
import ccxt
import pandas as pd
import numpy as np
import ta
import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, List

class PaperTradingEngine:
    """Moteur paper trading unifié"""
    def __init__(self, initial_balance: float = 10000):
        self.balance_usdt = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}  # {symbol: {'amount': float, 'entry_price': float, 'strategy': str}}
        self.trades_history = []
        self.pnl_by_strategy = {
            'Grid Trading': 0.0,
            'DCA Strategy': 0.0,
            'Scalping': 0.0,
            'Trend Following': 0.0
        }
        
    def buy(self, symbol: str, amount_usdt: float, price: float, strategy: str):
        """Achat paper"""
        if amount_usdt > self.balance_usdt:
            return {'success': False, 'reason': 'Insufficient balance'}
        
        amount_coin = amount_usdt / price
        self.balance_usdt -= amount_usdt
        
        if symbol not in self.positions:
            self.positions[symbol] = {'amount': 0, 'entry_price': 0, 'strategy': strategy}
        
        old_amount = self.positions[symbol]['amount']
        new_amount = old_amount + amount_coin
        avg_price = ((old_amount * self.positions[symbol]['entry_price']) + (amount_coin * price)) / new_amount if new_amount > 0 else price
        
        self.positions[symbol] = {
            'amount': new_amount,
            'entry_price': avg_price,
            'strategy': strategy
        }
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'side': 'BUY',
            'amount': amount_coin,
            'price': price,
            'cost': amount_usdt
        }
        self.trades_history.append(trade)
        return {'success': True, 'trade': trade}
    
    def sell(self, symbol: str, amount_coin: float, price: float, strategy: str):
        """Vente paper"""
        if symbol not in self.positions or self.positions[symbol]['amount'] < amount_coin:
            return {'success': False, 'reason': 'Insufficient position'}
        
        revenue = amount_coin * price
        entry_price = self.positions[symbol]['entry_price']
        pnl = (price - entry_price) * amount_coin
        
        self.balance_usdt += revenue
        self.positions[symbol]['amount'] -= amount_coin
        self.pnl_by_strategy[strategy] += pnl
        
        if self.positions[symbol]['amount'] < 0.0001:
            del self.positions[symbol]
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'side': 'SELL',
            'amount': amount_coin,
            'price': price,
            'revenue': revenue,
            'pnl': pnl
        }
        self.trades_history.append(trade)
        return {'success': True, 'trade': trade}


class StrategyRunner:
    """Execute toutes les stratégies"""
    def __init__(self):
        self.exchange = ccxt.bybit({'enableRateLimit': True})
        self.paper_engine = PaperTradingEngine(initial_balance=10000)
        self.active_strategies = []
        self.state_file = '/opt/smartorder-pro/data/state.json'
        
    def fetch_market_data(self, symbol='BTC/USDT'):
        """Données marché réelles"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def calculate_indicators(self, df):
        """Indicateurs techniques"""
        return {
            'price': df['close'].iloc[-1],
            'rsi': ta.momentum.rsi(df['close'], window=14).iloc[-1],
            'macd_hist': ta.trend.MACD(df['close']).macd_diff().iloc[-1],
            'bb_upper': ta.volatility.BollingerBands(df['close']).bollinger_hband().iloc[-1],
            'bb_lower': ta.volatility.BollingerBands(df['close']).bollinger_lband().iloc[-1],
            'ema_20': ta.trend.ema_indicator(df['close'], window=20).iloc[-1],
            'volume': df['volume'].iloc[-1]
        }
    
    def run_grid_trading(self, symbol='BTC/USDT'):
        """Stratégie Grid Trading"""
        df = self.fetch_market_data(symbol)
        ind = self.calculate_indicators(df)
        price = ind['price']
        
        # Grid simple: acheter tous les -1%, vendre tous les +1%
        if symbol not in self.paper_engine.positions:
            # Pas de position, on achète
            self.paper_engine.buy(symbol, 500, price, 'Grid Trading')
            print(f"   🟢 Grid: BUY @ ${price:.2f}")
        else:
            pos = self.paper_engine.positions[symbol]
            profit_pct = ((price - pos['entry_price']) / pos['entry_price']) * 100
            
            if profit_pct >= 1.0:  # +1% profit
                amount = pos['amount'] * 0.5  # Vendre 50%
                result = self.paper_engine.sell(symbol, amount, price, 'Grid Trading')
                if result['success']:
                    print(f"   🔴 Grid: SELL @ ${price:.2f} | PnL: ${result['trade']['pnl']:.2f}")
    
    def run_dca_strategy(self, symbol='BTC/USDT'):
        """Stratégie DCA"""
        df = self.fetch_market_data(symbol)
        ind = self.calculate_indicators(df)
        price = ind['price']
        rsi = ind['rsi']
        
        # DCA: acheter quand RSI < 40
        if rsi < 40:
            self.paper_engine.buy(symbol, 300, price, 'DCA Strategy')
            print(f"   💰 DCA: BUY @ ${price:.2f} (RSI={rsi:.1f})")
    
    def run_scalping(self, symbol='BTC/USDT'):
        """Stratégie Scalping"""
        df = self.fetch_market_data(symbol)
        ind = self.calculate_indicators(df)
        price = ind['price']
        
        # Scalp: petits trades rapides
        if symbol in self.paper_engine.positions:
            pos = self.paper_engine.positions[symbol]
            if pos['strategy'] == 'Scalping':
                profit_pct = ((price - pos['entry_price']) / pos['entry_price']) * 100
                if profit_pct >= 0.3:  # +0.3% profit rapide
                    result = self.paper_engine.sell(symbol, pos['amount'], price, 'Scalping')
                    if result['success']:
                        print(f"   ⚡ Scalp: SELL @ ${price:.2f} | PnL: ${result['trade']['pnl']:.2f}")
        else:
            # Ouvrir position scalping
            self.paper_engine.buy(symbol, 200, price, 'Scalping')
            print(f"   ⚡ Scalp: BUY @ ${price:.2f}")
    
    def run_trend_following(self, symbol='BTC/USDT'):
        """Stratégie Trend Following"""
        df = self.fetch_market_data(symbol)
        ind = self.calculate_indicators(df)
        price = ind['price']
        macd = ind['macd_hist']
        ema = ind['ema_20']
        
        # Trend: suivre la tendance EMA + MACD
        if macd > 0 and price > ema:
            if symbol not in self.paper_engine.positions or self.paper_engine.positions[symbol]['strategy'] != 'Trend Following':
                self.paper_engine.buy(symbol, 400, price, 'Trend Following')
                print(f"   📈 Trend: BUY @ ${price:.2f} (MACD+)")
        elif macd < 0 and symbol in self.paper_engine.positions:
            pos = self.paper_engine.positions[symbol]
            if pos['strategy'] == 'Trend Following':
                result = self.paper_engine.sell(symbol, pos['amount'], price, 'Trend Following')
                if result['success']:
                    print(f"   📉 Trend: SELL @ ${price:.2f} | PnL: ${result['trade']['pnl']:.2f}")
    
    def update_state(self):
        """Mise à jour état pour dashboard"""
        df = self.fetch_market_data()
        current_price = df['close'].iloc[-1]
        
        total_value = self.paper_engine.balance_usdt
        for symbol, pos in self.paper_engine.positions.items():
            if 'BTC' in symbol:
                total_value += pos['amount'] * current_price
        
        total_pnl = total_value - self.paper_engine.initial_balance
        
        state = {
            'mode': 'PAPER',
            'paused': False,
            'active_strategies': self.active_strategies,
            'balance': self.paper_engine.balance_usdt,
            'total_value': total_value,
            'pnl': {
                'total': total_pnl,
                'daily': total_pnl,
                'weekly': total_pnl,
                'monthly': total_pnl,
                'by_strategy': self.paper_engine.pnl_by_strategy
            },
            'positions': [
                {
                    'symbol': sym,
                    'strategy': pos['strategy'],
                    'amount': pos['amount'],
                    'entry_price': pos['entry_price'],
                    'current_price': current_price if 'BTC' in sym else 0,
                    'pnl': (current_price - pos['entry_price']) * pos['amount'] if 'BTC' in sym else 0
                }
                for sym, pos in self.paper_engine.positions.items()
            ],
            'trades_count': len(self.paper_engine.trades_history),
            'last_update': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def run_cycle(self):
        """Execute un cycle complet"""
        print(f"\n{'='*80}")
        print(f"🔄 Cycle {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        
        try:
            # Charger stratégies actives depuis state
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.active_strategies = state.get('active_strategies', [])
            
            # Execute stratégies actives
            if 'Grid Trading' in self.active_strategies:
                self.run_grid_trading()
            
            if 'DCA Strategy' in self.active_strategies:
                self.run_dca_strategy()
            
            if 'Scalping' in self.active_strategies:
                self.run_scalping()
            
            if 'Trend Following' in self.active_strategies:
                self.run_trend_following()
            
            # Update state
            self.update_state()
            
            # Display stats
            df = self.fetch_market_data()
            price = df['close'].iloc[-1]
            total_value = self.paper_engine.balance_usdt
            for pos in self.paper_engine.positions.values():
                total_value += pos['amount'] * price
            
            pnl = total_value - self.paper_engine.initial_balance
            
            print(f"\n💰 WALLET:")
            print(f"   Balance: ${self.paper_engine.balance_usdt:.2f}")
            print(f"   Valeur totale: ${total_value:.2f}")
            print(f"   PnL: ${pnl:.2f} ({(pnl/self.paper_engine.initial_balance)*100:+.2f}%)")
            print(f"   Positions: {len(self.paper_engine.positions)}")
            print(f"   Trades: {len(self.paper_engine.trades_history)}")
            
            print(f"\n📊 PnL par stratégie:")
            for strat, pnl_val in self.paper_engine.pnl_by_strategy.items():
                if pnl_val != 0:
                    print(f"   {strat}: ${pnl_val:.2f}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self, interval=60):
        """Lance le runner"""
        print(f"\n{'='*80}")
        print("🚀 SMARTORDER PRO - ALL STRATEGIES PAPER TRADING")
        print(f"{'='*80}")
        print(f"Capital initial: ${self.paper_engine.initial_balance:.2f}")
        print(f"Interval: {interval}s")
        print("\nStratégies disponibles:")
        print("  - Grid Trading")
        print("  - DCA Strategy")
        print("  - Scalping")
        print("  - Trend Following")
        print("\n▶️  Démarrez les stratégies depuis le dashboard!")
        
        while True:
            try:
                self.run_cycle()
                print(f"\n⏳ Prochain cycle dans {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\n⚠️ Arrêt manuel")
                break
            except Exception as e:
                print(f"\n❌ Erreur globale: {e}")
                time.sleep(interval)


if __name__ == '__main__':
    import os
    os.makedirs('/opt/smartorder-pro/data', exist_ok=True)
    
    runner = StrategyRunner()
    runner.run(interval=30)
