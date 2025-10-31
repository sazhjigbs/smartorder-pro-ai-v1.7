#!/usr/bin/env python3
"""
🚀 ULTIMATE TRADING BOT - 100% Real Data
Stratégies basées sur indicateurs techniques professionnels réels
"""
import ccxt
import pandas as pd
import numpy as np
import ta
import time
from datetime import datetime
from typing import Dict, List

class UltimateTradingBot:
    """
    Bot de trading avec indicateurs 100% réels :
    - RSI, MACD, Bollinger Bands, ATR, ADX
    - Détection régime de marché
    - Grid adaptatif intelligent
    """
    
    def __init__(self, symbol: str = 'BTC/USDT', initial_capital: float = 10000):
        self.symbol = symbol
        self.capital = initial_capital
        self.initial_capital = initial_capital
        
        # Exchange RÉEL
        self.exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Positions et ordres
        self.positions = []
        self.orders = []
        self.pnl = 0.0
        
        print(f"✅ Bot initialisé: {symbol} | Capital: ${initial_capital}")
    
    def fetch_real_data(self, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Récupère données réelles depuis l'exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"❌ Erreur fetch data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calcule TOUS les indicateurs techniques avec bibliothèque TA"""
        
        # RSI
        rsi = ta.momentum.rsi(df['close'], window=14)
        
        # MACD
        macd_obj = ta.trend.MACD(df['close'])
        macd = macd_obj.macd()
        macd_signal = macd_obj.macd_signal()
        macd_hist = macd_obj.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        bb_upper = bb.bollinger_hband()
        bb_middle = bb.bollinger_mavg()
        bb_lower = bb.bollinger_lband()
        
        # ATR (volatilité)
        atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        
        # ADX (force tendance)
        adx = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
        
        # EMA
        ema_20 = ta.trend.ema_indicator(df['close'], window=20)
        ema_50 = ta.trend.ema_indicator(df['close'], window=50)
        
        # Prix actuel
        current_price = df['close'].iloc[-1]
        
        # Volatilité (écart-type normalisé)
        volatility = df['close'].pct_change().std() * np.sqrt(24)  # Annualisé
        
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
        """
        Détecte le régime de marché avec indicateurs RÉELS
        Returns: 'trending_up', 'trending_down', 'ranging', 'volatile'
        """
        rsi = indicators['rsi']
        adx = indicators['adx']
        macd_hist = indicators['macd_hist']
        volatility = indicators['volatility']
        price = indicators['price']
        ema_20 = indicators['ema_20']
        ema_50 = indicators['ema_50']
        
        # Haute volatilité
        if volatility > 0.05:  # >5% volatilité annualisée
            return 'volatile'
        
        # Trending fort (ADX > 25)
        if adx > 25:
            if macd_hist > 0 and price > ema_20 > ema_50:
                return 'trending_up'
            elif macd_hist < 0 and price < ema_20 < ema_50:
                return 'trending_down'
        
        # Range (ADX faible)
        return 'ranging'
    
    def generate_grid_levels(self, indicators: Dict, num_levels: int = 10) -> List[float]:
        """
        Génère grille adaptative basée sur volatilité et régime
        """
        price = indicators['price']
        atr = indicators['atr']
        regime = self.detect_market_regime(indicators)
        
        # Espacement adaptatif basé sur ATR (volatilité réelle)
        if regime == 'volatile':
            spacing = atr * 1.5
        elif 'trending' in regime:
            spacing = atr * 1.0
        else:  # ranging
            spacing = atr * 0.8
        
        # Générer niveaux symétriques
        levels = []
        for i in range(-num_levels//2, num_levels//2 + 1):
            level_price = price + (i * spacing)
            if level_price > 0:  # Éviter prix négatifs
                levels.append(level_price)
        
        return sorted(levels)
    
    def generate_signals(self, indicators: Dict) -> Dict:
        """
        Génère signaux de trading basés sur indicateurs réels
        """
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
            'regime': regime
        }
        
        # Stratégie selon régime
        if regime == 'ranging':
            # Range trading avec BB + RSI
            if price <= bb_lower and rsi < 30:
                signal = {
                    'action': 'BUY',
                    'confidence': 0.8,
                    'reason': 'RSI oversold + BB lower',
                    'regime': regime
                }
            elif price >= bb_upper and rsi > 70:
                signal = {
                    'action': 'SELL',
                    'confidence': 0.8,
                    'reason': 'RSI overbought + BB upper',
                    'regime': regime
                }
        
        elif regime == 'trending_up':
            # Trend following avec MACD
            if macd_hist > 0 and rsi < 70:
                signal = {
                    'action': 'BUY',
                    'confidence': 0.75,
                    'reason': 'MACD bullish + trending up',
                    'regime': regime
                }
        
        elif regime == 'trending_down':
            if macd_hist < 0 and rsi > 30:
                signal = {
                    'action': 'SELL',
                    'confidence': 0.75,
                    'reason': 'MACD bearish + trending down',
                    'regime': regime
                }
        
        elif regime == 'volatile':
            # Éviter le trading en haute volatilité
            signal['reason'] = 'High volatility - waiting'
        
        return signal
    
    def run_cycle(self):
        """Execute un cycle de trading complet"""
        print(f"\n{'='*70}")
        print(f"🔄 Cycle {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # 1. Fetch données réelles
        df = self.fetch_real_data()
        if df.empty:
            print("❌ Pas de données disponibles")
            return
        
        # 2. Calculer indicateurs
        indicators = self.calculate_indicators(df)
        
        print(f"\n📊 INDICATEURS RÉELS:")
        print(f"   Prix: ${indicators['price']:.2f}")
        print(f"   RSI: {indicators['rsi']:.2f}")
        print(f"   MACD Hist: {indicators['macd_hist']:.4f}")
        print(f"   ADX: {indicators['adx']:.2f}")
        print(f"   ATR: ${indicators['atr']:.2f}")
        print(f"   Volatilité: {indicators['volatility']*100:.2f}%")
        
        # 3. Détecter régime
        regime = self.detect_market_regime(indicators)
        print(f"\n🎯 Régime: {regime.upper()}")
        
        # 4. Générer grille
        grid_levels = self.generate_grid_levels(indicators)
        print(f"\n📈 Grille Adaptative ({len(grid_levels)} niveaux):")
        print(f"   Range: ${min(grid_levels):.2f} - ${max(grid_levels):.2f}")
        print(f"   Espacement moyen: ${(max(grid_levels)-min(grid_levels))/len(grid_levels):.2f}")
        
        # 5. Générer signal
        signal = self.generate_signals(indicators)
        print(f"\n🚦 SIGNAL:")
        print(f"   Action: {signal['action']}")
        print(f"   Confiance: {signal['confidence']*100:.0f}%")
        print(f"   Raison: {signal['reason']}")
        
        # 6. Stats
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ${self.initial_capital:.2f}")
        print(f"   Actuel: ${self.capital:.2f}")
        print(f"   PnL: ${self.pnl:.2f} ({(self.pnl/self.initial_capital)*100:.2f}%)")
    
    def run(self, cycles: int = 10, interval: int = 60):
        """Lance le bot pour N cycles"""
        print(f"\n{'='*70}")
        print(f"🚀 ULTIMATE TRADING BOT - DÉMARRAGE")
        print(f"{'='*70}")
        print(f"Symbol: {self.symbol}")
        print(f"Cycles: {cycles}")
        print(f"Interval: {interval}s")
        
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
                time.sleep(interval)
        
        print(f"\n{'='*70}")
        print("✅ Bot terminé")
        print(f"{'='*70}")


if __name__ == '__main__':
    # Lancer le bot
    bot = UltimateTradingBot(symbol='BTC/USDT', initial_capital=10000)
    bot.run(cycles=5, interval=30)  # 5 cycles, 30s entre chaque
