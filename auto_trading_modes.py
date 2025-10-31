#!/usr/bin/env python3
"""
AUTO TRADING MODES - SPOT & FUTURES
Exécution automatique avec gestion de risque
"""
import ccxt
import pandas as pd
import ta
import json
import time
from datetime import datetime
from typing import Dict, List

class AutoSpotTrader:
    """Mode AUTO SPOT - Trading automatique spot"""
    def __init__(self, capital: float = 5000):
        self.capital = capital
        self.balance = capital
        self.positions = {}
        self.exchange = ccxt.bybit({'enableRateLimit': True})
        self.max_position_size = capital * 0.2  # Max 20% par position
        self.active = False
        
    def analyze_spot_opportunity(self, symbol='BTC/USDT'):
        """Analyse opportunité spot"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Indicateurs
            rsi = ta.momentum.rsi(df['close'], window=14).iloc[-1]
            macd_hist = ta.trend.MACD(df['close']).macd_diff().iloc[-1]
            bb = ta.volatility.BollingerBands(df['close'])
            price = df['close'].iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            bb_upper = bb.bollinger_hband().iloc[-1]
            
            # Signaux AUTO SPOT
            signal = None
            confidence = 0
            
            # ACHAT: RSI bas + prix proche BB lower
            if rsi < 35 and price <= bb_lower * 1.01:
                signal = 'BUY'
                confidence = 0.8
                
            # VENTE: RSI haut + prix proche BB upper
            elif rsi > 65 and price >= bb_upper * 0.99:
                signal = 'SELL'
                confidence = 0.8
            
            return {
                'signal': signal,
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'reason': f'RSI={rsi:.1f}, BB position'
            }
        except Exception as e:
            print(f"Erreur analyse spot: {e}")
            return None
    
    def execute_spot_trade(self, signal_data):
        """Exécute trade spot en paper"""
        if not signal_data or not signal_data['signal']:
            return None
            
        signal = signal_data['signal']
        price = signal_data['price']
        symbol = 'BTC/USDT'
        
        if signal == 'BUY' and self.balance > 0:
            amount_usdt = min(self.max_position_size, self.balance)
            amount_btc = amount_usdt / price
            
            self.balance -= amount_usdt
            if symbol not in self.positions:
                self.positions[symbol] = {'amount': 0, 'entry_price': 0}
            
            old_amount = self.positions[symbol]['amount']
            new_amount = old_amount + amount_btc
            avg_price = ((old_amount * self.positions[symbol]['entry_price']) + (amount_btc * price)) / new_amount if new_amount > 0 else price
            
            self.positions[symbol] = {'amount': new_amount, 'entry_price': avg_price}
            
            return {
                'type': 'SPOT BUY',
                'symbol': symbol,
                'amount': amount_btc,
                'price': price,
                'cost': amount_usdt
            }
            
        elif signal == 'SELL' and symbol in self.positions:
            pos = self.positions[symbol]
            amount = pos['amount'] * 0.5  # Vendre 50%
            revenue = amount * price
            pnl = (price - pos['entry_price']) * amount
            
            self.balance += revenue
            self.positions[symbol]['amount'] -= amount
            
            if self.positions[symbol]['amount'] < 0.0001:
                del self.positions[symbol]
            
            return {
                'type': 'SPOT SELL',
                'symbol': symbol,
                'amount': amount,
                'price': price,
                'revenue': revenue,
                'pnl': pnl
            }
        
        return None


class AutoFuturesTrader:
    """Mode AUTO FUTURES - Trading automatique futures avec levier"""
    def __init__(self, capital: float = 5000):
        self.capital = capital
        self.balance = capital
        self.positions = {}
        self.exchange = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        self.max_leverage = 3  # Levier max 3x pour sécurité
        self.max_position_size = capital * 0.3  # Max 30% par position
        self.active = False
        
    def analyze_futures_opportunity(self, symbol='BTC/USDT:USDT'):
        """Analyse opportunité futures"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Indicateurs futures
            rsi = ta.momentum.rsi(df['close'], window=14).iloc[-1]
            macd = ta.trend.MACD(df['close'])
            macd_hist = macd.macd_diff().iloc[-1]
            ema_20 = ta.trend.ema_indicator(df['close'], window=20).iloc[-1]
            ema_50 = ta.trend.ema_indicator(df['close'], window=50).iloc[-1]
            price = df['close'].iloc[-1]
            
            # Signaux AUTO FUTURES (plus agressifs)
            signal = None
            side = None
            confidence = 0
            
            # LONG: Tendance haussière forte
            if macd_hist > 0 and price > ema_20 > ema_50 and rsi > 45 and rsi < 70:
                signal = 'OPEN'
                side = 'LONG'
                confidence = 0.75
                
            # SHORT: Tendance baissière forte  
            elif macd_hist < 0 and price < ema_20 < ema_50 and rsi < 55 and rsi > 30:
                signal = 'OPEN'
                side = 'SHORT'
                confidence = 0.75
            
            # CLOSE: Inverse de tendance
            elif macd_hist < 0 and rsi < 40:
                signal = 'CLOSE'
                side = 'LONG'
                
            elif macd_hist > 0 and rsi > 60:
                signal = 'CLOSE'
                side = 'SHORT'
            
            return {
                'signal': signal,
                'side': side,
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'macd_hist': macd_hist,
                'reason': f'MACD={macd_hist:.2f}, RSI={rsi:.1f}'
            }
        except Exception as e:
            print(f"Erreur analyse futures: {e}")
            return None
    
    def execute_futures_trade(self, signal_data):
        """Exécute trade futures en paper"""
        if not signal_data or not signal_data['signal']:
            return None
            
        signal = signal_data['signal']
        side = signal_data['side']
        price = signal_data['price']
        symbol = 'BTC/USDT:USDT'
        
        if signal == 'OPEN':
            position_size = min(self.max_position_size, self.balance * 0.5)
            leverage_amount = position_size * self.max_leverage
            amount_btc = leverage_amount / price
            
            if symbol not in self.positions or self.positions[symbol]['side'] != side:
                self.positions[symbol] = {
                    'side': side,
                    'amount': amount_btc,
                    'entry_price': price,
                    'leverage': self.max_leverage,
                    'margin': position_size
                }
                
                return {
                    'type': f'FUTURES {side}',
                    'symbol': symbol,
                    'amount': amount_btc,
                    'price': price,
                    'leverage': self.max_leverage,
                    'margin': position_size
                }
        
        elif signal == 'CLOSE' and symbol in self.positions:
            pos = self.positions[symbol]
            if pos['side'] == side:
                amount = pos['amount']
                pnl = (price - pos['entry_price']) * amount if side == 'LONG' else (pos['entry_price'] - price) * amount
                
                self.balance += pos['margin'] + pnl
                del self.positions[symbol]
                
                return {
                    'type': f'FUTURES CLOSE {side}',
                    'symbol': symbol,
                    'amount': amount,
                    'price': price,
                    'pnl': pnl
                }
        
        return None


class AutoTradingManager:
    """Gestionnaire des modes AUTO"""
    def __init__(self):
        self.spot_trader = AutoSpotTrader(capital=5000)
        self.futures_trader = AutoFuturesTrader(capital=5000)
        self.mode = 'SPOT'  # SPOT, FUTURES, HYBRID
        self.state_file = '/opt/smartorder-pro/data/auto_trading_state.json'
        
    def set_mode(self, mode: str):
        """Change mode: SPOT, FUTURES, HYBRID"""
        self.mode = mode.upper()
        self.spot_trader.active = mode in ['SPOT', 'HYBRID']
        self.futures_trader.active = mode in ['FUTURES', 'HYBRID']
        
    def run_cycle(self):
        """Execute cycle auto trading"""
        trades = []
        
        # AUTO SPOT
        if self.spot_trader.active:
            spot_signal = self.spot_trader.analyze_spot_opportunity()
            if spot_signal and spot_signal['signal']:
                trade = self.spot_trader.execute_spot_trade(spot_signal)
                if trade:
                    trades.append(trade)
                    print(f"✅ {trade['type']}: {trade['amount']:.6f} @ ${trade['price']:.2f}")
        
        # AUTO FUTURES
        if self.futures_trader.active:
            futures_signal = self.futures_trader.analyze_futures_opportunity()
            if futures_signal and futures_signal['signal']:
                trade = self.futures_trader.execute_futures_trade(futures_signal)
                if trade:
                    trades.append(trade)
                    print(f"✅ {trade['type']}: {trade['amount']:.6f} @ ${trade['price']:.2f}")
        
        # Save state
        self.save_state()
        
        return trades
    
    def save_state(self):
        """Sauvegarde état"""
        state = {
            'mode': self.mode,
            'spot': {
                'balance': self.spot_trader.balance,
                'positions': self.spot_trader.positions,
                'capital': self.spot_trader.capital
            },
            'futures': {
                'balance': self.futures_trader.balance,
                'positions': self.futures_trader.positions,
                'capital': self.futures_trader.capital
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def run(self, interval=60):
        """Lance auto trading"""
        print(f"\n{'='*80}")
        print("🚀 AUTO TRADING - SPOT & FUTURES")
        print(f"{'='*80}")
        print(f"Mode: {self.mode}")
        print(f"SPOT Capital: ${self.spot_trader.capital}")
        print(f"FUTURES Capital: ${self.futures_trader.capital}")
        
        while True:
            try:
                print(f"\n🔄 Cycle {datetime.now().strftime('%H:%M:%S')}")
                
                trades = self.run_cycle()
                
                # Stats
                spot_value = self.spot_trader.balance
                for pos in self.spot_trader.positions.values():
                    spot_value += pos['amount'] * 114000  # Approx
                
                spot_pnl = spot_value - self.spot_trader.capital
                futures_pnl = self.futures_trader.balance - self.futures_trader.capital
                
                print(f"💰 SPOT: ${spot_value:.2f} | PnL: ${spot_pnl:+.2f}")
                print(f"💰 FUTURES: ${self.futures_trader.balance:.2f} | PnL: ${futures_pnl:+.2f}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n⚠️ Arrêt")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                time.sleep(interval)


if __name__ == '__main__':
    import sys
    
    manager = AutoTradingManager()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'HYBRID'
    manager.set_mode(mode)
    manager.run(interval=30)
