#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Dual Direction Trader
==========================================
Trading bidirectionnel Long/Short simultané
by MAIGA ABOUBACAR
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

LOG = logging.getLogger("dual_direction")
LOG.setLevel(logging.INFO)

@dataclass
class DualPosition:
    coin: str
    long_entry: float
    long_size: float
    short_entry: float
    short_size: float
    long_active: bool = True
    short_active: bool = True

class DualDirectionTrader:
    """Trading Long + Short simultané pour profiter des deux directions"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {"tp_percent": 2.0, "sl_percent": 1.5}
        self.positions: Dict[str, DualPosition] = {}
        LOG.info("✅ Dual Direction Trader initialized")
    
    def open_dual_position(self, coin: str, price: float, size: float) -> DualPosition:
        """Ouvre position Long + Short"""
        position = DualPosition(
            coin=coin,
            long_entry=price,
            long_size=size,
            short_entry=price,
            short_size=size
        )
        self.positions[coin] = position
        LOG.info(f"✅ Dual position opened: {coin} @ ${price:.2f}")
        return position
    
    def update_position(self, coin: str, current_price: float) -> Dict:
        """Met à jour et check TP/SL"""
        if coin not in self.positions:
            return {"action": "none"}
        
        pos = self.positions[coin]
        actions = []
        
        # Check Long TP/SL
        if pos.long_active:
            long_pnl_pct = ((current_price - pos.long_entry) / pos.long_entry) * 100
            if long_pnl_pct >= self.config["tp_percent"]:
                actions.append({"side": "long", "action": "close", "reason": "tp", "pnl": long_pnl_pct})
                pos.long_active = False
            elif long_pnl_pct <= -self.config["sl_percent"]:
                actions.append({"side": "long", "action": "close", "reason": "sl", "pnl": long_pnl_pct})
                pos.long_active = False
        
        # Check Short TP/SL
        if pos.short_active:
            short_pnl_pct = ((pos.short_entry - current_price) / pos.short_entry) * 100
            if short_pnl_pct >= self.config["tp_percent"]:
                actions.append({"side": "short", "action": "close", "reason": "tp", "pnl": short_pnl_pct})
                pos.short_active = False
            elif short_pnl_pct <= -self.config["sl_percent"]:
                actions.append({"side": "short", "action": "close", "reason": "sl", "pnl": short_pnl_pct})
                pos.short_active = False
        
        # Close position si les deux fermées
        if not pos.long_active and not pos.short_active:
            del self.positions[coin]
        
        return {"actions": actions}

_dual_trader = None
def get_dual_trader():
    global _dual_trader
    if _dual_trader is None:
        _dual_trader = DualDirectionTrader()
    return _dual_trader
