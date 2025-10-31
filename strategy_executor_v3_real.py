#!/usr/bin/env python3
"""
🚀 STRATEGY EXECUTOR v3 REAL - SmartOrder PRO AI
================================================
Moteur de trading Paper avec VRAIE analyse technique:
- RSI, MACD, Bollinger Bands, Volume
- Prix réels via CCXT (Bybit/Binance)
- Signal Validator multi-niveaux
- Paper Trading Engine v2
- PnL tracking en temps réel
"""

import ccxt
import pandas as pd
import ta
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading

# Configuration
CONFIG_DIR = Path('/opt/smartorder-pro/config')
STRATEGIES_FILE = CONFIG_DIR / 'strategies_state.json'
EXCHANGES_FILE = CONFIG_DIR / 'exchanges_state.json'
WATCHLIST_FILE = CONFIG_DIR / 'watchlist.json'
POSITIONS_FILE = CONFIG_DIR / 'positions.json'
PNL_FILE = CONFIG_DIR / 'pnl_tracker.json'
LOG_DIR = Path('/opt/smartorder-pro/logs')
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'strategy_executor_v3_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TechnicalAnalysis:
    """Analyse technique complète"""
    
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> Dict:
        """Calcule RSI, MACD, Bollinger, Volume"""
        try:
            # RSI
            rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            macd_line = macd.macd().iloc[-1]
            macd_signal = macd.macd_signal().iloc[-1]
            macd_bullish = macd_line > macd_signal
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'])
            bb_upper = bollinger.bollinger_hband().iloc[-1]
            bb_lower = bollinger.bollinger_lband().iloc[-1]
            bb_middle = bollinger.bollinger_mavg().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Position dans Bollinger
            if current_price >= bb_upper:
                bb_position = "overbought"
            elif current_price <= bb_lower:
                bb_position = "oversold"
            else:
                bb_position = "neutral"
            
            # Volume
            volume_sma = df['volume'].rolling(window=20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1.0
            
            # EMA trend
            ema_20 = df['close'].ewm(span=20).mean().iloc[-1]
            ema_50 = df['close'].ewm(span=50).mean().iloc[-1]
            trend = "bullish" if ema_20 > ema_50 else "bearish"
            
            return {
                'rsi': round(rsi, 2),
                'macd_bullish': macd_bullish,
                'macd_line': round(macd_line, 4),
                'macd_signal': round(macd_signal, 4),
                'bb_position': bb_position,
                'bb_upper': round(bb_upper, 2),
                'bb_lower': round(bb_lower, 2),
                'bb_middle': round(bb_middle, 2),
                'volume_ratio': round(volume_ratio, 2),
                'trend': trend,
                'ema_20': round(ema_20, 2),
                'ema_50': round(ema_50, 2)
            }
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs: {e}")
            return None


class SignalValidator:
    """Validateur de signaux multi-critères"""
    
    @staticmethod
    def validate_buy_signal(indicators: Dict) -> Tuple[bool, str, float]:
        """
        Valide un signal d'achat
        Returns: (is_valid, reason, confidence)
        """
        if not indicators:
            return False, "No indicators", 0.0
        
        score = 0
        max_score = 5
        reasons = []
        
        # 1. RSI oversold (30-40 optimal)
        if indicators['rsi'] < 40:
            score += 1
            reasons.append(f"RSI oversold ({indicators['rsi']})")
        elif indicators['rsi'] < 50:
            score += 0.5
            reasons.append(f"RSI neutral-low ({indicators['rsi']})")
        
        # 2. MACD bullish
        if indicators['macd_bullish']:
            score += 1
            reasons.append("MACD bullish")
        
        # 3. Bollinger oversold
        if indicators['bb_position'] == 'oversold':
            score += 1
            reasons.append("Bollinger oversold")
        elif indicators['bb_position'] == 'neutral':
            score += 0.5
        
        # 4. Volume élevé
        if indicators['volume_ratio'] >= 1.5:
            score += 1
            reasons.append(f"Volume high ({indicators['volume_ratio']}x)")
        elif indicators['volume_ratio'] >= 1.2:
            score += 0.5
        
        # 5. Trend bullish
        if indicators['trend'] == 'bullish':
            score += 1
            reasons.append("Trend bullish")
        
        confidence = (score / max_score) * 100
        is_valid = confidence >= 60  # Seuil 60%
        
        return is_valid, " | ".join(reasons), confidence
    
    @staticmethod
    def validate_sell_signal(indicators: Dict) -> Tuple[bool, str, float]:
        """
        Valide un signal de vente
        Returns: (is_valid, reason, confidence)
        """
        if not indicators:
            return False, "No indicators", 0.0
        
        score = 0
        max_score = 5
        reasons = []
        
        # 1. RSI overbought (60-70 optimal)
        if indicators['rsi'] > 60:
            score += 1
            reasons.append(f"RSI overbought ({indicators['rsi']})")
        elif indicators['rsi'] > 50:
            score += 0.5
            reasons.append(f"RSI neutral-high ({indicators['rsi']})")
        
        # 2. MACD bearish
        if not indicators['macd_bullish']:
            score += 1
            reasons.append("MACD bearish")
        
        # 3. Bollinger overbought
        if indicators['bb_position'] == 'overbought':
            score += 1
            reasons.append("Bollinger overbought")
        elif indicators['bb_position'] == 'neutral':
            score += 0.5
        
        # 4. Volume élevé
        if indicators['volume_ratio'] >= 1.5:
            score += 1
            reasons.append(f"Volume high ({indicators['volume_ratio']}x)")
        elif indicators['volume_ratio'] >= 1.2:
            score += 0.5
        
        # 5. Trend bearish
        if indicators['trend'] == 'bearish':
            score += 1
            reasons.append("Trend bearish")
        
        confidence = (score / max_score) * 100
        is_valid = confidence >= 60
        
        return is_valid, " | ".join(reasons), confidence


class PositionManager:
    """Gestionnaire de positions Paper Trading"""
    
    def __init__(self):
        self.positions = self.load_positions()
        self.pnl_tracker = self.load_pnl()
    
    def load_positions(self) -> List[Dict]:
        try:
            if POSITIONS_FILE.exists():
                with open(POSITIONS_FILE) as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def save_positions(self):
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(self.positions, f, indent=2)
    
    def load_pnl(self) -> Dict:
        try:
            if PNL_FILE.exists():
                with open(PNL_FILE) as f:
                    return json.load(f)
            return {'total_pnl': 0.0, 'trades': [], 'by_strategy': {}}
        except:
            return {'total_pnl': 0.0, 'trades': [], 'by_strategy': {}}
    
    def save_pnl(self):
        with open(PNL_FILE, 'w') as f:
            json.dump(self.pnl_tracker, f, indent=2)
    
    def open_position(self, symbol: str, side: str, amount: float, 
                     entry_price: float, strategy: str) -> Dict:
        position = {
            'id': f'pos_{int(time.time())}_{hash(symbol) % 10000}',
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'entry_price': entry_price,
            'current_price': entry_price,
            'pnl': 0.0,
            'pnl_percent': 0.0,
            'strategy': strategy,
            'opened_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        self.positions.append(position)
        self.save_positions()
        
        logger.info(f"🟢 Position: {side} {amount:.6f} {symbol} @ ${entry_price:.2f} ({strategy})")
        return position
    
    def close_position(self, position_id: str, exit_price: float) -> Optional[Dict]:
        for pos in self.positions:
            if pos['id'] == position_id and pos['status'] == 'open':
                if pos['side'] == 'BUY':
                    pnl = (exit_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - exit_price) * pos['amount']
                
                pos['status'] = 'closed'
                pos['exit_price'] = exit_price
                pos['pnl'] = round(pnl, 2)
                pos['closed_at'] = datetime.now().isoformat()
                
                self.pnl_tracker['total_pnl'] += pnl
                
                strategy = pos['strategy']
                if strategy not in self.pnl_tracker['by_strategy']:
                    self.pnl_tracker['by_strategy'][strategy] = 0.0
                self.pnl_tracker['by_strategy'][strategy] += pnl
                
                self.pnl_tracker['trades'].append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'amount': pos['amount'],
                    'entry': pos['entry_price'],
                    'exit': exit_price,
                    'pnl': pnl,
                    'strategy': strategy
                })
                
                self.save_positions()
                self.save_pnl()
                
                logger.info(f"🔴 Closed: {pos['symbol']} @ ${exit_price:.2f} | "
                          f"PnL: ${pnl:+.2f} | Total: ${self.pnl_tracker['total_pnl']:.2f}")
                
                return pos
        return None
    
    def update_positions(self, current_prices: Dict):
        """Met à jour les prix et PnL des positions ouvertes"""
        for pos in self.positions:
            if pos['status'] == 'open' and pos['symbol'] in current_prices:
                current_price = current_prices[pos['symbol']]
                pos['current_price'] = current_price
                
                if pos['side'] == 'BUY':
                    pnl = (current_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - current_price) * pos['amount']
                
                pos['pnl'] = round(pnl, 2)
                pos['pnl_percent'] = round((pnl / (pos['entry_price'] * pos['amount'])) * 100, 2)
        
        self.save_positions()


class StrategyExecutorV3:
    """Exécuteur avec analyse technique réelle"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.position_manager = PositionManager()
        
        # CCXT Exchange
        try:
            self.exchange = ccxt.bybit({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            logger.info("✅ CCXT Bybit initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur CCXT: {e}")
            self.exchange = None
    
    def load_config(self):
        """Charge watchlist et stratégies"""
        try:
            with open(WATCHLIST_FILE) as f:
                watchlist = json.load(f).get('coins', ['BTC/USDT', 'ETH/USDT'])
            
            with open(STRATEGIES_FILE) as f:
                strategies_data = json.load(f)
            
            enabled_strategies = []
            for mode in ['spot', 'futures', 'hybride']:
                for s in strategies_data.get(mode, []):
                    if s.get('enabled'):
                        s['mode'] = mode
                        enabled_strategies.append(s)
            
            return watchlist, enabled_strategies
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return ['BTC/USDT', 'ETH/USDT'], []
    
    def fetch_ohlcv(self, symbol: str, timeframe='1h', limit=100) -> Optional[pd.DataFrame]:
        """Récupère données OHLCV réelles"""
        if not self.exchange:
            return None
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Erreur fetch {symbol}: {e}")
            return None
    
    def execute_strategy(self, strategy: Dict):
        """Exécute une stratégie avec analyse technique"""
        strategy_name = strategy['name']
        watchlist, _ = self.load_config()
        
        logger.info(f"🚀 {strategy_name} démarre - Coins: {', '.join(watchlist)}")
        
        open_positions = {}  # {symbol: position_id}
        iteration = 0
        
        try:
            while self.running and strategy['id'] in self.strategy_threads:
                iteration += 1
                
                # Récupérer prix actuels
                current_prices = {}
                for symbol in watchlist:
                    df = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
                    if df is not None and len(df) > 50:
                        current_prices[symbol] = df['close'].iloc[-1]
                
                # Mettre à jour positions ouvertes
                if current_prices:
                    self.position_manager.update_positions(current_prices)
                
                # Analyser chaque coin
                for symbol in watchlist:
                    df = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
                    if df is None or len(df) < 50:
                        continue
                    
                    # Calculer indicateurs
                    indicators = TechnicalAnalysis.calculate_indicators(df)
                    if not indicators:
                        continue
                    
                    current_price = df['close'].iloc[-1]
                    
                    # Si pas de position, chercher signal BUY
                    if symbol not in open_positions:
                        is_valid, reason, confidence = SignalValidator.validate_buy_signal(indicators)
                        
                        if is_valid:
                            amount = 0.001 if 'BTC' in symbol else 0.01  # Montants adaptés
                            
                            pos = self.position_manager.open_position(
                                symbol, 'BUY', amount, current_price, strategy_name
                            )
                            open_positions[symbol] = pos['id']
                            
                            logger.info(f"[{strategy_name}] 📈 BUY {symbol}: {reason} (Conf: {confidence:.0f}%)")
                    
                    # Si position ouverte, chercher signal SELL
                    elif symbol in open_positions:
                        is_valid, reason, confidence = SignalValidator.validate_sell_signal(indicators)
                        
                        if is_valid:
                            self.position_manager.close_position(
                                open_positions[symbol], current_price
                            )
                            del open_positions[symbol]
                            
                            logger.info(f"[{strategy_name}] 📉 SELL {symbol}: {reason} (Conf: {confidence:.0f}%)")
                
                # Log PnL toutes les 10 itérations
                if iteration % 10 == 0:
                    total_pnl = self.position_manager.pnl_tracker['total_pnl']
                    logger.info(f"[{strategy_name}] 💰 PnL: ${total_pnl:.2f}")
                
                # Attente entre itérations (1h timeframe)
                time.sleep(3600)  # 1 heure
                
        except Exception as e:
            logger.error(f"[{strategy_name}] Erreur: {e}")
        finally:
            # Fermer positions ouvertes
            for symbol, pos_id in open_positions.items():
                if symbol in current_prices:
                    self.position_manager.close_position(pos_id, current_prices[symbol])
            
            logger.info(f"[{strategy_name}] Arrêt")
    
    def start_strategy(self, strategy: Dict):
        """Lance une stratégie dans un thread"""
        strategy_id = strategy['id']
        
        if strategy_id in self.strategy_threads:
            return
        
        thread = threading.Thread(
            target=self.execute_strategy,
            args=(strategy,),
            daemon=True
        )
        thread.start()
        self.strategy_threads[strategy_id] = thread
        
        logger.info(f"✅ {strategy['name']} lancée")
    
    def run(self):
        """Boucle principale"""
        logger.info("=" * 80)
        logger.info("🚀 STRATEGY EXECUTOR v3 REAL - Analyse technique activée")
        logger.info("=" * 80)
        
        watchlist, strategies = self.load_config()
        
        logger.info(f"Watchlist: {', '.join(watchlist)}")
        logger.info(f"Stratégies: {len(strategies)}")
        logger.info(f"PnL Initial: ${self.position_manager.pnl_tracker['total_pnl']:.2f}")
        logger.info("=" * 80)
        
        self.running = True
        
        # Lancer toutes les stratégies activées
        for strategy in strategies:
            self.start_strategy(strategy)
        
        try:
            while self.running:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Arrêt demandé")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Arrêt propre"""
        logger.info("🛑 Arrêt...")
        self.running = False
        
        for sid, thread in list(self.strategy_threads.items()):
            thread.join(timeout=10)
        
        final_pnl = self.position_manager.pnl_tracker['total_pnl']
        logger.info(f"💰 PnL Final: ${final_pnl:.2f}")
        logger.info("=" * 80)


if __name__ == '__main__':
    executor = StrategyExecutorV3()
    executor.run()
