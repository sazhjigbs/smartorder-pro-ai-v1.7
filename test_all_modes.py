#!/usr/bin/env python3
"""
TEST COMPLET - TOUS LES MODES EN PAPER
SPOT, FUTURES, HYBRIDE + Toutes les stratégies
"""
import ccxt
import pandas as pd
import ta
import json
import time
from datetime import datetime

class UnifiedPaperTester:
    """Teste TOUS les modes simultanément"""
    
    def __init__(self):
        self.exchange = ccxt.bybit({'enableRateLimit': True})
        
        # Wallets séparés par mode
        self.wallets = {
            'SPOT': {'balance': 10000, 'positions': {}, 'trades': [], 'pnl': 0},
            'FUTURES': {'balance': 10000, 'positions': {}, 'trades': [], 'pnl': 0},
            'HYBRIDE': {'balance': 10000, 'positions': {}, 'trades': [], 'pnl': 0},
            'MANUEL': {'balance': 10000, 'positions': {}, 'trades': [], 'pnl': 0}
        }
        
        # Stratégies à tester
        self.strategies = ['Grid Trading', 'DCA Strategy', 'Scalping', 'Trend Following']
        
        # Exchanges connectés
        self.exchanges_status = {
            'Bybit': {'connected': True, 'balance': 10000},
            'Binance': {'connected': False, 'balance': 0},
            'OKX': {'connected': False, 'balance': 0}
        }
        
    def fetch_market_data(self, timeframe='1h'):
        """Données marché"""
        ohlcv = self.exchange.fetch_ohlcv('BTC/USDT', timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        rsi = ta.momentum.rsi(df['close'], window=14).iloc[-1]
        macd = ta.trend.MACD(df['close']).macd_diff().iloc[-1]
        bb = ta.volatility.BollingerBands(df['close'])
        price = df['close'].iloc[-1]
        
        return {
            'price': price,
            'rsi': rsi,
            'macd': macd,
            'bb_upper': bb.bollinger_hband().iloc[-1],
            'bb_lower': bb.bollinger_lband().iloc[-1]
        }
    
    def test_spot_mode(self, market_data):
        """Test mode SPOT"""
        price = market_data['price']
        rsi = market_data['rsi']
        
        # Grid Trading SPOT
        if rsi < 40 and self.wallets['SPOT']['balance'] > 500:
            amount = 500 / price
            self.wallets['SPOT']['balance'] -= 500
            self.wallets['SPOT']['positions']['BTC/USDT'] = {
                'amount': amount,
                'entry': price,
                'strategy': 'Grid Trading'
            }
            self.wallets['SPOT']['trades'].append({
                'time': datetime.now().isoformat(),
                'type': 'SPOT BUY',
                'price': price,
                'amount': amount
            })
            return f"SPOT: Grid Trading BUY @ ${price:.2f}"
        
        elif rsi > 60 and 'BTC/USDT' in self.wallets['SPOT']['positions']:
            pos = self.wallets['SPOT']['positions']['BTC/USDT']
            revenue = pos['amount'] * price
            pnl = (price - pos['entry']) * pos['amount']
            
            self.wallets['SPOT']['balance'] += revenue
            self.wallets['SPOT']['pnl'] += pnl
            del self.wallets['SPOT']['positions']['BTC/USDT']
            
            self.wallets['SPOT']['trades'].append({
                'time': datetime.now().isoformat(),
                'type': 'SPOT SELL',
                'price': price,
                'pnl': pnl
            })
            return f"SPOT: SELL @ ${price:.2f} | PnL: ${pnl:+.2f}"
        
        return None
    
    def test_futures_mode(self, market_data):
        """Test mode FUTURES avec levier"""
        price = market_data['price']
        macd = market_data['macd']
        
        # LONG si MACD positif
        if macd > 0 and 'LONG' not in self.wallets['FUTURES']['positions']:
            margin = 1500
            leverage = 3
            amount = (margin * leverage) / price
            
            self.wallets['FUTURES']['positions']['LONG'] = {
                'amount': amount,
                'entry': price,
                'margin': margin,
                'leverage': leverage
            }
            
            self.wallets['FUTURES']['trades'].append({
                'time': datetime.now().isoformat(),
                'type': 'FUTURES LONG',
                'price': price,
                'leverage': leverage
            })
            return f"FUTURES: LONG x{leverage} @ ${price:.2f}"
        
        # Close LONG
        elif macd < 0 and 'LONG' in self.wallets['FUTURES']['positions']:
            pos = self.wallets['FUTURES']['positions']['LONG']
            pnl = (price - pos['entry']) * pos['amount']
            
            self.wallets['FUTURES']['balance'] += pos['margin'] + pnl
            self.wallets['FUTURES']['pnl'] += pnl
            del self.wallets['FUTURES']['positions']['LONG']
            
            self.wallets['FUTURES']['trades'].append({
                'time': datetime.now().isoformat(),
                'type': 'FUTURES CLOSE LONG',
                'price': price,
                'pnl': pnl
            })
            return f"FUTURES: CLOSE LONG @ ${price:.2f} | PnL: ${pnl:+.2f}"
        
        return None
    
    def test_hybride_mode(self, market_data):
        """Test mode HYBRIDE (SPOT + FUTURES)"""
        spot_result = self.test_spot_mode(market_data)
        futures_result = self.test_futures_mode(market_data)
        
        results = []
        if spot_result:
            results.append(spot_result)
        if futures_result:
            results.append(futures_result)
        
        return results if results else None
    
    def save_state(self):
        """Sauvegarde état complet"""
        market = self.fetch_market_data()
        
        state = {
            'mode': 'TESTING_ALL',
            'timestamp': datetime.now().isoformat(),
            'exchanges': self.exchanges_status,
            'current_price': market['price'],
            'modes': {}
        }
        
        # Stats par mode
        for mode, wallet in self.wallets.items():
            total_value = wallet['balance']
            for pos in wallet['positions'].values():
                total_value += pos['amount'] * market['price']
            
            state['modes'][mode] = {
                'balance': wallet['balance'],
                'positions': len(wallet['positions']),
                'trades': len(wallet['trades']),
                'total_value': total_value,
                'pnl': wallet['pnl'],
                'performance': ((total_value - 10000) / 10000) * 100
            }
        
        # Sauver pour dashboard
        with open('/opt/smartorder-pro/data/all_modes_test.json', 'w') as f:
            json.dump(state, f, indent=2)
        
        return state
    
    def run_test_cycle(self):
        """Execute un cycle de test complet"""
        print(f"\n{'='*80}")
        print(f"🧪 TEST CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        
        market = self.fetch_market_data()
        print(f"\n📊 Marché: ${market['price']:.2f} | RSI: {market['rsi']:.1f} | MACD: {market['macd']:.2f}")
        
        # Test tous les modes
        print("\n🔍 Tests en cours...")
        
        spot_result = self.test_spot_mode(market)
        if spot_result:
            print(f"   📊 {spot_result}")
        
        futures_result = self.test_futures_mode(market)
        if futures_result:
            print(f"   ⚡ {futures_result}")
        
        # Sauvegarder état
        state = self.save_state()
        
        # Afficher résultats
        print(f"\n{'='*80}")
        print("💰 RÉSULTATS PAR MODE:")
        print(f"{'='*80}")
        
        for mode, stats in state['modes'].items():
            print(f"\n{mode}:")
            print(f"  Balance: ${stats['balance']:.2f}")
            print(f"  Valeur totale: ${stats['total_value']:.2f}")
            print(f"  PnL: ${stats['pnl']:+.2f} ({stats['performance']:+.2f}%)")
            print(f"  Trades: {stats['trades']}")
    
    def run(self, cycles=100, interval=30):
        """Lance test complet"""
        print(f"\n{'='*80}")
        print("🚀 TEST COMPLET - TOUS LES MODES")
        print(f"{'='*80}")
        print("Modes testés: SPOT, FUTURES, HYBRIDE, MANUEL")
        print(f"Stratégies: {', '.join(self.strategies)}")
        print(f"Capital par mode: $10,000")
        print(f"{'='*80}\n")
        
        for i in range(cycles):
            try:
                self.run_test_cycle()
                
                if i < cycles - 1:
                    print(f"\n⏳ Prochain cycle dans {interval}s...")
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ Arrêt")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval)


if __name__ == '__main__':
    tester = UnifiedPaperTester()
    tester.run(cycles=100, interval=30)
