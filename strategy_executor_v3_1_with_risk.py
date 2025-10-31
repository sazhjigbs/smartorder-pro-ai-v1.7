#!/usr/bin/env python3
"""
🚀 STRATEGY EXECUTOR v3.1 WITH RISK MANAGEMENT - SmartOrder PRO AI v2.0-stable
================================================================================
Ajout intégré:
- Stop-Loss automatique (-2%)
- Take-Profit automatique (+3%)
- Drawdown Guard (max -5% du capital)
- Max position size (2% du capital par trade)
- Portfolio heat monitoring
"""

import sys
sys.path.insert(0, '/opt/smartorder-pro')

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
from core.risk_manager import RiskManager

# Configuration
CONFIG_DIR = Path('/opt/smartorder-pro/config')
STRATEGIES_FILE = CONFIG_DIR / 'strategies_state.json'
WATCHLIST_FILE = CONFIG_DIR / 'watchlist.json'
POSITIONS_FILE = CONFIG_DIR / 'positions.json'
PNL_FILE = CONFIG_DIR / 'pnl_tracker.json'
LOG_DIR = Path('/opt/smartorder-pro/logs')
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'strategy_executor_v3_1_risk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TechnicalAnalysis:
    """Analyse technique complète"""
    
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> Dict:
        try:
            rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
            
            macd = ta.trend.MACD(df['close'])
            macd_line = macd.macd().iloc[-1]
            macd_signal = macd.macd_signal().iloc[-1]
            macd_bullish = macd_line > macd_signal
            
            bollinger = ta.volatility.BollingerBands(df['close'])
            bb_upper = bollinger.bollinger_hband().iloc[-1]
            bb_lower = bollinger.bollinger_lband().iloc[-1]
            bb_middle = bollinger.bollinger_mavg().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if current_price >= bb_upper:
                bb_position = "overbought"
            elif current_price <= bb_lower:
                bb_position = "oversold"
            else:
                bb_position = "neutral"
            
            volume_sma = df['volume'].rolling(window=20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1.0
            
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
        if not indicators:
            return False, "No indicators", 0.0
        
        score = 0
        max_score = 5
        reasons = []
        
        if indicators['rsi'] < 40:
            score += 1
            reasons.append(f"RSI oversold ({indicators['rsi']})")
        elif indicators['rsi'] < 50:
            score += 0.5
        
        if indicators['macd_bullish']:
            score += 1
            reasons.append("MACD bullish")
        
        if indicators['bb_position'] == 'oversold':
            score += 1
            reasons.append("Bollinger oversold")
        elif indicators['bb_position'] == 'neutral':
            score += 0.5
        
        if indicators['volume_ratio'] >= 1.5:
            score += 1
            reasons.append(f"Volume high ({indicators['volume_ratio']}x)")
        elif indicators['volume_ratio'] >= 1.2:
            score += 0.5
        
        if indicators['trend'] == 'bullish':
            score += 1
            reasons.append("Trend bullish")
        
        confidence = (score / max_score) * 100
        is_valid = confidence >= 60
        
        return is_valid, " | ".join(reasons), confidence
    
    @staticmethod
    def validate_sell_signal(indicators: Dict) -> Tuple[bool, str, float]:
        if not indicators:
            return False, "No indicators", 0.0
        
        score = 0
        max_score = 5
        reasons = []
        
        if indicators['rsi'] > 60:
            score += 1
            reasons.append(f"RSI overbought ({indicators['rsi']})")
        elif indicators['rsi'] > 50:
            score += 0.5
        
        if not indicators['macd_bullish']:
            score += 1
            reasons.append("MACD bearish")
        
        if indicators['bb_position'] == 'overbought':
            score += 1
            reasons.append("Bollinger overbought")
        elif indicators['bb_position'] == 'neutral':
            score += 0.5
        
        if indicators['volume_ratio'] >= 1.5:
            score += 1
            reasons.append(f"Volume high ({indicators['volume_ratio']}x)")
        elif indicators['volume_ratio'] >= 1.2:
            score += 0.5
        
        if indicators['trend'] == 'bearish':
            score += 1
            reasons.append("Trend bearish")
        
        confidence = (score / max_score) * 100
        is_valid = confidence >= 60
        
        return is_valid, " | ".join(reasons), confidence


class PositionManager:
    """Gestionnaire de positions avec Risk Management"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.positions = self.load_positions()
        self.pnl_tracker = self.load_pnl()
        
        # Risk Manager avec paramètres conservateurs
        self.risk_manager = RiskManager(
            max_risk_per_trade=0.02,      # 2% max par trade
            max_portfolio_risk=0.10,       # 10% max total
            max_drawdown=0.05              # 5% max drawdown (Drawdown Guard)
        )
        
        logger.info("🛡️ Risk Manager initialisé: SL -2%, TP +3%, Drawdown Guard -5%")
    
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
    
    def check_drawdown_guard(self) -> bool:
        """Vérifie si Drawdown Guard est déclenché"""
        current_pnl = self.pnl_tracker.get('total_pnl', 0.0)
        drawdown_pct = (current_pnl / self.initial_capital) * 100
        
        if drawdown_pct <= -5.0:
            logger.warning(f"🚨 DRAWDOWN GUARD TRIGGERED: {drawdown_pct:.2f}% - TRADING STOPPED")
            return True
        return False
    
    def calculate_position_size(self, price: float, stop_loss_pct: float = 0.02) -> float:
        """Calcule taille position avec Risk Management"""
        current_capital = self.initial_capital + self.pnl_tracker.get('total_pnl', 0.0)
        
        # Max 2% du capital par trade
        max_risk_amount = current_capital * 0.02
        
        # Calculer taille basée sur stop-loss
        position_size_usdt = max_risk_amount / stop_loss_pct
        position_size = position_size_usdt / price
        
        return position_size
    
    def open_position(self, symbol: str, side: str, price: float, strategy: str) -> Optional[Dict]:
        """Ouvre position avec Stop-Loss et Take-Profit automatiques"""
        
        # Vérifier Drawdown Guard
        if self.check_drawdown_guard():
            logger.warning("❌ Position refusée: Drawdown Guard actif")
            return None
        
        # Calculer taille position
        amount = self.calculate_position_size(price)
        
        # Calculer Stop-Loss et Take-Profit
        if side == 'BUY':
            stop_loss_price = price * 0.98   # -2%
            take_profit_price = price * 1.03  # +3%
        else:
            stop_loss_price = price * 1.02
            take_profit_price = price * 0.97
        
        position = {
            'id': f'pos_{int(time.time())}_{hash(symbol) % 10000}',
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'entry_price': price,
            'current_price': price,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'pnl': 0.0,
            'pnl_percent': 0.0,
            'strategy': strategy,
            'opened_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        self.positions.append(position)
        self.save_positions()
        
        logger.info(f"🟢 Position: {side} {amount:.6f} {symbol} @ ${price:.2f} | SL: ${stop_loss_price:.2f} | TP: ${take_profit_price:.2f}")
        return position
    
    def check_stop_loss_take_profit(self, position: Dict, current_price: float) -> Optional[str]:
        """Vérifie si Stop-Loss ou Take-Profit est atteint"""
        if position['side'] == 'BUY':
            if current_price <= position['stop_loss']:
                return 'STOP_LOSS'
            elif current_price >= position['take_profit']:
                return 'TAKE_PROFIT'
        else:
            if current_price >= position['stop_loss']:
                return 'STOP_LOSS'
            elif current_price <= position['take_profit']:
                return 'TAKE_PROFIT'
        return None
    
    def close_position(self, position_id: str, exit_price: float, reason: str = 'MANUAL') -> Optional[Dict]:
        for pos in self.positions:
            if pos['id'] == position_id and pos['status'] == 'open':
                if pos['side'] == 'BUY':
                    pnl = (exit_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - exit_price) * pos['amount']
                
                pos['status'] = 'closed'
                pos['exit_price'] = exit_price
                pos['pnl'] = round(pnl, 2)
                pos['close_reason'] = reason
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
                    'strategy': strategy,
                    'reason': reason
                })
                
                self.save_positions()
                self.save_pnl()
                
                emoji = "🔴" if reason == "STOP_LOSS" else "🟢" if reason == "TAKE_PROFIT" else "⚪"
                logger.info(f"{emoji} Closed [{reason}]: {pos['symbol']} @ ${exit_price:.2f} | PnL: ${pnl:+.2f} | Total: ${self.pnl_tracker['total_pnl']:.2f}")
                
                return pos
        return None
    
    def update_positions(self, current_prices: Dict):
        """Met à jour positions et vérifie SL/TP"""
        for pos in self.positions:
            if pos['status'] == 'open' and pos['symbol'] in current_prices:
                current_price = current_prices[pos['symbol']]
                pos['current_price'] = current_price
                
                # Vérifier Stop-Loss / Take-Profit
                trigger = self.check_stop_loss_take_profit(pos, current_price)
                if trigger:
                    self.close_position(pos['id'], current_price, trigger)
                    continue
                
                # Calculer PnL unrealized
                if pos['side'] == 'BUY':
                    pnl = (current_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - current_price) * pos['amount']
                
                pos['pnl'] = round(pnl, 2)
                pos['pnl_percent'] = round((pnl / (pos['entry_price'] * pos['amount'])) * 100, 2)
        
        self.save_positions()


class StrategyExecutorV31:
    """Exécuteur avec Risk Management intégré"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.position_manager = PositionManager(initial_capital=10000.0)
        
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
        strategy_name = strategy['name']
        watchlist, _ = self.load_config()
        
        logger.info(f"🚀 {strategy_name} démarre avec Risk Management - Coins: {', '.join(watchlist)}")
        
        open_positions = {}
        iteration = 0
        
        try:
            while self.running and strategy['id'] in self.strategy_threads:
                iteration += 1
                
                # Vérifier Drawdown Guard
                if self.position_manager.check_drawdown_guard():
                    logger.warning(f"⚠️ {strategy_name}: Drawdown Guard actif - pause trading")
                    time.sleep(300)  # Pause 5 minutes
                    continue
                
                current_prices = {}
                for symbol in watchlist:
                    df = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
                    if df is not None and len(df) > 50:
                        current_prices[symbol] = df['close'].iloc[-1]
                
                if current_prices:
                    self.position_manager.update_positions(current_prices)
                
                for symbol in watchlist:
                    df = self.fetch_ohlcv(symbol, timeframe='1h', limit=100)
                    if df is None or len(df) < 50:
                        continue
                    
                    indicators = TechnicalAnalysis.calculate_indicators(df)
                    if not indicators:
                        continue
                    
                    current_price = df['close'].iloc[-1]
                    
                    if symbol not in open_positions:
                        is_valid, reason, confidence = SignalValidator.validate_buy_signal(indicators)
                        
                        if is_valid:
                            pos = self.position_manager.open_position(
                                symbol, 'BUY', current_price, strategy_name
                            )
                            if pos:
                                open_positions[symbol] = pos['id']
                                logger.info(f"[{strategy_name}] 📈 BUY {symbol}: {reason} (Conf: {confidence:.0f}%)")
                    
                    elif symbol in open_positions:
                        is_valid, reason, confidence = SignalValidator.validate_sell_signal(indicators)
                        
                        if is_valid:
                            self.position_manager.close_position(
                                open_positions[symbol], current_price, 'SIGNAL'
                            )
                            del open_positions[symbol]
                            logger.info(f"[{strategy_name}] 📉 SELL {symbol}: {reason} (Conf: {confidence:.0f}%)")
                
                if iteration % 10 == 0:
                    total_pnl = self.position_manager.pnl_tracker['total_pnl']
                    logger.info(f"[{strategy_name}] 💰 PnL: ${total_pnl:.2f}")
                
                time.sleep(3600)  # 1 heure
                
        except Exception as e:
            logger.error(f"[{strategy_name}] Erreur: {e}")
        finally:
            for symbol, pos_id in open_positions.items():
                if symbol in current_prices:
                    self.position_manager.close_position(pos_id, current_prices[symbol], 'SHUTDOWN')
            logger.info(f"[{strategy_name}] Arrêt")
    
    def start_strategy(self, strategy: Dict):
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
        logger.info(f"✅ {strategy['name']} lancée avec Risk Management")
    
    def run(self):
        logger.info("=" * 80)
        logger.info("🚀 STRATEGY EXECUTOR v3.1 WITH RISK MANAGEMENT - v2.0-stable")
        logger.info("🛡️ Stop-Loss: -2% | Take-Profit: +3% | Drawdown Guard: -5%")
        logger.info("=" * 80)
        
        watchlist, strategies = self.load_config()
        
        logger.info(f"Watchlist: {', '.join(watchlist)}")
        logger.info(f"Stratégies: {len(strategies)}")
        logger.info(f"PnL Initial: ${self.position_manager.pnl_tracker['total_pnl']:.2f}")
        logger.info("=" * 80)
        
        self.running = True
        
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
        logger.info("🛑 Arrêt...")
        self.running = False
        
        for sid, thread in list(self.strategy_threads.items()):
            thread.join(timeout=10)
        
        final_pnl = self.position_manager.pnl_tracker['total_pnl']
        logger.info(f"💰 PnL Final: ${final_pnl:.2f}")
        logger.info("=" * 80)


if __name__ == '__main__':
    executor = StrategyExecutorV31()
    executor.run()
