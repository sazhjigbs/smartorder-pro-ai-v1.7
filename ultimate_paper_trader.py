#!/usr/bin/env python3
"""
🚀 ULTIMATE PAPER TRADER
Indicateurs 100% réels + Exécution paper trading complète
"""
import ccxt
import pandas as pd
import numpy as np
import ta
import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class PaperWallet:
    """Wallet virtuel pour paper trading"""
    def __init__(self, initial_balance: float = 10000):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}  # {symbol: {'amount': float, 'entry_price': float}}
        self.orders_history = []
        self.trades_history = []
        
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calcule valeur totale (balance + positions)"""
        total = self.balance
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                total += pos['amount'] * current_prices[symbol]
        return total
    
    def get_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calcule PnL total"""
        return self.get_total_value(current_prices) - self.initial_balance
    
    def buy(self, symbol: str, amount: float, price: float) -> Dict:
        """Exécute achat paper"""
        cost = amount * price
        if cost > self.balance:
            return {'success': False, 'reason': 'Insufficient balance'}
        
        self.balance -= cost
        if symbol not in self.positions:
            self.positions[symbol] = {'amount': 0, 'entry_price': 0}
        
        old_amount = self.positions[symbol]['amount']
        new_amount = old_amount + amount
        # Prix d'entrée moyen pondéré
        avg_price = ((old_amount * self.positions[symbol]['entry_price']) + (amount * price)) / new_amount if new_amount > 0 else price
        
        self.positions[symbol] = {
            'amount': new_amount,
            'entry_price': avg_price
        }
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': 'BUY',
            'amount': amount,
            'price': price,
            'cost': cost,
            'balance_after': self.balance
        }
        self.trades_history.append(trade)
        
        return {'success': True, 'trade': trade}
    
    def sell(self, symbol: str, amount: float, price: float) -> Dict:
        """Exécute vente paper"""
        if symbol not in self.positions or self.positions[symbol]['amount'] < amount:
            return {'success': False, 'reason': 'Insufficient position'}
        
        revenue = amount * price
        self.balance += revenue
        self.positions[symbol]['amount'] -= amount
        
        if self.positions[symbol]['amount'] <= 0.0001:
            del self.positions[symbol]
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': 'SELL',
            'amount': amount,
            'price': price,
            'revenue': revenue,
            'balance_after': self.balance
        }
        self.trades_history.append(trade)
        
        return {'success': True, 'trade': trade}


class UltimatePaperTrader:
    """Bot ultime avec exécution complète paper trading"""
    
    def __init__(self, symbol: str = 'BTC/USDT', initial_capital: float = 10000):
        self.symbol = symbol
        self.symbol_clean = symbol.replace('/', '')
        
        # Wallet paper
        self.wallet = PaperWallet(initial_capital)
        
        # Exchange RÉEL (données seulement)
        self.exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # DB pour persistence
        self.db_path = '/opt/smartorder-pro/data/ultimate_paper.db'
        self.init_database()
        
        # Trading params
        self.min_order_size = 0.001  # BTC
        self.position_size_pct = 0.1  # 10% du capital par trade
        
        print(f"✅ Ultimate Paper Trader initialisé")
        print(f"   Symbol: {symbol}")
        print(f"   Capital: ${initial_capital:.2f}")
    
    def init_database(self):
        """Initialise DB SQLite pour logs"""
        import os
        os.makedirs('/opt/smartorder-pro/data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                amount REAL,
                price REAL,
                value REAL,
                pnl REAL,
                balance_after REAL
            )
        ''')
        
        # Table signals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                regime TEXT,
                action TEXT,
                confidence REAL,
                reason TEXT,
                price REAL,
                rsi REAL,
                macd REAL,
                adx REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_real_data(self, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Récupère données réelles"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"❌ Erreur fetch data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calcule indicateurs techniques"""
        rsi = ta.momentum.rsi(df['close'], window=14)
        
        macd_obj = ta.trend.MACD(df['close'])
        macd = macd_obj.macd()
        macd_signal = macd_obj.macd_signal()
        macd_hist = macd_obj.macd_diff()
        
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        bb_upper = bb.bollinger_hband()
        bb_middle = bb.bollinger_mavg()
        bb_lower = bb.bollinger_lband()
        
        atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        adx = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
        
        ema_20 = ta.trend.ema_indicator(df['close'], window=20)
        ema_50 = ta.trend.ema_indicator(df['close'], window=50)
        
        current_price = df['close'].iloc[-1]
        volatility = df['close'].pct_change().std() * np.sqrt(24)
        
        return {
            'price': current_price,
            'rsi': rsi.iloc[-1],
            'macd': macd.iloc[-1],
            'macd_signal': macd_signal.iloc[-1],
            'macd_hist': macd_hist.iloc[-1],
            'bb_upper': bb_upper.iloc[-1],
            'bb_middle': bb_middle.iloc[-1],
            'bb_lower': bb_lower.iloc[-1],
            'atr': atr.iloc[-1],
            'adx': adx.iloc[-1],
            'ema_20': ema_20.iloc[-1],
            'ema_50': ema_50.iloc[-1],
            'volatility': volatility,
            'timestamp': datetime.now()
        }
    
    def detect_market_regime(self, indicators: Dict) -> str:
        """Détecte régime marché"""
        rsi = indicators['rsi']
        adx = indicators['adx']
        macd_hist = indicators['macd_hist']
        volatility = indicators['volatility']
        price = indicators['price']
        ema_20 = indicators['ema_20']
        ema_50 = indicators['ema_50']
        
        if volatility > 0.05:
            return 'volatile'
        
        if adx > 25:
            if macd_hist > 0 and price > ema_20 > ema_50:
                return 'trending_up'
            elif macd_hist < 0 and price < ema_20 < ema_50:
                return 'trending_down'
        
        return 'ranging'
    
    def generate_signal(self, indicators: Dict) -> Dict:
        """Génère signal de trading"""
        rsi = indicators['rsi']
        macd_hist = indicators['macd_hist']
        price = indicators['price']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        regime = self.detect_market_regime(indicators)
        
        signal = {
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': '',
            'regime': regime,
            'price': price
        }
        
        # Stratégies
        if regime == 'ranging':
            if price <= bb_lower * 1.005 and rsi < 35:
                signal = {
                    'action': 'BUY',
                    'confidence': 0.85,
                    'reason': f'Oversold: RSI={rsi:.1f}, BB lower',
                    'regime': regime,
                    'price': price
                }
            elif price >= bb_upper * 0.995 and rsi > 65:
                signal = {
                    'action': 'SELL',
                    'confidence': 0.85,
                    'reason': f'Overbought: RSI={rsi:.1f}, BB upper',
                    'regime': regime,
                    'price': price
                }
        
        elif regime == 'trending_up':
            if macd_hist > 0 and rsi < 65 and rsi > 40:
                signal = {
                    'action': 'BUY',
                    'confidence': 0.75,
                    'reason': 'Trend following: MACD+, uptrend',
                    'regime': regime,
                    'price': price
                }
        
        elif regime == 'trending_down':
            if macd_hist < 0 and rsi > 35:
                signal = {
                    'action': 'SELL',
                    'confidence': 0.70,
                    'reason': 'Trend following: MACD-, downtrend',
                    'regime': regime,
                    'price': price
                }
        
        # Log signal dans DB
        self.log_signal(signal, indicators)
        
        return signal
    
    def execute_signal(self, signal: Dict, indicators: Dict):
        """Exécute signal en paper trading"""
        if signal['action'] == 'HOLD' or signal['confidence'] < 0.7:
            return
        
        price = indicators['price']
        current_value = self.wallet.get_total_value({self.symbol: price})
        
        if signal['action'] == 'BUY':
            # Calculer taille position
            buy_value = current_value * self.position_size_pct
            amount = buy_value / price
            
            if amount >= self.min_order_size:
                result = self.wallet.buy(self.symbol, amount, price)
                if result['success']:
                    print(f"   ✅ BUY EXECUTED: {amount:.6f} BTC @ ${price:.2f}")
                    self.log_trade(result['trade'])
                else:
                    print(f"   ❌ BUY FAILED: {result['reason']}")
        
        elif signal['action'] == 'SELL':
            # Vendre position actuelle si elle existe
            if self.symbol in self.wallet.positions:
                pos = self.wallet.positions[self.symbol]
                amount = pos['amount'] * 0.5  # Vendre 50%
                
                if amount >= self.min_order_size:
                    result = self.wallet.sell(self.symbol, amount, price)
                    if result['success']:
                        entry_price = pos['entry_price']
                        pnl = (price - entry_price) * amount
                        print(f"   ✅ SELL EXECUTED: {amount:.6f} BTC @ ${price:.2f} | PnL: ${pnl:.2f}")
                        self.log_trade(result['trade'], pnl)
                    else:
                        print(f"   ❌ SELL FAILED: {result['reason']}")
    
    def log_trade(self, trade: Dict, pnl: float = 0.0):
        """Log trade dans DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, side, amount, price, value, pnl, balance_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['timestamp'],
            trade['symbol'],
            trade['side'],
            trade['amount'],
            trade['price'],
            trade.get('cost', trade.get('revenue', 0)),
            pnl,
            trade['balance_after']
        ))
        conn.commit()
        conn.close()
    
    def log_signal(self, signal: Dict, indicators: Dict):
        """Log signal dans DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO signals (timestamp, symbol, regime, action, confidence, reason, price, rsi, macd, adx)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            self.symbol,
            signal['regime'],
            signal['action'],
            signal['confidence'],
            signal['reason'],
            signal['price'],
            indicators['rsi'],
            indicators['macd_hist'],
            indicators['adx']
        ))
        conn.commit()
        conn.close()
    
    def run_cycle(self):
        """Execute un cycle complet"""
        print(f"\n{'='*80}")
        print(f"🔄 Cycle {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # 1. Fetch data
        df = self.fetch_real_data()
        if df.empty:
            print("❌ Pas de données")
            return
        
        # 2. Calculate indicators
        indicators = self.calculate_indicators(df)
        
        # 3. Generate signal
        signal = self.generate_signal(indicators)
        
        # 4. Display info
        price = indicators['price']
        print(f"\n📊 MARCHÉ:")
        print(f"   Prix: ${price:.2f}")
        print(f"   RSI: {indicators['rsi']:.2f} | MACD: {indicators['macd_hist']:.2f} | ADX: {indicators['adx']:.2f}")
        print(f"   Régime: {signal['regime'].upper()}")
        
        print(f"\n🚦 SIGNAL:")
        print(f"   Action: {signal['action']} ({signal['confidence']*100:.0f}%)")
        print(f"   Raison: {signal['reason']}")
        
        # 5. Execute signal
        if signal['action'] != 'HOLD':
            self.execute_signal(signal, indicators)
        
        # 6. Display wallet
        total_value = self.wallet.get_total_value({self.symbol: price})
        pnl = self.wallet.get_pnl({self.symbol: price})
        pnl_pct = (pnl / self.wallet.initial_balance) * 100
        
        print(f"\n💰 WALLET:")
        print(f"   Balance: ${self.wallet.balance:.2f}")
        if self.symbol in self.wallet.positions:
            pos = self.wallet.positions[self.symbol]
            pos_value = pos['amount'] * price
            print(f"   Position: {pos['amount']:.6f} BTC (${pos_value:.2f}) @ ${pos['entry_price']:.2f}")
        print(f"   Valeur totale: ${total_value:.2f}")
        print(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"   Trades: {len(self.wallet.trades_history)}")
    
    def run(self, cycles: int = 100, interval: int = 60):
        """Lance le bot"""
        print(f"\n{'='*80}")
        print(f"🚀 ULTIMATE PAPER TRADER - DÉMARRAGE")
        print(f"{'='*80}")
        
        for i in range(cycles):
            try:
                self.run_cycle()
                if i < cycles - 1:
                    print(f"\n⏳ Prochaine analyse dans {interval}s...")
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\n⚠️ Arrêt manuel")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval)
        
        # Summary
        price = self.exchange.fetch_ticker(self.symbol)['last']
        total_value = self.wallet.get_total_value({self.symbol: price})
        pnl = self.wallet.get_pnl({self.symbol: price})
        
        print(f"\n{'='*80}")
        print(f"📊 RÉSUMÉ FINAL")
        print(f"{'='*80}")
        print(f"Capital initial: ${self.wallet.initial_balance:.2f}")
        print(f"Valeur finale: ${total_value:.2f}")
        print(f"PnL: ${pnl:.2f} ({(pnl/self.wallet.initial_balance)*100:+.2f}%)")
        print(f"Trades: {len(self.wallet.trades_history)}")


if __name__ == '__main__':
    trader = UltimatePaperTrader(symbol='BTC/USDT', initial_capital=10000)
    trader.run(cycles=10, interval=30)
