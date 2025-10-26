#!/usr/bin/env python3
"""
🤖 SAFELOGIC SmartOrder PRO — Auto Trading Engine
Trading automatique intelligent avec AI + Risk Management
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bybit_client import futures_positions, _post
from core.execution_engine import get_engine
from core.logger import logger
from ai.signal_memory import get_trust_score, add_signal

class AutoTradingEngine:
    """Moteur de trading automatique"""
    
    def __init__(self):
        self.enabled = False
        self.symbol = "BTCUSDT"
        
        # Risk Management
        self.max_positions = 3
        self.max_daily_loss = 50.0  # USDT
        self.max_position_size = 100.0  # USDT
        self.min_confidence = 0.65
        self.min_trust_score = 70.0
        
        # Trading
        self.leverage = 2
        self.stop_loss_pct = 2.0
        self.take_profit_pct = 5.0
        
        # State
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.last_trade_time = None
        self.min_trade_interval = 300  # 5 min
        
        self.memory_file = "db/market_memory.json"
        self.state_file = "db/trading_state.json"
        
        self.load_state()
        logger.info("Auto Trading Engine initialized")
    
    def load_state(self):
        """Charge état"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.daily_pnl = state.get("daily_pnl", 0.0)
                    self.trades_today = state.get("trades_today", 0)
                    
                    # Reset si nouveau jour
                    today = datetime.now().strftime("%Y-%m-%d")
                    if state.get("last_date") != today:
                        self.daily_pnl = 0.0
                        self.trades_today = 0
        except Exception as e:
            logger.error(f"Load state error: {str(e)}")
    
    def save_state(self):
        """Sauvegarde état"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            state = {
                "daily_pnl": self.daily_pnl,
                "trades_today": self.trades_today,
                "last_date": datetime.now().strftime("%Y-%m-%d")
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Save state error: {str(e)}")
    
    def read_market_signals(self) -> Dict:
        """Lit signaux AI"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                return {
                    "bias": data.get("bias", "neutral"),
                    "confidence": data.get("confidence", 0.0),
                    "trend": data.get("trend", "flat")
                }
        except:
            pass
        return {"bias": "neutral", "confidence": 0.0, "trend": "flat"}
    
    def get_current_positions(self) -> List[Dict]:
        """Positions ouvertes"""
        try:
            data = futures_positions()
            positions = data.get("futures", [])
            return [p for p in positions if p.get("size", "0") != "0"]
        except:
            return []
    
    def calculate_position_size(self, confidence: float, trust: float) -> float:
        """Calcule taille position"""
        base = 20.0
        conf_mult = max(0.5, confidence)
        trust_mult = min(1.0, trust / 100.0)
        size = base * conf_mult * trust_mult
        return min(size, self.max_position_size)
    
    def check_risk_limits(self) -> Tuple[bool, str]:
        """Vérifie limites risque"""
        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss: {self.daily_pnl:.2f} USDT"
        
        positions = self.get_current_positions()
        if len(positions) >= self.max_positions:
            return False, f"Max positions: {len(positions)}"
        
        if self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time).total_seconds()
            if elapsed < self.min_trade_interval:
                return False, f"Wait {int(self.min_trade_interval - elapsed)}s"
        
        return True, "OK"
    
    def should_trade(self, signals: Dict) -> Tuple[bool, str]:
        """Décide si trader"""
        if not self.enabled:
            return False, "Disabled"
        
        if signals["bias"] == "neutral":
            return False, "Neutral"
        
        if signals["confidence"] < self.min_confidence:
            return False, f"Low conf: {signals['confidence']:.2%}"
        
        try:
            trust = get_trust_score(self.symbol, None, 50).get("trust_score", 0)
            if trust < self.min_trust_score:
                return False, f"Low trust: {trust:.1f}"
        except:
            pass
        
        can_trade, reason = self.check_risk_limits()
        if not can_trade:
            return False, reason
        
        return True, "OK"
    
    def place_market_order(self, side: str, qty: float) -> Tuple[bool, Dict]:
        """Place ordre market"""
        try:
            current_price = 67000.0  # TODO: get real price
            crypto_qty = qty / current_price
            
            order_data = {
                "category": "linear",
                "symbol": self.symbol,
                "side": side,
                "orderType": "Market",
                "qty": f"{crypto_qty:.6f}",
                "timeInForce": "IOC"
            }
            
            logger.info(f"Placing: {side} {crypto_qty:.6f} {self.symbol}")
            success, response = _post("/v5/order/create", order_data)
            
            if success:
                order_id = response.get("result", {}).get("orderId", "?")
                logger.info(f"Order OK: {order_id}")
                
                # Save signal
                signal_id = add_signal(
                    self.symbol, "15m",
                    "LONG" if side == "Buy" else "SHORT",
                    current_price, 0.75, self.leverage
                )
                
                return True, {
                    "order_id": order_id,
                    "signal_id": signal_id,
                    "side": side,
                    "qty": crypto_qty,
                    "price": current_price
                }
            else:
                logger.error(f"Order failed: {response}")
                return False, response
        except Exception as e:
            logger.error(f"Place order error: {str(e)}")
            return False, {"error": str(e)}
    
    def setup_trailing_stop(self, side: str, entry: float):
        """Configure trailing stop"""
        try:
            engine = get_engine()
            trail_side = "LONG" if side == "Buy" else "SHORT"
            
            trail = engine.setup_trailing_stop(
                self.symbol, trail_side, entry,
                self.stop_loss_pct, entry
            )
            
            logger.info(f"Trailing stop: {self.symbol} @ {entry}")
            return trail
        except Exception as e:
            logger.error(f"Trailing stop error: {str(e)}")
            return None
    
    def process_signals(self):
        """Traite signaux et trade"""
        try:
            signals = self.read_market_signals()
            logger.info(
                f"Signals: {signals['bias']} "
                f"conf={signals['confidence']:.2%}"
            )
            
            should, reason = self.should_trade(signals)
            if not should:
                logger.info(f"No trade: {reason}")
                return
            
            side = "Buy" if signals["bias"] == "bullish" else "Sell"
            
            try:
                trust = get_trust_score(self.symbol, None, 50).get("trust_score", 75)
            except:
                trust = 75
            
            size = self.calculate_position_size(signals["confidence"], trust)
            
            logger.info(f"Decision: {side} {size:.2f} USDT (trust={trust:.1f})")
            
            success, result = self.place_market_order(side, size)
            
            if success:
                self.trades_today += 1
                self.last_trade_time = datetime.now()
                self.save_state()
                
                entry = result.get("price", 0)
                self.setup_trailing_stop(side, entry)
                
                logger.info(f"✅ Trade OK: {side} {self.symbol}")
            else:
                logger.error(f"❌ Trade failed")
                
        except Exception as e:
            logger.error(f"Process error: {str(e)}")
    
    def monitor_positions(self):
        """Monitore positions"""
        try:
            positions = self.get_current_positions()
            if not positions:
                return
            
            engine = get_engine()
            
            for pos in positions:
                symbol = pos.get("symbol")
                price = float(pos.get("markPrice", 0))
                
                if price > 0:
                    triggered, trail = engine.update_trailing_stop(symbol, price)
                    
                    if triggered:
                        logger.warning(f"🔴 Stop triggered: {symbol} @ {price}")
                        
        except Exception as e:
            logger.error(f"Monitor error: {str(e)}")
    
    def run_continuous(self, interval: int = 30):
        """Lance trading continu"""
        logger.info(f"🚀 Auto Trading started (interval={interval}s)")
        logger.info(f"Max pos={self.max_positions}, Max loss={self.max_daily_loss} USDT")
        
        cycle = 0
        try:
            while True:
                cycle += 1
                logger.info(f"--- Cycle {cycle} ---")
                
                try:
                    if self.enabled:
                        self.process_signals()
                    self.monitor_positions()
                except Exception as e:
                    logger.error(f"Cycle error: {str(e)}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")

# Singleton
_engine = None

def get_auto_trading_engine() -> AutoTradingEngine:
    global _engine
    if _engine is None:
        _engine = AutoTradingEngine()
    return _engine

def start_auto_trading():
    engine = get_auto_trading_engine()
    engine.enabled = True
    logger.info("✅ Auto trading ENABLED")

def stop_auto_trading():
    engine = get_auto_trading_engine()
    engine.enabled = False
    logger.info("🛑 Auto trading DISABLED")

def is_auto_trading_enabled() -> bool:
    return get_auto_trading_engine().enabled

def main():
    engine = get_auto_trading_engine()
    engine.enabled = True
    engine.run_continuous(30)

if __name__ == "__main__":
    main()
