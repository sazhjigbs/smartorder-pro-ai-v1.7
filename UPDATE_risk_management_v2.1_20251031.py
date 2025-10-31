#!/usr/bin/env python3
"""
UPDATE: Risk Management Module v2.1
Date: 2025-10-31
Description: Module de gestion des risques avec stop-loss, take-profit, drawdown guard
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RiskManager:
    """Gestionnaire de risques pour le trading"""
    
    def __init__(self, config_path: str = "/opt/smartorder-pro/config"):
        self.config_path = Path(config_path)
        self.max_position_size = 1000  # USDT
        self.max_drawdown = 0.05  # 5%
        self.stop_loss_percent = 0.02  # 2%
        self.take_profit_percent = 0.03  # 3%
        self.max_daily_loss = 100  # USDT
        
        # Tracking
        self.daily_pnl = 0
        self.positions = {}
        
    def check_position_size(self, amount_usdt: float) -> bool:
        """Verifie si la taille de position est acceptable"""
        if amount_usdt > self.max_position_size:
            logger.warning(f"Position size {amount_usdt} USDT exceeds max {self.max_position_size} USDT")
            return False
        return True
    
    def check_daily_loss(self) -> bool:
        """Verifie si la perte journaliere est acceptable"""
        if self.daily_pnl < -self.max_daily_loss:
            logger.error(f"Daily loss limit reached: {self.daily_pnl} USDT")
            return False
        return True
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calcule le prix de stop loss"""
        if side.upper() == "BUY":
            return entry_price * (1 - self.stop_loss_percent)
        else:
            return entry_price * (1 + self.stop_loss_percent)
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calcule le prix de take profit"""
        if side.upper() == "BUY":
            return entry_price * (1 + self.take_profit_percent)
        else:
            return entry_price * (1 - self.take_profit_percent)
    
    def should_close_position(self, position: Dict, current_price: float) -> Optional[str]:
        """Determine si une position doit etre fermee"""
        entry_price = position.get("entry_price", 0)
        side = position.get("side", "BUY")
        stop_loss = position.get("stop_loss")
        take_profit = position.get("take_profit")
        
        if not stop_loss or not take_profit:
            return None
        
        # Check stop loss
        if side.upper() == "BUY" and current_price <= stop_loss:
            return "STOP_LOSS"
        elif side.upper() == "SELL" and current_price >= stop_loss:
            return "STOP_LOSS"
        
        # Check take profit
        if side.upper() == "BUY" and current_price >= take_profit:
            return "TAKE_PROFIT"
        elif side.upper() == "SELL" and current_price <= take_profit:
            return "TAKE_PROFIT"
        
        return None
    
    def validate_trade(self, symbol: str, side: str, amount: float, price: float) -> Dict:
        """Valide un trade avant execution"""
        result = {
            "valid": True,
            "reasons": [],
            "stop_loss": None,
            "take_profit": None
        }
        
        amount_usdt = amount * price
        
        # Check position size
        if not self.check_position_size(amount_usdt):
            result["valid"] = False
            result["reasons"].append("Position size too large")
        
        # Check daily loss
        if not self.check_daily_loss():
            result["valid"] = False
            result["reasons"].append("Daily loss limit reached")
        
        # Calculate risk levels
        if result["valid"]:
            result["stop_loss"] = self.calculate_stop_loss(price, side)
            result["take_profit"] = self.calculate_take_profit(price, side)
        
        return result
    
    def update_daily_pnl(self, pnl: float):
        """Met a jour le PnL journalier"""
        self.daily_pnl += pnl
        logger.info(f"Daily PnL updated: {self.daily_pnl:.2f} USDT")

# Test du module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rm = RiskManager()
    
    # Test validation trade
    trade = rm.validate_trade("BTC/USDT", "BUY", 0.01, 45000)
    print(f"Trade validation: {trade}")
    
    # Test should close
    position = {
        "entry_price": 45000,
        "side": "BUY",
        "stop_loss": 44100,
        "take_profit": 46350
    }
    
    print(f"At 44000: {rm.should_close_position(position, 44000)}")
    print(f"At 46500: {rm.should_close_position(position, 46500)}")
    print(f"At 45500: {rm.should_close_position(position, 45500)}")
