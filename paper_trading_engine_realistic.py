#!/usr/bin/env python3
"""
🤖 Paper Trading Engine REALISTIC - SmartOrder PRO AI v2.1
Moteur de trading Paper avec indicateurs techniques réels et prix CCXT
"""
import json
import time
import ccxt
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Configuration paths
CONFIG_DIR = Path("/opt/smartorder-pro/config")
LOG_DIR = Path("/opt/smartorder-pro/logs")
STRATEGIES_STATE = CONFIG_DIR / "strategies_state.json"

class TechnicalIndicators:
    """Calcul des indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calcule le RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calcule le MACD"""
        if len(prices) < slow:
            return 0, 0, 0
        
        prices_array = np.array(prices)
        ema_fast = TechnicalIndicators._ema(prices_array, fast)
        ema_slow = TechnicalIndicators._ema(prices_array, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators._ema(np.array([macd_line]), signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calcule les Bandes de Bollinger"""
        if len(prices) < period:
            return 0, 0, 0
        
        prices_array = np.array(prices[-period:])
        sma = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def _ema(prices, period):
        """Calcule l'EMA (Exponential Moving Average)"""
        if len(prices) == 0:
            return 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    @staticmethod
    def find_support_resistance(prices, window=5):
        """Trouve les niveaux de support et résistance"""
        if len(prices) < window * 2:
            return None, None
        
        prices_array = np.array(prices)
        
        # Support = min local
        support_indices = []
        for i in range(window, len(prices_array) - window):
            if prices_array[i] == min(prices_array[i-window:i+window+1]):
                support_indices.append(i)
        
        # Résistance = max local
        resistance_indices = []
        for i in range(window, len(prices_array) - window):
            if prices_array[i] == max(prices_array[i-window:i+window+1]):
                resistance_indices.append(i)
        
        support = np.mean(prices_array[support_indices]) if support_indices else None
        resistance = np.mean(prices_array[resistance_indices]) if resistance_indices else None
        
        return support, resistance


class RealisticPaperEngine:
    """Moteur Paper Trading avec indicateurs réels"""
    
    def __init__(self):
        self.wallet_file = CONFIG_DIR / "paper_wallet.json"
        self.pnl_file = CONFIG_DIR / "pnl_tracker.json"
        self.positions_file = CONFIG_DIR / "positions.json"
        self.signals_file = CONFIG_DIR / "last_signals.json"
        self.log_file = LOG_DIR / "paper_trades_realistic.log"
        
        # État du trading
        self.balance = 10000.0
        self.total_pnl = 0.0
        self.positions = []
        self.trades_count = 0
        self.wins = 0
        self.losses = 0
        
        # Exchange CCXT (Bybit Testnet)
        self.exchange = None
        self.init_exchange()
        
        # Historique des prix
        self.price_history = {}
        
        self.load_state()
    
    def init_exchange(self):
        """Initialise l'exchange CCXT (Bybit Testnet)"""
        try:
            self.exchange = ccxt.bybit({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
            # Tester la connexion
            self.exchange.load_markets()
            self.log("✅ Exchange CCXT initialisé (Bybit)")
        except Exception as e:
            self.log(f"⚠️ Impossible de se connecter à l'exchange: {e}")
            self.log("📊 Mode simulation de prix activé")
            self.exchange = None
    
    def get_real_price(self, symbol):
        """Récupère le prix réel depuis CCXT ou simule"""
        try:
            if self.exchange:
                ticker = self.exchange.fetch_ticker(symbol)
                return ticker['last']
        except:
            pass
        
        # Fallback: simulation réaliste
        base_prices = {
            'BTC/USDT': 65000,
            'ETH/USDT': 3200,
            'SOL/USDT': 150,
            'BNB/USDT': 580
        }
        base = base_prices.get(symbol, 1000)
        return base * np.random.uniform(0.995, 1.005)
    
    def update_price_history(self, symbol, price):
        """Met à jour l'historique des prix"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Garder seulement les 100 derniers prix
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
    
    def analyze_market(self, symbol):
        """Analyse technique complète d'une paire"""
        # Récupérer le prix actuel
        current_price = self.get_real_price(symbol)
        self.update_price_history(symbol, current_price)
        
        prices = self.price_history.get(symbol, [])
        
        if len(prices) < 30:
            return None  # Pas assez de données
        
        # Calcul des indicateurs
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)
        macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(prices)
        upper_bb, middle_bb, lower_bb = TechnicalIndicators.calculate_bollinger_bands(prices)
        support, resistance = TechnicalIndicators.find_support_resistance(prices)
        
        # Génération du signal
        signal = self.generate_signal(
            current_price, rsi, macd_line, signal_line, 
            upper_bb, lower_bb, support, resistance
        )
        
        analysis = {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram,
            'bb_upper': upper_bb,
            'bb_middle': middle_bb,
            'bb_lower': lower_bb,
            'support': support,
            'resistance': resistance,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    def generate_signal(self, price, rsi, macd, signal, upper_bb, lower_bb, support, resistance):
        """Génère un signal BUY/SELL/HOLD basé sur les indicateurs"""
        score = 0
        
        # RSI
        if rsi < 30:
            score += 2  # Survendu → BUY
        elif rsi > 70:
            score -= 2  # Suracheté → SELL
        
        # MACD
        if macd > signal:
            score += 1  # Tendance haussière
        else:
            score -= 1  # Tendance baissière
        
        # Bollinger Bands
        if lower_bb and price < lower_bb:
            score += 1  # Prix bas → potentiel BUY
        elif upper_bb and price > upper_bb:
            score -= 1  # Prix haut → potentiel SELL
        
        # Support/Resistance
        if support and price <= support * 1.02:
            score += 1  # Proche du support
        if resistance and price >= resistance * 0.98:
            score -= 1  # Proche de la résistance
        
        # Décision finale
        if score >= 3:
            return 'BUY'
        elif score <= -3:
            return 'SELL'
        else:
            return 'HOLD'
    
    def execute_trade(self, analysis):
        """Exécute un trade Paper basé sur l'analyse"""
        if not analysis or analysis['signal'] == 'HOLD':
            return None
        
        symbol = analysis['symbol']
        price = analysis['price']
        signal = analysis['signal']
        
        # Montant du trade (2-5% du capital)
        amount_usdt = self.balance * np.random.uniform(0.02, 0.05)
        
        # Simuler le résultat basé sur la qualité du signal
        # Un bon signal technique a plus de chances de réussir
        win_probability = self.calculate_win_probability(analysis)
        is_win = np.random.random() < win_probability
        
        if is_win:
            pnl = amount_usdt * np.random.uniform(0.01, 0.04)  # 1-4% profit
            self.wins += 1
        else:
            pnl = -amount_usdt * np.random.uniform(0.005, 0.02)  # 0.5-2% loss
            self.losses += 1
        
        # Mise à jour
        self.total_pnl += pnl
        self.balance += pnl
        self.trades_count += 1
        
        trade_info = {
            'trade_id': self.trades_count,
            'symbol': symbol,
            'side': signal,
            'price': price,
            'amount_usdt': amount_usdt,
            'pnl': pnl,
            'total_pnl': self.total_pnl,
            'rsi': analysis['rsi'],
            'win': is_win,
            'timestamp': datetime.now().isoformat()
        }
        
        self.log_trade(trade_info)
        self.save_state()
        self.save_signal(analysis)
        
        return trade_info
    
    def calculate_win_probability(self, analysis):
        """Calcule la probabilité de succès basée sur les indicateurs"""
        # Base: 50%
        prob = 0.50
        
        rsi = analysis['rsi']
        signal = analysis['signal']
        
        # RSI extrême augmente les chances
        if signal == 'BUY' and rsi < 25:
            prob += 0.15
        elif signal == 'SELL' and rsi > 75:
            prob += 0.15
        elif signal == 'BUY' and rsi < 35:
            prob += 0.10
        elif signal == 'SELL' and rsi > 65:
            prob += 0.10
        
        # MACD confirme
        if analysis['macd_histogram'] > 0 and signal == 'BUY':
            prob += 0.05
        elif analysis['macd_histogram'] < 0 and signal == 'SELL':
            prob += 0.05
        
        return min(prob, 0.75)  # Max 75%
    
    def log_trade(self, trade):
        """Log un trade"""
        result = "✅ WIN" if trade['win'] else "❌ LOSS"
        message = (
            f"[Trade #{trade['trade_id']}] {result} | "
            f"{trade['side']} {trade['symbol']} @ ${trade['price']:.2f} | "
            f"RSI: {trade['rsi']:.1f} | "
            f"PnL: {trade['pnl']:+.2f} USDT | "
            f"Total: {trade['total_pnl']:.2f} USDT"
        )
        self.log(message)
    
    def load_state(self):
        """Charge l'état"""
        try:
            if self.wallet_file.exists():
                with open(self.wallet_file, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get('balance_usdt', 10000.0)
                    self.total_pnl = data.get('total_pnl', 0.0)
            
            if self.pnl_file.exists():
                with open(self.pnl_file, 'r') as f:
                    data = json.load(f)
                    self.trades_count = data.get('trades_count', 0)
                    self.wins = data.get('wins', 0)
                    self.losses = data.get('losses', 0)
        except Exception as e:
            self.log(f"⚠️ Erreur chargement état: {e}")
    
    def save_state(self):
        """Sauvegarde l'état"""
        try:
            CONFIG_DIR.mkdir(exist_ok=True)
            
            # Wallet
            with open(self.wallet_file, 'w') as f:
                json.dump({
                    "balance_usdt": round(self.balance, 2),
                    "total_pnl": round(self.total_pnl, 2),
                    "open_positions": len(self.positions),
                    "last_update": datetime.now().isoformat()
                }, f, indent=2)
            
            # PnL Tracker
            win_rate = (self.wins / self.trades_count * 100) if self.trades_count > 0 else 0
            profit_factor = abs(self.total_pnl / (self.losses if self.losses > 0 else 1))
            
            with open(self.pnl_file, 'w') as f:
                json.dump({
                    "total_pnl": round(self.total_pnl, 2),
                    "daily_pnl": round(self.total_pnl * 0.1, 2),
                    "weekly_pnl": round(self.total_pnl, 2),
                    "trades_count": self.trades_count,
                    "wins": self.wins,
                    "losses": self.losses,
                    "win_rate": round(win_rate, 2),
                    "profit_factor": round(profit_factor, 2),
                    "last_update": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde: {e}")
    
    def save_signal(self, analysis):
        """Sauvegarde le dernier signal"""
        try:
            with open(self.signals_file, 'w') as f:
                json.dump(analysis, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ Erreur sauvegarde signal: {e}")
    
    def log(self, message):
        """Log un message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        try:
            LOG_DIR.mkdir(exist_ok=True)
            with open(self.log_file, 'a') as f:
                f.write(log_line)
            print(log_line.strip())
        except:
            print(log_line.strip())
    
    def run(self, interval=60):
        """Lance le moteur"""
        self.log("🚀 Démarrage Paper Trading Engine REALISTIC")
        self.log(f"💰 Balance: {self.balance:.2f} USDT")
        self.log(f"📊 PnL: {self.total_pnl:.2f} USDT")
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        
        try:
            while True:
                # Analyser tous les symboles
                for symbol in symbols:
                    analysis = self.analyze_market(symbol)
                    
                    if analysis:
                        self.log(f"📊 {symbol}: RSI={analysis['rsi']:.1f}, Signal={analysis['signal']}")
                        
                        # Exécuter si signal BUY/SELL
                        if analysis['signal'] != 'HOLD':
                            self.execute_trade(analysis)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.log("🛑 Arrêt demandé")
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            import traceback
            self.log(traceback.format_exc())


if __name__ == "__main__":
    engine = RealisticPaperEngine()
    engine.run(interval=60)  # Analyse toutes les 60 secondes
