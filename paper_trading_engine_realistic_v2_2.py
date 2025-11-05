#!/usr/bin/env python3
"""
🎯 SmartOrder PRO AI - Paper Trading Engine REALISTIC v2.2
============================================================
Moteur de trading paper CCXT avec stratégies techniques réelles

Features:
- CCXT Bybit Testnet (prix réels)
- RSI, MACD, Bollinger Bands, Support/Resistance
- Risk Management: SL/TP dynamiques, R/R > 1.5
- Sorties: positions.json, pnl_tracker.jsonl, paper_wallet.json
- Logs: logs/paper_engine.log
- Daemon: cycle 60s

Author: SAFELOGIC - Aboubakr MAIGA
Version: 2.2.0-CCXT-DAEMON
Date: 2025-11-03
"""

import ccxt
import json
import time
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# === CONFIGURATION ===
CONFIG_DIR = Path("/opt/smartorder-pro/config")
LOG_DIR = Path("/opt/smartorder-pro/logs")
LOG_DIR.mkdir(exist_ok=True)

CYCLE_INTERVAL = 60  # secondes
INITIAL_BALANCE = 10000.0  # USDT
MAX_POSITIONS = 3
POSITION_SIZE_PCT = 0.1  # 10% du wallet par position
MIN_RR_RATIO = 1.5  # Risk/Reward minimum

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "paper_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === TECHNICAL INDICATORS ===
class TechnicalIndicators:
    """Calculs des indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calcule le RSI"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
        """Calcule le MACD"""
        if len(prices) < slow:
            return None
        
        prices_array = np.array(prices)
        ema_fast = TechnicalIndicators._ema(prices_array, fast)
        ema_slow = TechnicalIndicators._ema(prices_array, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators._ema(macd_line, signal)
        histogram = macd_line[-1] - signal_line[-1]
        
        return {
            'macd': round(macd_line[-1], 6),
            'signal': round(signal_line[-1], 6),
            'histogram': round(histogram, 6)
        }
    
    @staticmethod
    def calculate_bollinger(prices: List[float], period: int = 20, std_dev: int = 2) -> Optional[Dict]:
        """Calcule les Bollinger Bands"""
        if len(prices) < period:
            return None
        
        recent = prices[-period:]
        middle = np.mean(recent)
        std = np.std(recent)
        
        return {
            'upper': round(middle + (std_dev * std), 2),
            'middle': round(middle, 2),
            'lower': round(middle - (std_dev * std), 2),
            'width': round((std_dev * std * 2), 2)
        }
    
    @staticmethod
    def calculate_support_resistance(prices: List[float], window: int = 20) -> Tuple[float, float]:
        """Calcule support et résistance"""
        if len(prices) < window:
            return (min(prices), max(prices))
        
        recent = prices[-window:]
        support = round(min(recent), 2)
        resistance = round(max(recent), 2)
        return (support, resistance)
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calcule l'EMA (Exponential Moving Average)"""
        return np.array([np.mean(data[:i+1][-period:]) for i in range(len(data))])


# === PAPER TRADING ENGINE ===
class PaperTradingEngine:
    """Moteur de trading paper avec CCXT"""
    
    def __init__(self):
        self.exchange = self._init_exchange()
        self.wallet_file = CONFIG_DIR / "paper_wallet.json"
        self.pnl_file = CONFIG_DIR / "pnl_tracker.jsonl"
        self.positions_file = CONFIG_DIR / "positions.json"
        self.signals_file = CONFIG_DIR / "last_signals.json"
        self.strategies_file = CONFIG_DIR / "trading_modes.json"
        
        # État interne
        self.balance = INITIAL_BALANCE
        self.total_pnl = 0.0
        self.positions = []
        self.trades_count = 0
        self.wins = 0
        self.losses = 0
        self.total_invested = INITIAL_BALANCE
        
        self.load_state()
        logger.info("✅ Paper Trading Engine initialized")
    
    def _init_exchange(self) -> ccxt.Exchange:
        """Initialize CCXT Bybit Testnet"""
        try:
            exchange = ccxt.bybit({
                'apiKey': '',  # Demo mode - no keys
                'secret': '',
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}  # ou 'spot'
            })
            exchange.set_sandbox_mode(True)  # Testnet
            logger.info("✅ CCXT Bybit Testnet initialized")
            return exchange
        except Exception as e:
            logger.warning(f"⚠️ CCXT init failed, using demo mode: {e}")
            return None
    
    def load_state(self):
        """Charge l'état depuis les fichiers JSON"""
        try:
            if self.wallet_file.exists():
                with open(self.wallet_file) as f:
                    data = json.load(f)
                    self.balance = data.get('balance_usdt', INITIAL_BALANCE)
                    self.total_pnl = data.get('total_pnl', 0.0)
                    self.trades_count = data.get('total_trades', 0)
                    logger.info(f"📊 State loaded: Balance={self.balance} USDT, PnL={self.total_pnl}")
            
            if self.positions_file.exists():
                with open(self.positions_file) as f:
                    data = json.load(f)
                    self.positions = data.get('positions', [])
                    logger.info(f"📍 Loaded {len(self.positions)} open positions")
        except Exception as e:
            logger.error(f"❌ Error loading state: {e}")
    
    def save_wallet(self):
        """Sauvegarde l'état du wallet"""
        try:
            wallet_data = {
                'balance_usdt': round(self.balance, 2),
                'total_pnl': round(self.total_pnl, 2),
                'total_invested': self.total_invested,
                'total_trades': self.trades_count,
                'open_positions': len(self.positions),
                'equity': round(self.balance + sum(p.get('unrealized_pnl', 0) for p in self.positions), 2),
                'last_update': datetime.now().isoformat()
            }
            with open(self.wallet_file, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            logger.debug("💾 Wallet saved")
        except Exception as e:
            logger.error(f"❌ Error saving wallet: {e}")
    
    def save_positions(self):
        """Sauvegarde les positions"""
        try:
            data = {
                'positions': self.positions,
                'total_value': sum(p.get('value_usdt', 0) for p in self.positions),
                'last_update': datetime.now().isoformat()
            }
            with open(self.positions_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"📍 Positions saved ({len(self.positions)} open)")
        except Exception as e:
            logger.error(f"❌ Error saving positions: {e}")
    
    def append_trade_log(self, trade_data: Dict):
        """Ajoute un trade au log JSONL"""
        try:
            with open(self.pnl_file, 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
            logger.debug(f"📝 Trade logged: {trade_data.get('symbol')} {trade_data.get('side')} PnL={trade_data.get('pnl', 0)}")
        except Exception as e:
            logger.error(f"❌ Error logging trade: {e}")
    
    def fetch_market_data(self, symbol: str = 'BTC/USDT', timeframe: str = '1h', limit: int = 100) -> Optional[List[float]]:
        """Récupère les données OHLCV de CCXT"""
        try:
            if self.exchange is None:
                # Mode demo: prix simulés
                base_price = 65000 if 'BTC' in symbol else 3500
                prices = [base_price + np.random.normal(0, base_price * 0.02) for _ in range(limit)]
                logger.debug(f"📊 Demo prices for {symbol}: {prices[-1]:.2f}")
                return prices
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            prices = [candle[4] for candle in ohlcv]  # Close prices
            logger.debug(f"📊 CCXT fetched {len(prices)} prices for {symbol}: last={prices[-1]:.2f}")
            return prices
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def calculate_indicators(self, prices: List[float]) -> Dict:
        """Calcule tous les indicateurs techniques"""
        indicators = {}
        
        indicators['rsi'] = TechnicalIndicators.calculate_rsi(prices)
        indicators['macd'] = TechnicalIndicators.calculate_macd(prices)
        indicators['bollinger'] = TechnicalIndicators.calculate_bollinger(prices)
        support, resistance = TechnicalIndicators.calculate_support_resistance(prices)
        indicators['support'] = support
        indicators['resistance'] = resistance
        indicators['current_price'] = prices[-1]
        
        return indicators
    
    def generate_signal(self, indicators: Dict) -> str:
        """Génère un signal de trading basé sur les indicateurs"""
        rsi = indicators.get('rsi')
        macd = indicators.get('macd', {})
        bb = indicators.get('bollinger', {})
        price = indicators.get('current_price')
        
        if not all([rsi, macd, bb, price]):
            return 'HOLD'
        
        # Stratégie combinée RSI + MACD + Bollinger
        signal_score = 0
        
        # RSI
        if rsi < 30:
            signal_score += 2  # Oversold
        elif rsi > 70:
            signal_score -= 2  # Overbought
        
        # MACD
        if macd.get('histogram', 0) > 0:
            signal_score += 1
        elif macd.get('histogram', 0) < 0:
            signal_score -= 1
        
        # Bollinger
        if price < bb.get('lower', 0):
            signal_score += 1  # Prix sous BB inférieure
        elif price > bb.get('upper', 0):
            signal_score -= 1  # Prix au-dessus BB supérieure
        
        # Décision (seuils abaissés pour tests)
        if signal_score >= 1:  # Abaissé de 2 à 1
            return 'BUY'
        elif signal_score <= -1:  # Abaissé de -2 à -1
            return 'SELL'
        else:
            return 'HOLD'
    
    def calculate_sl_tp(self, entry_price: float, side: str, indicators: Dict) -> Tuple[float, float]:
        """Calcule Stop Loss et Take Profit dynamiques"""
        atr_proxy = indicators.get('bollinger', {}).get('width', entry_price * 0.02) / 4
        
        if side == 'BUY':
            sl = round(entry_price - (atr_proxy * 1.5), 2)
            tp = round(entry_price + (atr_proxy * MIN_RR_RATIO * 1.5), 2)
        else:  # SELL
            sl = round(entry_price + (atr_proxy * 1.5), 2)
            tp = round(entry_price - (atr_proxy * MIN_RR_RATIO * 1.5), 2)
        
        return (sl, tp)
    
    def open_position(self, symbol: str, side: str, indicators: Dict):
        """Ouvre une nouvelle position"""
        if len(self.positions) >= MAX_POSITIONS:
            logger.warning(f"⚠️ Max positions reached ({MAX_POSITIONS})")
            return
        
        price = indicators.get('current_price')
        position_value = self.balance * POSITION_SIZE_PCT
        quantity = round(position_value / price, 6)
        
        if position_value > self.balance:
            logger.warning(f"⚠️ Insufficient balance: {self.balance} < {position_value}")
            return
        
        sl, tp = self.calculate_sl_tp(price, side, indicators)
        
        position = {
            'id': f"POS_{int(time.time() * 1000)}",
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'quantity': quantity,
            'value_usdt': round(position_value, 2),
            'sl': sl,
            'tp': tp,
            'status': 'OPEN',
            'opened_at': datetime.now().isoformat(),
            'strategy': 'RSI_MACD_BB',
            'mode': 'paper',
            'exchange': 'bybit_testnet'
        }
        
        self.positions.append(position)
        self.balance -= position_value
        
        logger.info(f"🟢 OPEN {side} {symbol} @ {price} | Qty: {quantity} | SL: {sl} | TP: {tp}")
        self.save_positions()
        self.save_wallet()
    
    def check_exit_conditions(self, position: Dict, current_price: float):
        """Vérifie si une position doit être fermée"""
        side = position['side']
        entry = position['entry_price']
        sl = position['sl']
        tp = position['tp']
        
        if side == 'BUY':
            if current_price <= sl:
                return 'SL_HIT'
            elif current_price >= tp:
                return 'TP_HIT'
        else:  # SELL
            if current_price >= sl:
                return 'SL_HIT'
            elif current_price <= tp:
                return 'TP_HIT'
        
        return None
    
    def close_position(self, position: Dict, current_price: float, reason: str):
        """Ferme une position"""
        entry = position['entry_price']
        quantity = position['quantity']
        side = position['side']
        
        if side == 'BUY':
            pnl = (current_price - entry) * quantity
        else:  # SELL
            pnl = (entry - current_price) * quantity
        
        pnl_pct = (pnl / position['value_usdt']) * 100
        
        self.balance += position['value_usdt'] + pnl
        self.total_pnl += pnl
        self.trades_count += 1
        
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        # Log trade
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': position['symbol'],
            'side': side,
            'entry_price': entry,
            'exit_price': current_price,
            'quantity': quantity,
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'reason': reason,
            'strategy': position['strategy']
        }
        self.append_trade_log(trade_data)
        
        # Remove position
        self.positions.remove(position)
        
        logger.info(f"🔴 CLOSE {side} {position['symbol']} @ {current_price} | PnL: {pnl:.2f} USDT ({pnl_pct:.1f}%) | Reason: {reason}")
        
        self.save_positions()
        self.save_wallet()
    
    def save_signals(self, symbol: str, indicators: Dict, signal: str):
        """Sauvegarde les derniers signaux"""
        try:
            signals_data = {
                'symbol': symbol,
                'price': indicators.get('current_price'),
                'rsi': indicators.get('rsi'),
                'macd': indicators.get('macd', {}).get('macd'),
                'macd_signal': indicators.get('macd', {}).get('signal'),
                'macd_histogram': indicators.get('macd', {}).get('histogram'),
                'bb_upper': indicators.get('bollinger', {}).get('upper'),
                'bb_middle': indicators.get('bollinger', {}).get('middle'),
                'bb_lower': indicators.get('bollinger', {}).get('lower'),
                'support': indicators.get('support'),
                'resistance': indicators.get('resistance'),
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.signals_file, 'w') as f:
                json.dump(signals_data, f, indent=2)
            logger.debug(f"💡 Signals saved: {signal}")
        except Exception as e:
            logger.error(f"❌ Error saving signals: {e}")
    
    def run_cycle(self):
        """Exécute un cycle de trading"""
        try:
            logger.info("🔄 === NEW TRADING CYCLE ===")
            
            # Fetch market data
            symbol = 'BTC/USDT'
            prices = self.fetch_market_data(symbol)
            
            if not prices:
                logger.warning("⚠️ No market data, skipping cycle")
                return
            
            # Calculate indicators
            indicators = self.calculate_indicators(prices)
            signal = self.generate_signal(indicators)
            
            logger.info(f"📊 {symbol} @ {indicators['current_price']:.2f} | RSI: {indicators['rsi']} | Signal: {signal}")
            
            # Save signals
            self.save_signals(symbol, indicators, signal)
            
            # Check exit conditions for open positions
            current_price = indicators['current_price']
            for position in self.positions[:]:  # Copy list to allow removal
                exit_reason = self.check_exit_conditions(position, current_price)
                if exit_reason:
                    self.close_position(position, current_price, exit_reason)
            
            # Open new position if signal
            if signal in ['BUY', 'SELL'] and len(self.positions) < MAX_POSITIONS:
                self.open_position(symbol, signal, indicators)
            
            # Stats
            win_rate = (self.wins / self.trades_count * 100) if self.trades_count > 0 else 0
            logger.info(f"📈 Balance: {self.balance:.2f} USDT | PnL: {self.total_pnl:.2f} | Trades: {self.trades_count} | WinRate: {win_rate:.1f}% | Positions: {len(self.positions)}")
            
        except Exception as e:
            logger.error(f"❌ Error in cycle: {e}", exc_info=True)
    
    def run_daemon(self):
        """Lance le daemon en boucle infinie"""
        logger.info("🚀 Starting Paper Trading Engine Daemon")
        logger.info(f"⏱️ Cycle interval: {CYCLE_INTERVAL}s")
        
        try:
            while True:
                self.run_cycle()
                time.sleep(CYCLE_INTERVAL)
        except KeyboardInterrupt:
            logger.info("⏹️ Daemon stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)


# === MAIN ===
if __name__ == '__main__':
    import sys
    
    engine = PaperTradingEngine()
    
    if '--test' in sys.argv:
        logger.info("🧪 TEST MODE: Running single cycle")
        engine.run_cycle()
        logger.info("✅ Test completed")
    else:
        engine.run_daemon()
